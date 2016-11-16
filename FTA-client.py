import RTP
import sys

IP = sys.argv[1]
UPDport = int(sys.argv[2])

def connect(): 
	global socket
	socket = RTP.Connection()
	socket.connect((IP, UPDport))
    socket.listen()
	print("Connection Successful")

def get_file(filename):
	# Need to send file to server
	socket.RTP_Send(bytearray(filename, 'utf-8'))

	fileBytes = socket.RTP_Recv(value??)

	# Write file; wb = write and binary
	file = open('new' + command.split(' ')[i], 'wb')
	file.write(fileBytes)
	# Get file from server

	print("File from server received")

def send_file(filename):
	# Need to send file to server
	socket.RTP_Send(bytearray(filename, 'utf-8'))

	# load file
	fileBytes = open(command.split(' ')[i], 'rb').read()

	# Send file to server
	socket.RTP_Send(fileBytes)

	print("File has been sent")

def set_window(newSize):
    # epdate window size
    windowSize = newSize
    socket.setMaxWindowSize(newSize)

    print('New window size set')


def disconnect():
    # Disconnect from the server
    socket.close()

    # Print a confirmation to the user
    print('Disconnected....')



while True:
    user_input = input('Enter a command on FTA client:')

    command = user_input.split(' ')[0]
    if command == 'connect':
        connect()
    elif command == 'get':
        get_file(user_input)
    elif command == 'post':
        send_file(user_input)
    elif command == 'window':
        set_window(int(user_input.split(' ')[1]))
    elif command == 'disconnect':
        disconnect()
    elif command == 'exit':
    	print ("Disconnecting....")
        sys.exit()
    else:
        print('That was not valid. Please enter a valid command')