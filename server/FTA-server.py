import sys
import time
# sys.path.insert(0, '/home/azmuth/Documents/RTP/RTP Socket Code')

import rtp_socket
# import socket
import threading
import os

def initialize(IPnum, portnum):
    rtpServerSocket.bind((IPnum, portnum))
    rtpServerSocket.listen(1)
    print ("Socket binded to " + str(IPnum) + ":" + str(portnum))

def receive_command(con):
    command = recv_generic(con, 100, decode_data=True)
    filename = ''

    if command != "disconnect":
        command = command.split(' ')
        filename = command[1]
        command = command[0]

    if (str(command) == "get"):
        send_file(filename, con)
        return False
    elif (command == "post"):
        filesize = recv_generic(con, 5)
        intBytes = int.from_bytes(filesize, byteorder='little')
        if(os.path.exists(filename)):
            send_generic(con, b'FILEEXISTS')
        else:
            send_generic(con, b'NO')

        check = recv_generic(con, 1, decode_data=True)
        if (check == 'y'):
            dataset = bytearray()
            i = 0
            while i < intBytes:
                rcvData = con.recv(1024)
                t = bytearray(rcvData)
                dataset.extend(t)
                i = i + len(rcvData)
                
            write_file(filename, dataset)
            print("File uploaded to server.")
            return False
        elif(check == 'n'):
            print("File not uploaded to server.")
            return False
    elif (command == "disconnect"):
        print("Will disconnect...")
        return True

def send_file(filename, con):
    if(os.path.exists(filename)):
        with open(filename, 'rb') as f:
            fileBytes = f.read()

        # Sending Length of file in bytes to client
        send_generic(con, len(fileBytes).to_bytes(5, byteorder='little'))

        # Send chunks of 1024 bytes to client
        for b in chunks_from_file(filename):
            if(b != -1):
                try:
                    print(b)
                except:
                    pass
                # time.sleep(.2)
                con.sendall(b)

        print(filename + " has been sent to client.")

    else:
        print("File does not exist on server.")
        send_generic(con, (0).to_bytes(5, byteorder='little'))

def chunks_from_file(filename, chunksize = 1024):
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                yield chunk
            else:
                yield -1
                break
def write_file(filename, dataset):

    with open(filename, 'wb') as out:
        out.write(dataset)
        print("File written on server successfully.")

def set_window(newSize):
    socket.setMaxWindowSize(newSize)

    print('New window size set to: ' + str(newSize))

def send_generic(con, data):
    # Append a byte value of 4 to signal end of data.
    data += bytearray([4])
    con.sendall(data)

def recv_generic(con, recv_size, decode_data=False):
    # A byte value of 4 will be the end of message character.
    data = bytearray()
    while 4 not in data:
        data += con.recv(recv_size)
    return data[:data.index(4)] if not decode_data else data[:data.index(4)].decode('utf8')

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
            should_terminate = True
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
    # rtpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rtpServerSocket = rtp_socket.rtp_socket(IPv6=False, debug=debug)
    # IP = rtp_socket.get_IP()
    initialize('', port)
    should_terminate = False
    connection_open = False

    # Forever check command input by the user and run server until terminate command entered.
    # command_thread = threading.Thread(target=prompt)
    # command_thread.daemon = True
    # command_thread.start()

    while not should_terminate:
        try:
            print("Waiting for new connection...")
            connection_open = False
            con, addr = rtpServerSocket.accept()
            connection_open = True
            print("Accepted a new connection.")
            finished = False
            while not finished:
                finished = receive_command(con)
        except TimeoutError:
            print("Timed out.")
        except:
            if(debug): print("Something went wrong in client_interact. " + str(sys.exc_info()[1]) +  "\nRestarting...")
        finally:
            if connection_open:
                con.close()
            print("Completed connection.")
        should_terminate = input("Terminate? [y, n] ")
        should_terminate = True if should_terminate == "y" else False
        if not should_terminate:
            change_window = input("Change window? [y, n] ")
            if change_window == 'y':
                value = input("New window value: ")
                set_window(value)

    rtpServerSocket.close()
    print("\n\nThank you for using FTA-Server!")
    print("- Sid Senthilkumar & Ashika Ganesh")