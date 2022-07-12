import argparse
import os
import socket
import sys
import time
import traceback

sys.path.append("..")
sys.path.append(".")

from shared import fta_lib, rtp_socket
from shared.fta_lib import CHECK_LEN, CONFIRM, FILE_FOUND, FILE_NOT_FOUND, GET, POST, REJECT, recv_exact


def connect(IP, port, rtpClientSocket, connected):
    if connected:
        print("You are already connected to FTA-Server.")
        return True

    try:
        rtpClientSocket.connect((IP, port))
        print(f"Connection successful to: {IP}:{port}")
        return True
    except ConnectionRefusedError as e:
        print(repr(e))
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
    return recv_exact(rtpClientSocket, CHECK_LEN).decode("ascii")


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
    start_time = time.time()
    fta_lib.recv_file(filename, rtpClientSocket)
    print(f"Successfully downloaded {filename} in {time.time() - start_time} seconds.")


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

    start_time = time.time()
    fta_lib.send_file(filename, rtpClientSocket)
    print(f"Successfully uploaded {filename} in {time.time() - start_time} seconds.")


def handle_command(command, commandInput, rtpClientSocket, real):
    commandArg = None
    if len(commandInput) > 1 and len(commandInput[1]) > 0:
        commandArg = commandInput[1]

    if command == "get":
        if commandArg is None:
            print("get command must be followed by a filename. Please try again.")
        else:
            print(f"Requesting file: {commandArg}")
            request_file(commandArg, rtpClientSocket)
    elif command == "post":
        if commandArg is None:
            print("post command must be followed by a filename. Please try again.")
        else:
            print(f"Sending file: {commandArg}")
            send_file(commandArg, rtpClientSocket)
    elif command == "window":
        if commandArg is None:
            print("window command must be followed by an integer number of segments. Please try again.")
        else:
            try:
                commandArg = int(commandArg)
            except (ValueError, TypeError):
                print("window command must be followed by an integer number of segments. Please try again.")

            try:
                print(f"Setting window: {commandArg} segments")
                fta_lib.set_window(commandArg, rtpClientSocket, real)
            except ValueError as e:
                print(repr(e))


def main(IP, port, debug, real):
    fta_lib.configure_logger(debug)

    # Command loop.
    rtpClientSocket = None
    connected = False
    valid_commands = ["connect", "get", "post", "window", "disconnect", "exit"]
    while True:

        # Create socket
        if rtpClientSocket is None:
            rtpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) if real else rtp_socket.rtp_socket()

        try:
            commandInput = input(
                """
Enter a command on FTA client -
[connect, get, post, window, disconnect, exit]: """
            )
            commandInput = commandInput.split(" ")
            command = commandInput[0].lower()

            if command not in valid_commands:
                print("That was not valid. Please enter a valid command.")
            elif command == "connect":
                connected = connect(IP, port, rtpClientSocket, connected)
            elif command == "disconnect":
                connected = disconnect(rtpClientSocket, connected, printError=True)
            elif command == "exit":
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
            print("--------------------------------------")
            print(str(sys.exc_info()[1]))
            traceback.print_exc()
            print("--------------------------------------")
            break

        # Must be re-created on disconnect because RTP doesn't support reusing closed sockets.
        rtpClientSocket = None if not connected else rtpClientSocket


if __name__ == "__main__":

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

    print(art)
    parser = argparse.ArgumentParser(prog="FTA-client", description="Runs a file transfer client.")
    parser.add_argument("ip", action="store", nargs="?", type=str, help="the IP address of the server")
    parser.add_argument("port", action="store", nargs="?", type=int, help="the port of the server")
    parser.add_argument("-d", "--debug", action="store_true", help="prints debug outputs")
    parser.add_argument("-r", "--real", action="store_true", help="use real TCP instead of RTP")
    args = parser.parse_args()
    args.port = args.port if args.port else 8080
    args.ip = args.ip if args.ip else "127.0.0.1"
    main(args.ip, args.port, args.debug, args.real)
    print("\n\nThank you for using FTA-Client!")
    print("- Sid Senthilkumar & Ashika Ganesh")
