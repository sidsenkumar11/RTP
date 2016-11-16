# FTA-client.py

# import RTP
import sys
import socket


if (len(sys.argv) > 2):
	IP = sys.argv[1]
	port = int(sys.argv[2])
	print("IP is: " + IP)
	print("Port is: " + str(port))
else:
	print("Port and IP is not given. Auto set to 8080 and 128.61.12.27")
	port = 8080
	IP = "128.61.12.27"

# global socket
# socket = RTP.RTP()
rtpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
isConnected = False

def connect(): 
	print("About to connect...")
	try:
		rtpClientSocket.connect((IP,port))
	except:
		print ("Could not connect to server...quitting now")
		sys.exit()

	print("Connection Successful to: " + IP + ":" + str(port))


def send_file(filename):

	# # Need to tell server we are going to send file to server
	# socket.RTP_Send(bytearray(filename, 'utf-8'))

	# # load file
	# fileBytes = open(command.split(' ')[i], 'rb').read()

	# # Send file to server
	# socket.RTP_Send(fileBytes)
	rtpClientSocket.sendall(b"thisisatest")
	print("thisisatest has been sent")

def get_file(filename):
	# # Need to tell server we are going to send file to server
	# socket.RTP_Send(bytearray(filename, 'utf-8'))

	# fileBytes = socket.RTP_Recv(1024)

	# # Write file; wb = write and binary
	# file = open('new' + command.split(' ')[i], 'wb')
	# file.write(fileBytes)
	# # Get file from server
	try:
		data = rtpClientSocket.recv(1024)
	except:
		print ("get_file could not recv")
		data = 'N/A'

	print ("get_file got data: " + str(data))

def set_window(newSize):
	# epdate window size
	windowSize = newSize
	# socket.setMaxWindowSize(newSize)

	print('New window size set to: ' + str(newSize))


def disconnect():
	# Disconnect from the server
	rtpClientSocket.close()

	print('Disconnected...')

def exit():
	print ("Exiting...")
	sys.exit()


while True:
	commandInput = input('Enter a command on FTA client - \n[connect, get, post, window, disconnect, exit]: ')

	command = commandInput.split(' ')[0]
	if command == 'connect':
		connect()
		isConnected = True
	elif command == 'get' and isConnected:
		get_file(commandInput)
	elif command == 'post' and isConnected:
		send_file(commandInput)
	elif command == 'window' and isConnected:
		s = input('Enter the new window size:')
		set_window(s)
	elif command == 'disconnect' and isConnected:
		disconnect()
		isConnected = False
	elif command == 'exit':
		exit()
	elif not isConnected:
		print ("Currently not connected. Please connect.")
	else:
		print('That was not valid. Please enter a valid command')