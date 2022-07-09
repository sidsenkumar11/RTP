from shared.fta_lib import CHECK_LEN, GET, POST, CONFIRM, REJECT, FILE_FOUND, FILE_NOT_FOUND
from shared import rtp_socket
from shared import fta_lib
import sys
import os

def connect(IP, port, rtpClientSocket, connected):
    if connected:
        print("You are already connected to FTA-Server.")
        return True

    try:
        rtpClientSocket.connect((IP,port))
        print(f"Connection successful to: {IP}:{port}")
        return True
    except ConnectionRefusedError as e:
        print(repr(e))
        return False
    except:
        print("Could not connect to server.")
        return False

def disconnect(rtpClientSocket, connected, printError=False):
    if not connected:
        if printError:
            print("Not connected to FTP-Server. Please connect first.")
        return False

    print("Disconnecting...")
    rtpClientSocket.close()
    print("Disconnected.")
    return False

def send_cmd(cmd, filename, rtpClientSocket):
    rtpClientSocket.sendall(bytes(cmd, "ascii"))
    fta_lib.send_int(rtpClientSocket, len(filename))
    rtpClientSocket.sendall(bytes(filename, "ascii"))
    return rtpClientSocket.recv(CHECK_LEN).decode("ascii")

def request_file(filename, rtpClientSocket):
    # Check if file already exists.
    if os.path.exists(filename):
        if not fta_lib.yn_prompt("This file already exists, do you want to overwrite it?"):
            print("Okay. Will not request the file.")
            return
        print("Okay. Going to overwrite the file.")

    # Tell server we are requesting a file.
    check = send_cmd(GET, filename, rtpClientSocket)
    if check == FILE_NOT_FOUND:
        print("Sorry, this file does not appear to exist on the server.")
        return

    # Download the file.
    fta_lib.recv_file(filename, rtpClientSocket)
    print(f"Successfully downloaded {filename} from server.")

def send_file(filename, rtpClientSocket):
    # Check if file already exists.
    if not os.path.exists(filename):
        print("Sorry, this file does not appear to exist.")
        return

    # Tell server we are sending a file.
    check = send_cmd(POST, filename, rtpClientSocket)
    if check == FILE_FOUND:
        print("This file already exists on the server.")
        if not fta_lib.yn_prompt("Are you sure you want to overwrite it?"):
            print("Ok, post cancelled.")
            rtpClientSocket.sendall(bytes(REJECT, "ascii"))
            return
        rtpClientSocket.sendall(bytes(CONFIRM, "ascii"))
    fta_lib.send_file(filename, rtpClientSocket)

def handle_command(command, commandInput, rtpClientSocket, real):
    commandArg = None
    if len(commandInput) > 1 and len(commandInput[1]) > 0:
        commandArg = commandInput[1]

    if command == 'get':
        if commandArg is None:
            print("get command must be followed by a filename. Please try again.")
        else:
            print(f"Requesting file: {commandArg}")
            request_file(commandArg, rtpClientSocket)
    elif command == 'post':
        if commandArg is None:
            print("post command must be followed by a filename. Please try again.")
        else:
            print(f"Sending file: {commandArg}")
            send_file(commandArg, rtpClientSocket)
    elif command == 'window':
        try:
            commandArg = int(commandArg)
        except (ValueError, TypeError):
            print("window command must be followed by an integer. Please try again.")

        try:
            print(f"Setting window: {commandArg}")
            fta_lib.set_window(commandArg, rtpClientSocket, real)
        except ValueError as e:
            print(repr(e))

def main(IP, port, debug, real):
    # Create socket.
    if real:
        import socket
        rtpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        rtpClientSocket = rtp_socket.rtp_socket(IPv6=False, debug=debug)

    # Command loop.
    connected = False
    valid_commands = ["connect", "get", "post", "window", "disconnect", "exit"]
    while True:
        try:
            commandInput = input("""
Enter a command on FTA client -
[connect, get, post, window, disconnect, exit]: """)
            commandInput = commandInput.split(' ')
            command = commandInput[0].lower()

            if command not in valid_commands:
                print("That was not valid. Please enter a valid command.")
            elif command == 'connect':
                connected = connect(IP, port, rtpClientSocket, connected)
            elif command == 'disconnect':
                connected = disconnect(rtpClientSocket, connected, printError=True)
            elif command == 'exit':
                connected = disconnect(rtpClientSocket, connected)
                break
            elif not connected:
                print("Not connected to FTP-Server. Please connect first.")
            else:
                handle_command(command, commandInput, rtpClientSocket, real)
        except KeyboardInterrupt:
            break
        except BrokenPipeError:
            print("The connection with the server has been reset.")
            connected = disconnect(rtpClientSocket, connected)
            print("Please reconnect.")
        except:
            connected = disconnect(rtpClientSocket, connected)
            print("Something went wrong while talking to the server.")
            print("You have been disconnected.")
            print('--------------------------------------')
            print(str(sys.exc_info()[1]))
            print('--------------------------------------')
            print('Restarting...')


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

    real = False
    for arg in sys.argv:
        if arg == '-d':
            debug = True
            real = True

    print(art)
    main(IP, port, debug, real)
    print("\n\nThank you for using FTA-Client!")
    print("- Sid Senthilkumar & Ashika Ganesh")
