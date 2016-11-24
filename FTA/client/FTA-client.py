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

    # Send request.
    rtpClientSocket.sendall(bytearray("get " + str(filename), 'utf8'))

    didPass = rtpClientSocket.recv(10)
    if(str(didPass) == str(b'pass')):
        filesize = rtpClientSocket.recv(5)
        intBytes = int.from_bytes(filesize, byteorder='little')
        
        dataset = bytearray()

        i = 0
        while i < intBytes:
            rcvData = rtpClientSocket.recv(1024)
            t = bytearray(rcvData)
            dataset.extend(t)
            i = i + len(rcvData)

        write_file(filename, dataset)
        if(debug): print("Successfully downloaded " + str(filename) + " from server.")
    else:
        if(debug): print("No such file found on server.")

def write_file(filename, dataset):

    if(os.path.exists(filename)):
        check = input('This file already exists, do you want to overwrite it? [y,n]: ')
        if (check == 'y'):
            if(debug): print("Okay. Going to overwrite the file.")
            with open(filename, 'wb') as out:
                out.write(dataset)
        elif(check == 'n'):
            if(debug): print("Okay. Will not overwrite the file.")
        else:
            if(debug): print("Invalid input. Did not overwrite the file.")
        return

    with open(filename, 'wb') as out:
        out.write(dataset)

def chunks_from_file(filename, chunksize = 1024):
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                yield chunk
            else:
                yield -1
                break

def send_file(filename):
    if(os.path.exists(filename)):
        # Need to tell server we are going to send file to server
        rtpClientSocket.sendall(bytearray("post " + str(filename),'utf8'))
        with open(filename, 'rb') as f:
            fileBytes = f.read()

        # Sending Length of file in bytes to server
        rtpClientSocket.sendall(len(fileBytes).to_bytes(5, byteorder='little'))
        check = rtpClientSocket.recv(12)

        # File exists on server.
        if(str(check) == str(b'FILEEXISTS')):
            while check != 'y' and check != 'n':
                check = input('This file already exists on the server; do you want to overwrite it? [y,n]: ')
        else:
            check = 'y'

        rtpClientSocket.sendall(bytes(check, 'utf8'))

        if (check == 'y'):
            # Send chunks of 1024 bytes to server
            for b in chunks_from_file(filename):
                if(b != -1):
                    rtpClientSocket.sendall(b)

            if(debug): print(filename + " has been sent to server.")
        elif(check == 'n'):
            if(debug): print('Okay. Will not send this file.')
        else:
            rtpClientSocket.sendall(b'n')
            if(debug): print('Invalid Input. Did not send file.')
    else:
        if(debug): print("Sorry, this file does not appear to exist.")

def set_window(newSize):
    # epdate window size
    windowSize = newSize
    # socket.setMaxWindowSize(newSize)

    if(debug): print('New window size set to: ' + str(newSize))


def disconnect():
    # Disconnect from the server
    rtpClientSocket.sendall(bytearray("disconnect", 'utf8'))
    rtpClientSocket.close()

    if(debug): print('Disconnected...')

def exit():
    
    if isConnected:
        disconnect()
    if(debug): print ("Exiting...")

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
            isConnected = connect(IP, port)
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
            exit()
            finished = True
        elif not isConnected:
            print ("Currently not connected. Please connect.")
        else:
            print('That was not valid. Please enter a valid command.')

    print("\n\nThank you for using FTA-Client!")
    print("- Sid Senthilkumar & Ashika Ganesh")