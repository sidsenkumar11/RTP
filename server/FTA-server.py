from shared.fta_lib import GET, POST, REJECT, FILE_FOUND, FILE_NOT_FOUND
from shared.fta_lib import CHECK_LEN, COMMAND_LEN
import shared.rtp_socket as rtp_socket
import shared.fta_lib as fta_lib
import argparse
import os
import sys
import threading

def exec_commands(con, addr, connections, run_event):
    try:
        # stop listening for commands on ctrl+c
        while run_event.is_set():
            # get command and length of filename
            command = con.recv(COMMAND_LEN).decode('ascii')
            filename_len = fta_lib.recv_int(con)
            filename = con.recv(filename_len).decode('ascii')

            # file server command
            if command == GET:
                send_file(filename, con)
            elif command == POST:
                recv_file(filename, con)
            else:
                print("Disconnected.")
                break
    except TimeoutError:
        print("Timed out.")
    finally:
        con.close()
        del(connections[addr])
        print("Connection closed.")

def recv_file(filename, con):
    if os.path.exists(filename):
        con.sendall(bytes(FILE_FOUND, 'ascii'))
        check = con.recvall(CHECK_LEN).decode('ascii')
        if check == REJECT:
            print("Client cancelled file upload.")
            return
    else:
        con.sendall(bytes(FILE_NOT_FOUND, 'ascii'))

    fta_lib.recv_file(filename, con)
    print("File uploaded to server.")

def send_file(filename, con):
    if not os.path.exists(filename):
        print("File does not exist on server.")
        con.sendall(bytes(FILE_NOT_FOUND, "ascii"))
        return
    con.sendall(bytes(FILE_FOUND, "ascii"))
    fta_lib.send_file(filename, con)
    print(f"{filename} has been sent to client.")

def main(port, debug, real):
    fta_lib.configure_logger(debug)

    # Bind and listen to socket.
    if real:
        import socket
        rtpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        rtpServerSocket = rtp_socket.rtp_socket(IPv6=False, debug=debug)
    rtpServerSocket.bind(('', port))
    rtpServerSocket.listen(1)
    print(f"Listening on 0.0.0.0:{port}")

    # State information for multi-threaded server.
    run_event = threading.Event()
    run_event.set()
    connections = {}

    # Wait for connections.
    while True:
        try:
            print("Waiting for new connection...")
            con, addr = rtpServerSocket.accept()
            print(f"Accepted a new connection from {addr}.")
            t = threading.Thread(target=exec_commands, args=(con, addr, connections, run_event), daemon=True)
            connections[addr] = t
            t.start()
        except KeyboardInterrupt:
            run_event.clear()
            for t in connections.values():
                t.join(.1) # timeout if connection takes too long to finish
            break
        except:
            print("Something went wrong with client interaction.")
            print('--------------------------------------')
            print(str(sys.exc_info()[1]))
            print('--------------------------------------')
            break

    rtpServerSocket.close()

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
    print(art)

    parser = argparse.ArgumentParser(
        prog="FTA-server",
        description="Runs a file transfer server.")
    parser.add_argument('port',
        action='store',
        nargs='?',
        type=int,
        help='the port to run the server on')
    parser.add_argument('-d', '--debug',
        action='store_true',
        help='prints debug outputs')
    parser.add_argument('-r', '--real',
        action='store_true',
        help='use real TCP instead of RTP')
    args = parser.parse_args()
    args.port = args.port if args.port else 8080
    main(args.port, args.debug, args.real)
    print("\n\nThank you for using FTA-Server!")
    print("- Sid Senthilkumar & Ashika Ganesh")
