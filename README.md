Nicholas Molica (nicmolica), February 2021

# FTP Client Implementation
This is a manual implementation of a File Transport Protocol client. It supports the `ls`, `mkdir`, `rm`, `rmdir`, `cp` and `mv` commands. It is written from scratch, but is designed to fit the spec required by an FTP server. Even though this client fits the FTP spec, it is not recommended to attempt to run this code on a public-facing FTP server, since the client is unverified. It is possible that the sever could be convinced that this client is malicious, potentially causing the server to blacklist you.

## Technology Used
This client is entirely implemented in Python. It utilizes the `sys` and `socket` modules, as well as several other general purpose modules. It is written in an object-oriented format to make it easily extensible. I developed this client independently.

## Development Process
My primary goal throughout development was to make this software easy to use. In order to accomplish this, I made it so that a user could create a `ControlSocket` object with the origin path and destionation path, then connect, login, and execute the command provided by the user. Including the creation of the `ControlSocket`, this is 5 lines of code to execute an FTP operation. In order to test this client against an actual server, I used an FTP server provided by a professor at Northeastern (Prof. Jackson Alden). Please note that all code is contained in the `3700ftp.py` file.
