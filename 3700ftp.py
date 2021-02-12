import os
import sys
import socket
import urllib.parse
import enum

# Enumeration of the operations available to the user.
class Operation(enum.Enum):
    ls = "ls"
    mkdir = "mkdir"
    rm = "rm"
    rmdir = "rmdir"
    cp = "cp"
    mv = "mv"

# Class to represent an address, which is an argument passed to any of the Operations
# available to the user. Can be either an FTP address or a local path.
class Address:
    def __init__(self, addr):
        ''' Creates an address given an FTP address (or simple path). Sets the default
        field values and then parses the provided address/path for any fields that the
        user wanted to specify (such as username, password, port, etc).
        '''
        self.user = 'anonymous' # default user is anonymous
        self.password = ''      # default password is no password
        self.port = 21          # default port is 21
        self.is_ftp = False     # default is_ftp flag is false (indicates whether this address is ftp or just a path)
        self.host = None
        self.path = ''
        try:
            self.parse_url(addr)
        except:
            print("Invalid address syntax: " + addr)
            exit(1)

    def parse_url(self, url):
        ''' Use the urllib module to parse a provided URL and pull out components so that
        they're in an accessible format for the control socket.
        '''
        parsed = urllib.parse.urlparse(url)
        # determine if scheme of URL is valid (either ftp or blank for a path)
        if parsed.scheme == 'ftp':
            self.is_ftp = True
        elif parsed.scheme == '' and parsed.hostname == None:
            self.is_ftp = False
        else:
            raise TypeError("Invalid path scheme. Must be an FTP or local path.")

        # pull out pieces of netloc, defaulting to presets
        self.host = parsed.hostname
        self.path = parsed.path
        if parsed.username != None:
            self.user = parsed.username
        if parsed.password != None:
            self.password = parsed.password
        if parsed.port != None:
            self.port = parsed.port
    
    def is_empty(self):
        ''' Helper method to determine if the address is empty. Helps other methods
        determine when an address should be ignored since the default for single-arg
        operations is to still pass 2 args but have one of them be empty.
        '''
        return self.user == 'anonymous' and self.password == '' and \
            self.port == 21 and self.is_ftp == False and self.host == None \
                and self.path == ''

# Class to represent user input into the program. Contains fields to represent the requested operation
# and the 2 paths provided by the user. For single-path operations, the second path is empty.
class UserInput:
    def __init__(self, args):
        ''' Parses user input and puts it into various fields to be parsed and more easily
        recognized. Handles the difference between single-arg and dual-arg operations and
        determines which provided address is an FTP address and which is a simple path.
        '''
        if len(args) == 3 and (args[1] == Operation.ls.name or args[1] == Operation.mkdir.name or \
            args[1] == Operation.rm.name or args[1] == Operation.rmdir.name):
            self.cmd = Operation(args[1])
            self.path1 = Address(args[2])
            self.path2 = Address('')
        elif len(args) == 4 and (args[1] == Operation.cp.name or args[1] == Operation.mv.name):
            self.cmd = Operation(args[1])
            self.path1 = Address(args[2])
            self.path2 = Address(args[3])
        else:
            print("Operation must be one of: ls, mkdir, rm, rmdir, cp, mv and include 1 or 2 arguments.")
            exit(1)
        
        if self.path1.is_ftp:
            self.ftp = self.path1
        elif self.path2.is_ftp:
            self.ftp = self.path2
        else:
            print("One address must be a server address.")

