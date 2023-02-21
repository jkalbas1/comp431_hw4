#Joseph Kalbas 730414620
#All code in this file has been written solely by myself, Joseph Kalbas

from sys import stdin
import os
import socket
from sys import argv

forward_path = argv[0].split("Server.py")
if len(forward_path) > 0:
    forward_path = forward_path[0]
else:
    forward_path = ""

receivers = []
seen = ""
special = ["<", ">", "(", ")", "[", "]", "\\", ".", ",", ";", ":", "\"", "@"]
space = [" ", "\t"]
rc_loc = ""
rc_dom = ""
sender = ""
connSock = ""

def mail_token(line):
    if(line[0:4] == "MAIL"):
        global seen
        seen += line[0:4]
        return True
    return False

def whitespace(line):
    global seen
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

def from_token(line):
    global seen
    line = line.split(seen)[1]
    if line[0:5] != "FROM:":
        return False
    seen += line[0:5]
    return True

def nullspace(line):
    global seen
    whitespace(line)
    return True

def local_part(line):
    global seen
    global connSock
    global rc_loc
    rc_loc = ""
    line = line.split(seen)[1]
    count = 0
    for sp in line:
        if sp in special or sp in space:
            if count == 0:
                send_msg = "501 Syntax error in parameters or arguments"
                connSock.send(send_msg.encode())
                return False
            return True
        else:
            count+=1
            seen += sp
            rc_loc += sp
    return True

def domain(line):
    global seen
    global connSock
    global rc_dom
    rc_dom = ""
    line = line.split(seen)[1]
    count = 0
    run_count = 0
    for sp in line:
        if count == 0 and not sp.isalpha():
            send_msg = "501 Syntax error in parameters or arguments"
            connSock.send(send_msg.encode())
            return False
        elif sp == ".":
            seen += sp
            rc_dom += sp
            count = 0
            run_count += 1
            continue
        elif sp.isalpha() or sp.isdigit():
            count += 1
            run_count += 1
            rc_dom += sp
            seen += sp
        elif sp == ">":
            seen += sp
            return True
        else:
            send_msg = "501 Syntax error in parameters or arguments"
            connSock.send(send_msg.encode())
            return False
    if line[run_count-1] == ".":
        send_msg = "501 Syntax error in parameters or arguments"
        connSock.send(send_msg.encode())
        return False
    return True

def path(line):
    global connSock
    global seen
    copy_line = line.split(seen)[1]
    if(copy_line[0] != "<"):
        send_msg = "501 Syntax error in parameters or arguments"
        connSock.send(send_msg.encode())
        return False
    seen += "<"
    if not local_part(line):
        return False
    copy_line = line.split(seen)[1]
    
    if(len(copy_line) == 0):
        send_msg = "501 Syntax error in parameters or arguments"
        connSock.send(send_msg.encode())
        return False
    if(copy_line[0] != "@"):
        send_msg = "501 Syntax error in parameters or arguments"
        connSock.send(send_msg.encode())
        return False
    
    seen += "@"

    if not domain(line):
        return False

    copy_line = line.split(seen)[1]
    if seen[-1] != ">":
        send_msg = "501 Syntax error in parameters or arguments"
        connSock.send(send_msg.encode())
        return False
    return True

def crlf(line):
    global seen
    global connSock
    copy_line = line.split(seen)[1]
    if(len(copy_line) == 0):
        send_msg = "501 Syntax error in parameters or arguments"
        connSock.send(send_msg.encode())
        return False
    if copy_line[0] != "\n":
        send_msg = "501 Syntax error in parameters or arguments"
        connSock.send(send_msg.encode())
        return False
    return True

