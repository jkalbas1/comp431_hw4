#Joseph Kalbas 730414620
#All code in this file has been written solely by myself, Joseph Kalbas

from sys import stdin
import os
import socket
from sys import argv
 
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
        if sp == ".":
            seen += sp
            rc_dom += sp
            count = 0
            run_count += 1
            continue
        if sp.isalpha() or sp.isdigit():
            count += 1
            run_count += 1
            rc_dom += sp
            seen += sp
        else:
            break
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
    if copy_line[0] != ">":
        send_msg = "501 Syntax error in parameters or arguments"
        connSock.send(send_msg.encode())
        return False
    seen += ">"
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
hostname = socket.gethostname() + ".cs.unc.edu"
port = int(argv[1])
serverSock.bind(('', port))
serverSock.listen(1)
clientHost = ""

while(True):
    connSock, addr = serverSock.accept()

    send_msg = "220 " + hostname

    recv_msg = connSock.recv(1024).decode()

    if recv_msg[0:5] == "HELO ":
        clientHost = recv_msg[5:]
        send_msg = "250 Hello " + clientHost + " pleased to meet you"
        connSock.send(send_msg.encode())
    else:
        send_msg = "221 " + hostname + " closing connection"
        connSock.send(send_msg.encode())

    while recv_msg != "QUIT":
        recv_msg = connSock.recv(1024).decode()
        
        stdin.write()
        if not check_valid_cmd(recv_msg) and state != "DATA":
            send_msg = "500 Syntax error: command unrecognized"
            connSock.send(send_msg.encode())
            state = ""
            receivers = []
            data_seen = ""
            continue
        
        seen = ""

        if(recv_msg[0:4] == "MAIL") and state != "DATA":
            if state != "":
                recv_msg = "503 Bad sequence of commands"
                connSock.send(send_msg.encode())
                state = ""
                receivers = []
                data_seen = ""
                continue
            if mail_from(recv_msg) and state == "":
                recv_msg = "250 OK"
                connSock.send(send_msg.encode())
                state = "mail"
            elif state != "":
                recv_msg = "503 Bad sequence of commands"
                connSock.send(send_msg.encode())
                state = ""
                receivers = []
                data_seen = ""
            else:
                state = ""
                receivers = []
                data_seen = ""
        elif(recv_msg[0:4] == "RCPT") and state != "DATA":
            if state != "mail" and state != "rcpt":
                recv_msg = "503 Bad sequence of commands"
                connSock.send(send_msg.encode())
                state = ""
                receivers = []
                data_seen = ""
                continue
            if rcpt(recv_msg):
                if state == "mail" or state == "rcpt":
                    recv_msg = "250 OK"
                    connSock.send(send_msg.encode())
                    ## add recipient to receivers list
                    state = "rcpt"
                else:
                    recv_msg = "503 Bad sequence of commands"
                    connSock.send(send_msg.encode())
                    state = ""
                    receivers = []
                    data_seen = ""
            else:
                state = ""
                receivers = []
                data_seen = ""
        elif(recv_msg [0:4] == "DATA") and state != "DATA":
            if state != "rcpt":
                recv_msg = "503 Bad sequence of commands"
                connSock.send(send_msg.encode())
                state = ""
                receivers = []
                data_seen = ""
                continue
            if data(recv_msg):
                if state == "rcpt":
                    recv_msg = "354 Start mail input; end with <CRLF>.<CRLF>"
                    connSock.send(send_msg.encode())
                    state = "DATA"
                    per = False
                else:
                    recv_msg = "503 Bad sequence of commands"
                    connSock.send(send_msg.encode())
                    state = ""
                    receivers = []
                    data_seen = ""
            else:
                state = ""
                receivers = []
                data_seen = ""
        else:
            if state == "DATA":
                if recv_msg == ".\n":
                    per = True
                    recv_msg = "250 OK"
                    connSock.send(send_msg.encode())
                    for add in receivers:
                        file = open("forward/" + add, "a+")
                        file.write("From: " + sender + "\n")
                        for rep in receivers:
                            file.write("To: <" + rep + ">\n")
                        file.write(data_seen)
                        file.close()

                    state = ""
                    data_seen = ""
                    receivers = []
                else:
                    data_seen += recv_msg
            else:
                recv_msg = "500 Syntax error: command unrecognized"
                connSock.send(send_msg.encode())
                state = ""
                data_seen = ""
                receivers = []

        if state == "DATA" and not per:
            recv_msg = "501 Syntax error in parameters or arguments"
            connSock.send(send_msg.encode())
    connSock.close()