# Class to represent the control socket used to talk to the server.
class ControlSocket:
    def __init__(self, addr1, addr2):
        ''' Initializes the socket and determines which address is an FTP address in 
        order to determine where to source username, password, port, etc.
        '''
        # fail if user didn't provide an FTP address
        if addr1.is_ftp == addr2.is_ftp and (not addr1.is_empty() or not addr2.is_empty()):
            print("One address must be a server address.")
            exit(1)
        elif addr1.is_ftp:
            self.ftp = addr1
        else:
            self.ftp = addr2
        
        # attempt to create the socket
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            print("Failed to create socket.")
            exit(1)

    def connect(self):
        ''' Attempt to connect to the socket, complain if it's not possible.
        '''
        try:
            self.sock.connect((self.ftp.host, self.ftp.port))
        except:
            print("Command socket failed to connect to the server.")
            exit(1)
    
    def login(self):
        ''' Handles logging into the server and setting appropriate connection modes
        to prep for sending and receiving data. Catches cases where a password is not
        required or when a provided password is incorrect.
        '''
        # wait for 220 code before logging in, complain if something else is recieved
        if self.read()[:3] == "220":
            pass
        else:
            print("Client did not receive 220 code.")
            exit(1)

        # log into server with username and password
        self.send("USER " + str(self.ftp.user) + "\r\n")
        code = self.read()[:3]
        if code == '331' and self.ftp.password == '':
            print("Password required by server and none provided.")
            exit(1)
        elif code == '230':
            pass
        else:
            self.send("PASS " + str(self.ftp.password) + "\r\n")
            if self.read()[:3] == '530':
                print("Invalid password.")
                exit(1)

        # set server modes to prep for sending/receiving data
        self.send("TYPE I\r\n")
        self.read()
        self.send("MODE S\r\n")
        self.read()
        self.send("STRU F\r\n")
        self.read()

    def read(self):
        ''' Read data from socket until end flag is recieved. If an error message is recieved,
        print it and error out.
        '''
        # read data using recv until the end flag \r\n is found
        msg = ""
        while msg == "" or msg[len(msg) - 2:] != "\r\n":
            packet = self.sock.recv(8192)
            msg = msg + packet.decode('utf-8')

        # display server error if the code is 4xx or higher
        if int(msg[0]) > 3:
            print("Server error: " + msg)
            exit(1)
        return msg

    def quit(self):
        ''' Send quit message and close the socket.
        '''
        self.send("QUIT\r\n")
        self.read()
        self.sock.close()

    def execute(self, user_input):
        ''' Determine which operation to call based on user input and pass correct args.
        '''
        if user_input.cmd == Operation.ls:
            self.ls(user_input.ftp.path)
        elif user_input.cmd == Operation.mkdir:
            self.mkdir(user_input.ftp.path)
        elif user_input.cmd == Operation.rm:
            self.rm(user_input.ftp)
        elif user_input.cmd == Operation.rmdir:
            self.rmdir(user_input.ftp.path)
        elif user_input.cmd == Operation.cp:
            self.cp(user_input.path1, user_input.path2)
        elif user_input.cmd == Operation.mv:
            self.mv(user_input.path1, user_input.path2)

    def init_data_socket(self):
        ''' Send PASV message to server and recieve IP and port for the data socket. Print an error
        message and fail out if there's a problem.
        '''
        self.send("PASV\r\n")
        pasv_response = self.read()
        if pasv_response[:3] != '227':
            print("Server refused data transfer with message: " + pasv_response)
            exit(1)
        
        try:
            nums = pasv_response.split("(")[1].split(")")[0].split(",")
            ip = nums[0] + "." + nums[1] + "." + nums[2] + "." + nums[3]
            port = int(nums[4]) * 256 + int(nums[5])
        except:
            print("Server did not provide valid IP/port for data stream.")
            exit(1)

        data_stream = DataSocket(ip, port)
        data_stream.connect()
        return data_stream
    
    def send(self, msg):
        ''' Send a message to the server.
        '''
        self.sock.sendall(msg.encode())
    
    def ls(self, path):
        ''' List files in a directory on the server.
        '''
        data_stream = self.init_data_socket()
        self.send("LIST " + path + "\r\n")
        print(data_stream.read())
        self.read()
        data_stream.quit()

    def mkdir(self, path):
        ''' Make a directory on the server.
        '''
        self.send("MKD " + path + "\r\n")
        self.read()

    def rm(self, addr):
        ''' Delete a file from the server. If the file is local, remove it using the os module.
        Note that this method cannot be called on a local path by the user, which is enforced
        in the constructor for UserInput. The local path removal functionality exists to be
        used by the mv function.
        '''
        if addr.is_ftp:
            self.send("DELE " + addr.path + "\r\n")
            self.read()
        else:
            os.remove(addr.path)

    def rmdir(self, path):
        ''' Remove a directory from the server.
        '''
        self.send("RMD " + path + "\r\n")
        self.read()

    def cp(self, src, dest):
        ''' Copy a file from a source to a destination. Works going to or from a server.
        '''
        data_stream = self.init_data_socket()
        if src.is_ftp:
            self.send("RETR " + src.path + "\r\n")
            f = open(dest.path, 'w')
            f.write(data_stream.read())
        else:
            self.send("STOR " + dest.path + "\r\n")
            f = open(src.path, 'r')
            data_stream.send(f.read())
        f.close()
        self.read()
        data_stream.quit()

    def mv(self, src, dest):
        ''' Move a file from one place to another. Works going to or from a server.
        '''
        self.cp(src, dest)
        self.rm(src)

# Class to represent the data socket used to move data to and from the server.
class DataSocket:
    def __init__(self, ip, port):
        ''' Create the socket, complain if it doesn't work.
        '''
        self.ip = ip
        self.port = port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            print("Failed to create socket.")
            exit(1)
    
    def connect(self):
        ''' Connect to the socket, complain if it doesn't work.
        '''
        try:
            self.sock.connect((self.ip, self.port))
        except:
            print("Data socket failed to connect to the server.")
            exit(1)

    def read(self):
        ''' Read data from the server. Continue reading until we recieve empty messages.
        '''
        msg = ""
        packet = None
        while msg == "" or packet.decode('utf-8') == '':
            packet = self.sock.recv(8192)
            msg = msg + packet.decode('utf-8')
        return msg

    def send(self, msg):
        ''' Send data to the server.
        '''
        self.sock.sendall(msg.encode())
    
    def quit(self):
        ''' Close the socket.
        '''
        self.sock.close()

def main():
    ''' Main method to control high-level program functionality. Get user input, initialize the control socket,
    connect and log into the server, execute the requested command, then close the control socket and quit.
    '''
    user_input = UserInput(sys.argv)
    ctrl = ControlSocket(user_input.path1, user_input.path2)
    ctrl.connect()
    ctrl.login()
    ctrl.execute(user_input)
    ctrl.quit()

# Begin program execution in main method.
if __name__ == "__main__":
    main()