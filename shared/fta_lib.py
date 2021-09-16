import os

GET            = "GET "
POST           = "POST"
FILE_NOT_FOUND = "N_FOUND"
FILE_FOUND     = "Y_FOUND"
CONFIRM        = "CONFIRM"
REJECT         = "REJECT "
CHECK_LEN      = len(CONFIRM)
COMMAND_LEN    = len(GET)

def yn_prompt(message):
    response = "initial_value"
    while response != 'y' and response != 'n':
        response = input(f"{message} [y, n] ").lower()
    return response == 'y'

def set_window(newSize, rtpSocket, real):
    if not real:
        rtpSocket.set_window_size(newSize)
        print(f"New window size set to: {newSize}")
    else:
        print("Cannot set max window size on real socket")

def send_int(rtpSocket, number):
    rtpSocket.sendall(number.to_bytes(8, byteorder='little'))

def recv_int(rtpSocket):
    data = rtpSocket.recv(8)
    return int.from_bytes(data, byteorder='little')

def send_file(filename, rtpSocket):
    filesize = os.path.getsize(filename)
    send_int(rtpSocket, filesize)
    for data in chunks_from_file(filename):
        rtpSocket.sendall(data)

def recv_file(filename, rtpSocket):
    filesize = recv_int(rtpSocket)
    with open(filename, 'wb') as fout:
        i = 0
        while i < filesize:
            rcvData = rtpSocket.recv(1024)
            i += len(rcvData)
            fout.write(rcvData)

def chunks_from_file(filename, chunksize=1024):
    with open(filename, "rb") as fin:
        while True:
            chunk = fin.read(chunksize)
            if not chunk:
                break
            yield chunk
