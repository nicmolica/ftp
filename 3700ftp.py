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
    def __init__(self, url):
        self.user = 'anonymous' # default user is anonymous
        self.password = ''      # default password is no password
        self.port = 21          # default port is 21
        self.is_ftp = False     # default is_ftp flag is false (indicates whether this address is ftp or just a path)
        self.host = None
        self.path = ''
        try:
            self.parse_url(url)
        except:
            print("Invalid address syntax: " + url)
            exit(1)

    def parse_url(self, url):
        parsed = urllib.parse.urlparse(url)
        # determine if scheme of URL is valid
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
        return self.user == 'anonymous' and self.password == '' and \
            self.port == 21 and self.is_ftp == False and self.host == None \
                and self.path == ''

# Class to represent user input into the program. Contains fields to represent the requested operation
# and the 2 paths provided by the user. For single-path operations, the second path is empty.
class UserInput:
    def __init__(self, args):
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
        # fail if user didn't provide an FTP address
        if addr1.is_ftp == addr2.is_ftp and (not addr1.is_empty() or not addr2.is_empty()):
            print("One address must be a server address.")
            exit(1)
        elif addr1.is_ftp:
            self.ftp = addr1
        else:
            self.ftp = addr2
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.sock.connect((self.ftp.host, self.ftp.port))
        except:
            print("Failed to connect to the server.")
            exit(1)
    
    def login(self):
        # wait for 220 code before logging in, complain if something else is recieved
        if self.read()[:3] == "220":
            pass
        else:
            print("Client did not receive 220 code.")
            exit(1)

        # log into server with username and password
        self.sock.sendall(("USER " + str(self.ftp.user) + "\r\n").encode())
        self.read()
        self.sock.sendall(("PASS " + str(self.ftp.password) + "\r\n").encode())
        self.read()

        # set server modes to prep for sending/receiving data
        self.sock.sendall(("TYPE I\r\n").encode())
        self.read()
        self.sock.sendall(("MODE S\r\n").encode())
        self.read()
        self.sock.sendall(("STRU F\r\n").encode())
        self.read()

    def read(self):
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
        self.sock.sendall(("QUIT\r\n").encode())
        self.read()

    def execute(self, user_input):
        if user_input.cmd == Operation.ls:
            pass
        elif user_input.cmd == Operation.mkdir:
            self.mkdir(user_input.ftp.path)
        elif user_input.cmd == Operation.rm:
            pass
        elif user_input.cmd == Operation.rmdir:
            self.rmdir(user_input.ftp.path)
        elif user_input.cmd == Operation.cp:
            pass
        elif user_input.cmd == Operation.mv:
            pass

    def ls(self):
        pass

    def mkdir(self, path):
        self.sock.sendall(("MKD " + path + "\r\n").encode())
        self.read()

    def rm(self):
        pass

    def rmdir(self, path):
        self.sock.sendall(("RMD " + path + "\r\n").encode())
        self.read()

    def cp(self):
        pass

    def mv(self):
        pass

# Main method that handles high-level program logic.
def main():
    # get user input
    user_input = UserInput(sys.argv)
    
    # initialize socket, connect and log into server
    ctrl = ControlSocket(user_input.path1, user_input.path2)
    ctrl.connect()
    ctrl.login()

    # execute user command
    ctrl.execute(user_input)

    # terminate control socket
    ctrl.quit()

# Begin program execution in main method.
if __name__ == "__main__":
    main()