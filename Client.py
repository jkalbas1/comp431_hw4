#Joseph Kalbas 730414620
#All code in this file has been written solely by myself, Joseph Kalbas

import sys

file_path = sys.argv[1]

read_file = open(file_path, 'r')
graceful_exit = False

def wait_250():
    global graceful_exit
    for line in sys.stdin:
        sys.stderr.write(line)
        if line[0:3] == "250":
            graceful_exit = True
            return True
        else:
            return False

def wait_354():
    global graceful_exit
    for line in sys.stdin:
        sys.stderr.write(line)
        if line[0:3] == "354":
            graceful_exit = True
            return True
        else:
            return False

def quit_prg():
    sys.stdout.write("Quit\n")
    exit(1)


state = ""
for line in read_file.readlines():
    graceful_exit = False

    if line[0:5] == "From:":
        if state == "data": # last line was the end of a data cmd
            sys.stdout.write(".\n")
            if not wait_250():
                quit_prg()
        sys.stdout.write("MAIL FROM:" + line[5:])
        state = "mail"
    elif line[0:3] == "To:":
        if state == "data": # last line was the end of a data cmd
            sys.stdout.write(".\n")
            if not wait_250(): 
                quit_prg()
        sys.stdout.write("RCPT TO:" + line[3:])
        state = "rcpt"
    elif state == "rcpt":
        if state == "data": # last line was the end of a data cmd
            sys.stdout.write(".\n")
            if not wait_250():
                quit_prg()
        sys.stdout.write("DATA\n")
        if not wait_354():
            quit_prg()
        state = "data"

    if state == "data":
        sys.stdout.write(line)
        continue

    if not wait_250():
        quit_prg()

    if EOFError and not graceful_exit:
        quit_prg()

if state == "data":
    sys.stdout.write("\n.\n")
    wait_250()
sys.stdout.write("QUIT\n")