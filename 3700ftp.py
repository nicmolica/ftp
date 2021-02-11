import sys
import socket
import urllib.parse
import enum

class Operation(enum.Enum):
    ls = "ls"
    mkdir = "mkdir"
    rm = "rm"
    rmdir = "rmdir"
    cp = "cp"
    mv = "mv"

class Address:
    def __init__(self, url):
        self.user = 'anonymous'
        self.password = ''
        self.host = ''
        self.port = 21
        self.path = ''
        try:
            self.parse_url(url)
        except:
            print("Invalid path formation: " + url)

    def parse_url(self, url):
        parsed = urllib.parse.urlparse(url, scheme = 'ftp')
        if len(parsed.netloc.split("@")) == 2:
            # case where user, password, host, port are provided
            if len(parsed.netloc.split(":")) == 3:
                self.user = parsed.netloc.split(":")[0]
                self.password = parsed.netloc.split("@")[0].split(":")[1]
                self.host = parsed.netloc.split("@")[1].split(":")[0]
                self.port = int(parsed.netloc.split("@")[1].split(":")[1])
            # case where user, password, host are provided
            elif len(parsed.netloc.split(":")) == 2 and len(parsed.netloc.split("@")[0].split(":")) == 2:
                self.user = parsed.netloc.split(":")[0]
                self.password = parsed.netloc.split("@")[0].split(":")[1]
                self.host = parsed.netloc.split("@")[1]
            # case where user, host, port are provided
            elif len(parsed.netloc.split(":")) == 2 and len(parsed.netloc.split("@")[0].split(":")) == 1:
                self.user = parsed.netloc.split("@")[0]
                self.host = parsed.netloc.split("@")[1].split(":")[0]
                self.port = parsed.netloc.split("@")[1].split(":")[1]
            # case where user, host are provided
            else:
                self.user = parsed.netloc.split("@")[0]
                self.host = parsed.netloc.split("@")[1]
        # case wehre just the host is provided
        else:
            self.host = parsed.netloc.split(":")[0]
            # case where host, port are provided
            if len(parsed.netloc.split(":")) > 1:
                self.port = int(parsed.netloc.split(":")[1])
        self.path = parsed.path

class UserInput:
    def __init__(self, args):
        if len(args) == 3 and (args[1] == Operation.ls.name or args[1] == Operation.mkdir.name or \
            args[1] == Operation.rm.name or args[1] == Operation.rmdir.name):
            self.cmd = Operation(args[1])
            self.path1 = Address(args[2])
            self.path2 = ''
        elif len(args) == 4 and (args[1] == Operation.cp.name or args[1] == Operation.mv.name):
            self.cmd = Operation(args[1])
            self.path1 = Address(args[2])
            self.path2 = Address(args[3])
        else:
            print("Operation must be one of: ls, mkdir, rm, rmdir, cp, mv and include 1 or 2 arguments.")
            exit(1)

class ControlSocket:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
        except:
            print("Failed to connect to the server.")
            exit(1)

def main():
    ui = UserInput(sys.argv)

if __name__ == "__main__":
    main()