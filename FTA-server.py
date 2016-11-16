# FTA-server.py

import RTP
import sys

port = ''
port = int(sys.argv[1])

global socket
socket = RTP.RTP()

IP = socket.get_IP

def initial(IPnum, portnum):
	IP = IPnum
	port = portnum
	# Not using IP to bind yet
	socket.RTP_Bind(('', port))
	# socket.RTP_listen(1)
	print ("Finished Initializing...")
initial(IP, port)

def send_file(filename):

	# Need to tell server we are going to send file to server
	socket.RTP_Send(bytearray(filename, 'utf-8'))

	# load file
	fileBytes = open(command.split(' ')[i], 'rb').read()

	# Send file to server
	socket.RTP_Send(fileBytes)

	print("File has been sent by server")

def get_file(filename):
	# Need to tell server we are going to send file to server
	socket.RTP_Send(bytearray(filename, 'utf-8'))

	fileBytes = socket.RTP_Recv(1024)

	# Write file; wb = write and binary
	file = open('new' + command.split(' ')[i], 'wb')
	file.write(fileBytes)
	
	# Get file from server
	print("File from server received")


def wait():
    # Get the command from the client
    command = socket.RTP_Recv(1024)

    # Check to see what the command is
    if command is None:
        global con
        con = False      
    elif command.decode('utf-8').split(' ')[0] == 'get':
        send_file(command)
    elif command.decode('utf-8').split(' ')[0] == 'post':
        get_file(command)
    else:
        print('Invalid command received')


def waitForConnect():
	global con
	con = False
	if(con):
		wait()
	else:    
		con, addr = socket.RTP_Recv()

def terminate():
	con.close()
	sys.exit()
	# raise Exception('terminate')

def set_window(newSize):
	# epdate window size
	windowSize = newSize
	socket.setMaxWindowSize(newSize)

	print('New window size set')

def prompt():
	#try:
	print('Enter some command for the FTA Server(terminate; window):')
	command = input()

	# Check for the type of command input by the user
	if command == 'terminate':
		terminate()
	elif command == 'window':
		set_window(int(user_input.split(' ')[1]))
	else:
		print('That was not a valid command')


while True:
	waitForConnect()