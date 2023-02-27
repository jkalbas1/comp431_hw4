#Joseph Kalbas 730414620
#All code in this file has been written solely by myself, Joseph Kalbas

import sys
import socket

hostname = sys.argv[1]
port = int(sys.argv[2])

seen = ""
special = ["<", ">", "(", ")", "[", "]", "\\", ".", ",", ";", ":", "\"", "@"]
space = [" ", "\t"]

def local_part(line):
    global seen
    if seen != "":
        copy_line = line.split(seen)[1]
    else:
        copy_line = line
    count = 0
    for sp in copy_line:
        if sp in special or sp in space:
            if count == 0:
                print("ERROR -- string")
                return False
            return True
        else:
            count+=1
            seen += sp
    return True

def whitespace(line):
    global seen
    if seen != "":
        line = line.split(seen)[1]
    if(line == ""):
        return True
    if(line[0] != " " and line[0] != "\t"):
        return False
    for sp in line:
        if sp == " " or sp == "\t":
            seen += sp
        else:
            return True

def domain(line):
    global seen
    line = line.split(seen)[1]
    count = 0
    run_count = 0
    for sp in line:
        if count == 0 and not sp.isalpha():
            print("ERROR -- element")
            return False
        if sp == ".":
            seen += sp
            count = 0
            run_count += 1
            continue
        if sp.isalpha() or sp.isdigit():
            count += 1
            run_count += 1
            seen += sp
        else:
            print("ERROR -- element")
            return False
    if line[run_count-1] == ".":
        print("ERROR -- element")
        return False
    return True

def path(line):
    global seen
    seen = ""
    if seen != "":
        copy_line = line.split(seen)[1]
    else:
        copy_line = line
    whitespace(copy_line)
    if not local_part(line):
        return False
    copy_line = line.split(seen)[1]
    if(copy_line == "" or copy_line[0] != "@"):
        print("ERROR -- mailbox")
        return False
    
    seen += "@"

    if not domain(line):
        return False
    return True

graceful_exit = False

def wait_250(line):
    global graceful_exit
    if line[0:3] == "250":
        graceful_exit = True
        return True
    else:
        return False

def wait_354(line):
    global graceful_exit
    if line[0:3] == "354":
        graceful_exit = True
        return True
    else:
        return False

def quit_prg():
    global clientSock
    send_msg = "QUIT\n"
    clientSock.send(send_msg.encode())
    try:
        recv_msg = clientSock.recv(1024).decode()
    except socket.error as e:
        print("Read failure")
        clientSock.close()
        exit(1)
    clientSock.close()
    exit(1)


state = ""

sys.stdout.write("From:\n")
from_addr = sys.stdin.readline().strip()
while not path(from_addr):
    sys.stdout.write("From:\n")
    from_addr = sys.stdin.readline().strip()

sys.stdout.write("To:\n")
to_addrs = sys.stdin.readline().strip().replace(" ", "").split(',')
for addr in to_addrs:
    if not path(addr):
        sys.stdout.write("To:\n")
        to_addrs = sys.stdin.readline().strip().replace(" ", "").split(',')

sys.stdout.write("Subject:\n")
subject = sys.stdin.readline()

sys.stdout.write("Message:\n")
msg = ""
line = ""
while line != ".\n":
    line = sys.stdin.readline()
    msg += line

clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    clientSock.connect((hostname, port))
except socket.error as e:
    print("Socket connect failure.")
    clientSock.close()
    exit(1)
send_msg = ""

try:
    recv_msg = clientSock.recv(1024).decode()
except socket.error as e:
    print("Read failure")
    clientSock.close()
    exit(1)

if recv_msg[0:3] == "220":
    send_msg = "HELO " + ('').join(socket.gethostname().split(".")[1:]) + "\n"
    try:
        clientSock.send(send_msg.encode())
    except socket.error as e:
        print("Send error")
        clientSock.close()
        exit(1)
else:
    quit_prg()
try:
    recv_msg = clientSock.recv(1024).decode()
except socket.error as e:
    print("Read failure")
    clientSock.close()
    exit(1)

send_msg = "MAIL FROM: <" + from_addr + ">\n"

for addr in to_addrs:
    send_msg += "RCPT TO: <" + addr + ">\n"

send_msg += "DATA\n"

send_msg += "From: <" + from_addr + ">\nTo: "
for recpt in to_addrs:
    temp_msg = "<" + recpt + ">, "
    send_msg += temp_msg

send_msg = send_msg[:-2]
send_msg += "\nSubject: " + subject + "\n" + msg

try:
    clientSock.send(send_msg.encode())
except socket.error as e:
    print("Send error")
    clientSock.close()
    exit(1)


try:
    recv_msg = clientSock.recv(1024).decode()
except socket.error as e:
    print("Read failure")
    clientSock.close()
    exit(1)

for i, line in enumerate(recv_msg.splitlines()):
    if i == len(to_addrs) + 1:
        #DATA recognition is expected
        if not wait_354:
            quit_prg()
    else:
        if not wait_250:
            quit_prg()



send_msg = "QUIT\n"
try:
    clientSock.send(send_msg.encode())
except socket.error as e:
    print("Send error")
    clientSock.close()
    exit(1)

#221 command
try:
    recv_msg = clientSock.recv(1024).decode()
except socket.error as e:
    print("Read failure")
    clientSock.close()
    exit(1)
clientSock.close()
