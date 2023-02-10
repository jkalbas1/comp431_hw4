#Joseph Kalbas 730414620
#All code in this file has been written solely by myself, Joseph Kalbas

import sys
import socket
import base64

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
    for sp in line:
        if sp in special or sp in space:
            if count == 0:
                print("ERROR -- string")
                return False
            return True
        else:
            count+=1
            seen += sp
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
            break
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
    recv_msg = clientSock.recv(1024).decode()
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
    msg += line
    line = sys.stdin.readline()

clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSock.connect((hostname, port))
send_msg = ""

recv_msg = clientSock.recv(1024).decode()
if recv_msg[0:3] == "220":
    send_msg = "HELO " + ('').join(socket.gethostname().split(".")[1:]) + "\n"
    clientSock.send(send_msg.encode())
else:
    quit_prg()
recv_msg = clientSock.recv(1024).decode()

send_msg = "MAIL FROM: <" + from_addr + ">\n"
clientSock.send(send_msg.encode())

recv_msg = clientSock.recv(1024).decode()
if not wait_250(recv_msg):
    quit_prg()

for addr in to_addrs:
    send_msg = "RCPT TO: <" + addr + ">\n"
    clientSock.send(send_msg.encode())
    recv_msg = clientSock.recv(1024).decode()
    if not wait_250(recv_msg):
        quit_prg()

send_msg = "DATA\n"
clientSock.send(send_msg.encode())

recv_msg = clientSock.recv(1024).decode()
if not wait_354(recv_msg):
    quit_prg()

send_msg = "From: <" + from_addr + ">\nTo: "
for recpt in to_addrs:
    temp_msg = "<" + recpt + ">, "
    send_msg += temp_msg

send_msg = send_msg[:-2]
send_msg += "\nSubject: " + subject + "MIME-Version: 1.0\nContent-Type: multipart/mixed; boundary=999888999\n\n--999888999\n" 
send_msg += "Content-Transfer-Encoding: quoted-printable\nContent-Type: text/plain\n\n" + msg
send_msg += "--999888999\nContent-Transfer-Encoding: base64\nContent-Type: image/jpeg\n\n"
with open("IMG_1813.JPG", "rb") as img:
    encoded_img = base64.b64encode(img.read())

send_msg += str(encoded_img.decode('ascii')) + "\n--999888999--\n."
clientSock.send(send_msg.encode())
recv_msg = clientSock.recv(1024)
if not wait_250:
    quit_prg()
send_msg = "QUIT\n"
clientSock.send(send_msg.encode())

recv_msg = clientSock.recv(1024).decode()
clientSock.close()