def mail_from(line):
    global seen
    global sender
    global connSock
    seen = ""

    if not mail_token(line):
        send_msg = "500 Syntax error: command unrecognized"
        connSock.send(send_msg.encode())
        return False

    if not whitespace(line):
        send_msg = "500 Syntax error: command unrecognized"
        connSock.send(send_msg.encode())
        return False

    if not from_token(line):
        send_msg = "500 Syntax error: command unrecognized"
        connSock.send(send_msg.encode())
        return False

    nullspace(line)

    if not path(line):
        return False
    
    nullspace(line)

    if not crlf(line):
        return False
    
    sender = "<" + rc_loc + "@" + rc_dom + ">"
    return True

def to_token(line):
    global seen
    line = line.split(seen)[1]
    if line[0:3] == "TO:":
        seen += "TO:"
        return True
    return False

def rcpt(line):
    global seen
    global receivers
    global connSock
    seen = "RCPT"

    if not whitespace(line):
        send_msg = "500 Syntax error: command unrecognized"
        connSock.send(send_msg.encode())
        return False
    
    if not to_token(line):
        send_msg = "500 Syntax error: command unrecognized"
        connSock.send(send_msg.encode())
        return False
    
    nullspace(line)

    if not path(line):
        return False
    
    nullspace(line)

    if not crlf(line):
        return False

    if rc_dom not in receivers:
        receivers.append(rc_dom)
    return True
    
def data(line):
    global seen
    global connSock
    seen = "DATA"
    nullspace(line)
    if not crlf(line):
        send_msg = "500 Syntax error: command unrecognized"
        connSock.send(send_msg.encode())
        return False

    return True

def check_valid_cmd(line):
    global seen
    seen = ""
    if(len(line) < 4):
        return False

    if line[0:4] == "MAIL":
        seen = "MAIL"
        if not whitespace(line):
            return False
        if not from_token(line):
            return False

    elif line[0:4] == "RCPT":
        seen = "RCPT"
        if not whitespace(line):
            return False
        if not to_token(line):
            return False
    
    elif line[0:4] != "DATA":
        return False
    return True

#Hold a string representation of previous previous message
state = ""
data_seen = ""
per = True

#implement these below
sender = ""

serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
hostname = socket.gethostname()
port = int(argv[1])
try:
    serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
except socket.error as e:
    print("Socket sockopt failure.")
    serverSock.close()
    exit(1)
try:
    serverSock.bind(('', port))
except socket.error as e:
    print("Socket bind failure.")
    serverSock.close()
    exit(1)

serverSock.listen(21)
clientHost = ""

