import sys
# sys.path.insert(0, '/home/azmuth/Documents/RTP/RTP Socket Code')

import rtp_socket
# import socket
import sys
import os

def connect(IP, port): 
    try:
        rtpClientSocket.connect((IP,port))
    except:
        print ("Could not connect to server.")
        return False

    print("Connection Successful to: " + IP + ":" + str(port))
    return True

def receive_file(filename):
    send_generic(rtpClientSocket, bytearray("get " + str(filename),'utf8'))

    filesize = recv_generic(rtpClientSocket, 5)
    intBytes = int.from_bytes(filesize, byteorder='little')
    if (intBytes != 0):
        dataset = bytearray()
        i = 0
        while i < intBytes:
            rcvData = rtpClientSocket.recv(1024)
            t = bytearray(rcvData)
            dataset.extend(t)
            i = i + len(rcvData)
            
        write_file(filename, dataset)
    else:
        print("Sorry, this file does not appear to exist.")

def write_file(filename, dataset):

    if(os.path.exists(filename)):
        check = input('This file already exists, do you want to overwrite it? [y,n]: ')
        if (check == 'y'):
            print("Okay. Going to overwrite the file.")
            with open(filename, 'wb') as out:
                out.write(dataset)
            print("Successfully downloaded " + str(filename) + " from server.")
        elif(check == 'n'):
            print("Okay. Will not overwrite the file.")
        else:
            print("Invalid input. Did not overwrite the file.")
        return

    with open(filename, 'wb') as out:
        out.write(dataset)
    print("Successfully downloaded " + str(filename) + " from server.")

def send_file(filename):
    if(os.path.exists(filename)):
        # Need to tell server we are going to send file to server
        send_generic(rtpClientSocket, bytearray("post " + str(filename),'utf8'))
        with open(filename, 'rb') as f:
            fileBytes = f.read()

        # Sending Length of file in bytes to server
        send_generic(rtpClientSocket, len(fileBytes).to_bytes(5, byteorder='little'))
        check = recv_generic(rtpClientSocket, 12, decode_data=True)

        # File exists on server.
        if(check == 'FILEEXISTS'):
            while check != 'y' and check != 'n':
                check = input('This file already exists on the server; do you want to overwrite it? [y,n]: ')
        else:
            check = 'y'

        send_generic(rtpClientSocket, bytes(check, 'utf8'))

        if (check == 'y'):
            # Send chunks of 1024 bytes to server
            for b in chunks_from_file(filename):
                if(b != -1):
                    rtpClientSocket.sendall(b)

            print(filename + " has been sent to server.")
        elif(check == 'n'):
            print('Okay. Will not send this file.')
        else:
            send_generic(rtpClientSocket, b'n')
            print('Invalid Input. Did not send file.')
    else:
        print("Sorry, this file does not appear to exist.")

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
    rtpClientSocket.set_window_size(newSize)

    print('New window size set to: ' + str(newSize))

def disconnect():
    # Disconnect from the server
    send_generic(rtpClientSocket, bytearray("disconnect", 'utf8'))
    rtpClientSocket.close()

    print('Disconnected...')

def recv_generic(con, recv_size, decode_data=False):
    # A byte value of 4 will be the end of message character.
    data = bytearray()
    while 4 not in data:
        data += con.recv(recv_size)
    return data[:data.index(4)] if not decode_data else data[:data.index(4)].decode('utf8')

def send_generic(con, data):
    # Append a byte value of 4 to signal end of data.
    data += bytearray([4])
    con.sendall(data)

if __name__ == '__main__':

    art = '''

88888888888  888888888888    db                   ,ad8888ba,   88  88                                   
88                88        d88b                 d8"'    `"8b  88  ""                            ,d     
88                88       d8'`8b               d8'            88                                88     
88aaaaa           88      d8'  `8b              88             88  88   ,adPPYba,  8b,dPPYba,  MM88MMM  
88"""""           88     d8YaaaaY8b   aaaaaaaa  88             88  88  a8P_____88  88P'   `"8a   88     
88                88    d8""""""""8b  """"""""  Y8,            88  88  8PP"""""""  88       88   88     
88                88   d8'        `8b            Y8a.    .a8P  88  88  "8b,   ,aa  88       88   88,    
88                88  d8'          `8b            `"Y8888Y"'   88  88   `"Ybbd8"'  88       88   "Y888  
                                                                                                       '''

    # Parse IP and Port arguments.
    debug = False
    if (len(sys.argv) > 2):
        try:
            IP = sys.argv[1]
            port = int(sys.argv[2])
        except:
            print("Usage: python3 FTA-client.py <IP> <port>")
            print("-d flag sets DEBUG mode on")
            sys.exit()
    else:
        print("Port and IP not given together. Auto set to 8080 and 128.61.12.27")
        port = 8080
        IP = "127.0.1.1"
        debug = True

    for arg in sys.argv:
        if arg == '-d':
            debug = True

    # Create socket.
    rtpClientSocket = rtp_socket.rtp_socket(IPv6=False, debug=debug)
    # rtpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    isConnected = False
    finished = False

    print(art)

    while not finished:
        commandInput = input('Enter a command on FTA client - \n[connect, get, post, window, disconnect, exit]: ')
        commandInput = commandInput.split(' ')
        command = commandInput[0]
        commandArg = None

        if len(commandInput) > 1:
            commandArg = commandInput[1]

        if command == 'connect':
            if not isConnected:
                isConnected = connect(IP, port)
            else:
                print("You are already connected to FTA-Server.")
        elif command == 'get' and isConnected:
            if commandArg == None:
                print("get command must be followed by a filename. Please try again.")
            else:
                print("Requesting file: " + str(commandArg))
                receive_file(commandArg)
        elif command == 'post' and isConnected:
            if commandArg == None:
                print("post command must be followed by a filename. Please try again.")
            else:
                print("Sending file: " + str(commandArg))
                send_file(commandArg)
        elif command == 'window' and isConnected:
            if commandArg == None:
                print("window command must be followed by an integer. Please try again.")
            else:
                try:
                    commandArg = int(commandArg)
                except:
                    print("window command must be followed by an integer. Please try again.")
                    commandArg = None

                if commandArg != None:
                    print("Setting window: " + str(commandArg))
                    set_window(commandArg)
        elif command == 'disconnect' and isConnected:
            isConnected = False
            disconnect()
        elif command == 'exit':
            if isConnected:
                disconnect()
            print ("Exiting...")
            finished = True
        elif not isConnected:
            print ("Currently not connected. Please connect.")
        else:
            print('That was not valid. Please enter a valid command.')

    print("\n\nThank you for using FTA-Client!")
    print("- Sid Senthilkumar & Ashika Ganesh")