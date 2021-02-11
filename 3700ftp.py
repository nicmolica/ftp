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
        self.user = 'anonymous'
        self.password = ''
        self.host = ''
        self.port = 21
        self.path = ''
        self.is_ftp = False
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
        elif parsed.scheme == '':
            self.is_ftp = False
        else:
            raise TypeError("Invalid path scheme. Must be an FTP or local path.")

        # pull out pieces of netloc, defaulting to presets
        self.host = parsed.hostname
        self.path = parsed.path
        if parsed.username != '':
            self.user = parsed.username
        if parsed.password != '':
            self.password = parsed.password
        if parsed.port != None:
            self.port = parsed.port

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

# Class to represent the control socket used to talk to the server.
class ControlSocket:
    def __init__(self, addr1, addr2):
        if addr1.is_ftp == addr2.is_ftp:
            print("One address must be local and the other must be on a server.")
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

def main():
    cmd = UserInput(sys.argv)
    ctrl = ControlSocket(cmd.path1, cmd.path2)
    ctrl.connect()

if __name__ == "__main__":
    main()