import logging
import os

GET = "GET "
POST = "POST"
FILE_NOT_FOUND = "N_FOUND"
FILE_FOUND = "Y_FOUND"
CONFIRM = "CONFIRM"
REJECT = "REJECT "
CHECK_LEN = len(CONFIRM)
COMMAND_LEN = len(GET)
CHUNK_SIZE = pow(2, 22)  # 4MB


def configure_logger(debug):
    logging.basicConfig(
        format="[%(asctime)s][%(levelname)s][%(name)s]: %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=logging.INFO if debug else logging.WARN,
    )


def yn_prompt(message):
    response = "initial_value"
    while response != "y" and response != "n":
        response = input(f"{message} [y, n] ").lower()
    return response == "y"


def set_window(newSize, rtpSocket, real):
    if not real:
        rtpSocket.set_window(newSize)
        print(f"New window size set to {newSize} segment(s)")
    else:
        print("Cannot set max window size on real socket")


def recv_exact(rtpSocket, num_bytes):
    data = bytes()
    while len(data) < num_bytes:
        data += rtpSocket.recv(num_bytes)
    return data


def send_int(rtpSocket, number):
    rtpSocket.sendall(number.to_bytes(8, byteorder="little"))


def recv_int(rtpSocket):
    data = recv_exact(rtpSocket, 8)
    return int.from_bytes(data, byteorder="little")


def send_file(filename, rtpSocket):
    filesize = os.path.getsize(filename)
    send_int(rtpSocket, filesize)
    for data in chunks_from_file(filename):
        rtpSocket.sendall(data)


def recv_file(filename, rtpSocket):
    filesize = recv_int(rtpSocket)
    with open(filename, "wb") as fout:
        i = 0
        while i < filesize:
            rcvData = rtpSocket.recv(CHUNK_SIZE)
            i += len(rcvData)
            fout.write(rcvData)


def chunks_from_file(filename, chunksize=CHUNK_SIZE):
    with open(filename, "rb") as fin:
        while True:
            chunk = fin.read(chunksize)
            if not chunk:
                break
            yield chunk