while(True):
    state = "" #keep track of state machine
    receivers = []
    data_seen = ""

    try: #accept connection
        connSock, addr = serverSock.accept()
    except socket.error as e:
        print("Socket accept error")
        serverSock.close()
        continue

    #send 220 hostname msg
    send_msg = "220 " + hostname
    try:
        connSock.send(send_msg.encode())
    except socket.error as e:
        print("Send error")
        connSock.close()
        continue

    try:
        recv_msg = connSock.recv(1024).decode()
    except socket.error as e:
        print("Read failure")
        connSock.close()
        continue

    #check if msg received is HELO msg
    if recv_msg[0:5] == "HELO ":
        clientHost = recv_msg[5:-1]
        send_msg = "250 Hello " + clientHost + " pleased to meet you"
        try:
            connSock.send(send_msg.encode())
        except socket.error as e:
            print("Send error")
            connSock.close()
            continue
    else:
        send_msg = "221 " + hostname + " closing connection"
        try:
            connSock.send(send_msg.encode())
            continue
        except socket.error as e:
            print("Send error")
            connSock.close()
            continue

    while recv_msg[0:4] != "QUIT":
        try:
            recv_msg = connSock.recv(1024).decode()
        except socket.error as e:
            print("Read failure")
            break
        
        #connection is broken
        if not recv_msg:
            break

        if(recv_msg[0:4] == "QUIT"):
            break

        #check for valid command
        if not check_valid_cmd(recv_msg) and state != "DATA":
            send_msg = "500 Syntax error: command unrecognized"
            try:
                connSock.send(send_msg.encode())
            except socket.error as e:
                print("Send error")
                break
            state = ""
            receivers = []
            data_seen = ""
            continue
        
        seen = ""

        if(recv_msg[0:4] == "MAIL") and state != "DATA": #MAIL cmd
            if state != "":
                send_msg = "503 Bad sequence of commands"
                try:
                    connSock.send(send_msg.encode())
                except socket.error as e:
                    print("Send error")
                    break
                state = ""
                receivers = []
                data_seen = ""
                continue
            if mail_from(recv_msg) and state == "": #valid mail to msg
                send_msg = "250 OK"
                try:
                    connSock.send(send_msg.encode())
                except socket.error as e:
                    print("Send error")
                    break
                state = "mail"
            elif state != "":
                send_msg = "503 Bad sequence of commands"
                try:
                    connSock.send(send_msg.encode())
                except socket.error as e:
                    print("Send error")
                    break
                state = ""
                receivers = []
                data_seen = ""
            else:
                state = ""
                receivers = []
                data_seen = ""
        elif(recv_msg[0:4] == "RCPT") and state != "DATA": #RCPT TO cmd
            if state != "mail" and state != "rcpt":
                send_msg = "503 Bad sequence of commands"
                try:
                    connSock.send(send_msg.encode())
                except socket.error as e:
                    print("Send error")
                    break
                state = ""
                receivers = []
                data_seen = ""
                continue
            if rcpt(recv_msg):
                if state == "mail" or state == "rcpt":
                    send_msg = "250 OK"
                    try:
                        connSock.send(send_msg.encode())
                    except socket.error as e:
                        print("Send error")
                        break
                    state = "rcpt"
                else:
                    send_msg = "503 Bad sequence of commands"
                    try:
                        connSock.send(send_msg.encode())
                    except socket.error as e:
                        print("Send error")
                        break
                    state = ""
                    receivers = []
                    data_seen = ""
            else:
                state = ""
                receivers = []
                data_seen = ""
        elif(recv_msg [0:4] == "DATA") and state != "DATA": #DATA cmd
            if state != "rcpt":
                send_msg = "503 Bad sequence of commands"
                try:
                    connSock.send(send_msg.encode())
                except socket.error as e:
                    print("Send error")
                    break
                state = ""
                receivers = []
                data_seen = ""
                continue
            if data(recv_msg):
                if state == "rcpt":
                    send_msg = "354 Start mail input; end with <CRLF>.<CRLF>\n"
                    try:
                        connSock.send(send_msg.encode())
                    except socket.error as e:
                        print("Send error")
                        break
                    state = "DATA"
                    per = False
                else:
                    send_msg = "503 Bad sequence of commands"
                    try:
                        connSock.send(send_msg.encode())
                    except socket.error as e:
                        print("Send error")
                        connSock.close()
                        break
                    state = ""
                    receivers = []
                    data_seen = ""
            else:
                state = ""
                receivers = []
                data_seen = ""
        else:
            if state == "DATA":
                if recv_msg.split("\n")[-2] == "." or recv_msg.split("\n")[-1] == ".":
                    per = True
                    send_msg = "250 OK"
                    try:
                        connSock.send(send_msg.encode())
                    except socket.error as e:
                        print("Send error")
                        connSock.close()
                        break
                    data_seen += ("\n").join(recv_msg.split("\n")[:-2])
                    for add in receivers:
                        file = open(forward_path + "forward/" + add, "a+")
                        file.write(data_seen)
                        file.close()

                    state = ""
                    data_seen = ""
                    receivers = []
                else:
                    data_seen += recv_msg
            else:
                send_msg = "500 Syntax error: command unrecognized"
                try:
                    connSock.send(send_msg.encode())
                except socket.error as e:
                    print("Send error")
                    connSock.close()
                    break
                state = ""
                data_seen = ""
                receivers = []
    
    if recv_msg[0:4] != "QUIT":
        connSock.close()
        continue

    send_msg = "221 " + hostname + " closing connection"
    try:
        connSock.send(send_msg.encode())
    except socket.error as e:
        print("Send error")
        connSock.close()
        continue
    connSock.close()