# import rtp_socket
import socket
import sys
import threading
import os

def initialize(IPnum, portnum):
    rtpServerSocket.bind((IPnum, portnum))
    rtpServerSocket.listen(1)
    if(debug): print ("Socket binded to " + str(IPnum) + ":" + str(portnum))

def prompt():
    finished = False
    while not finished:
        commandInput = input('Enter some command for the FTA Server - [window, terminate]: ')
        commandInput = commandInput.split(' ')
        command = commandInput[0]
        commandArg = None

        if len(commandInput) > 1:
            commandArg = commandInput[1]

        if command == 'terminate':
            rtpServerSocket.close()
            finished = True
        elif command == 'window':
            window_size = None
            try:
                window_size = int(commandArg)
            except:
                print("window command must be followed by an integer. Please try again.")

            if window_size != None:
                print("Attempting to change window to: " + str(commandArg))
                set_window(commandArg)
        else:
            print('That was not valid. Please enter a valid command.')

def client_interact():
    while True:
        try:
            con, addr = rtpServerSocket.accept()
            print("Accepted a new connection.")
            finished = False
            while not finished:
                finished = receive_command(con)
        except:
            if(debug): print("Something went wrong in client_interact. " + str(sys.exc_info()[1]) +  "\nRestarting...")
        finally:
            con.close()
            print("Completed connection. Waiting for new one...")

def receive_command(con):
    command = con.recv(100)
    command = command.decode('utf-8')
    filename = ''

    if command != "disconnect":
        command = command.split(' ')
        filename = command[1]
        command = command[0]

    if (str(command) == "get"):
        send_file(filename, con)
        return False
    elif (command == "post"):
        filesize = con.recv(5)
        intBytes = int.from_bytes(filesize, byteorder='little')
        if(os.path.exists(filename)):
            con.sendall(b'FILEEXISTS')
        else:
            con.sendall(b'NO')

        check = con.recv(1)
        if (str(check) == str(b'y')):
            dataset = bytearray()
            i = 0
            while i < intBytes:
                rcvData = con.recv(1024)
                t = bytearray(rcvData)
                dataset.extend(t)
                i = i + len(rcvData)
                
            write_file(filename, dataset)
            if(debug): print("File uploaded to server.")
            return False
        elif(str(check) == str(b'n')):
            if(debug): print("File not uploaded to server.")
            return False
    elif (command == "disconnect"):
        return True

def send_file(filename, con):

    if(os.path.exists(filename)):
        con.sendall(bytearray("pass",'utf8'))
        if(debug): print("File has been found on server.")

        with open(filename, 'rb') as f:
            fileBytes = f.read()

        con.sendall((len(fileBytes)).to_bytes(5, byteorder='little'))
        for b in chunks_from_file(filename):
            if b != -1:
                con.sendall(b)

        if(debug): print(filename + " has been sent to client.")
    else:
        con.sendall(bytearray("didNotpass",'utf8'))
        if(debug): print("File was not found on the server.")
        # closeConnection()
        # initialize(IP, port)
        # receive_file()

def write_file(filename, dataset):

    with open(filename, 'wb') as out:
        out.write(dataset)
        if(debug): print("File written on server successfully.")


def chunks_from_file(filename, chunksize = 1024):
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                yield chunk
            else:
                yield -1
                break

def set_window(newSize):
    # epdate window size
    pass
    # socket.setMaxWindowSize(newSize)

    if(debug): print('New window size set to: ' + str(newSize))

if __name__ == '__main__':

    art = '''
                                                                                                                            
    88888888888  888888888888    db                ad88888ba                                                                
    88                88        d88b              d8"     "8b                                                               
    88                88       d8'`8b             Y8,                                                                       
    88aaaaa           88      d8'  `8b            `Y8aaaaa,     ,adPPYba,  8b,dPPYba,  8b       d8   ,adPPYba,  8b,dPPYba,  
    88"""""           88     d8YaaaaY8b   aaaaaaaa  `"""""8b,  a8P_____88  88P'   "Y8  `8b     d8'  a8P_____88  88P'   "Y8  
    88                88    d8""""""""8b  """"""""        `8b  8PP"""""""  88           `8b   d8'   8PP"""""""  88          
    88                88   d8'        `8b         Y8a     a8P  "8b,   ,aa  88            `8b,d8'    "8b,   ,aa  88          
    88                88  d8'          `8b         "Y88888P"    `"Ybbd8"'  88              "8"       `"Ybbd8"'  88          
                                                                                                                            
                                                                                                                            '''

    # Parse arguments.
    debug = False
    if (len(sys.argv) > 1):
        try:
            port = int(sys.argv[1])
            print("Port is: " + str(port))
        except:
            print("Usage: python3 FTA-server.py <port> <-d>")
            print("-d flag sets DEBUG mode on")
            sys.exit()
    else:
        print("Port is not given. Auto set to 8080.")
        port = 8080
        debug = True

    for arg in sys.argv:
        if arg == '-d':
            debug = True


    # Create and bind socket.
    print(art)
    rtpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # rtpServerSocket = rtp_socket(IPv6=False, debug=debug)
    # IP = rtp_socket.get_IP()
    initialize('', port)

    # Forever check command input by the user and run server until terminate command entered.
    server_thread = threading.Thread(target=client_interact)
    command_thread = threading.Thread(target=prompt)

    server_thread.daemon = True
    command_thread.daemon = True

    command_thread.start()
    server_thread.start()

    command_thread.join()
    print("\n\nThank you for using FTA-Server!")
    print("- Sid Senthilkumar & Ashika Ganesh")