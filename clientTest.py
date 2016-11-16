# FTA-client.py

# import RTP
import sys
import socket

def connect(IP, port): 
	print("About to connect...")
	try:
		rtpClientSocket.connect((IP,port))
	except:
		print ("Could not connect to server...quitting now")
		sys.exit()

	print("Connection Successful to: " + IP + ":" + str(port))

def bytes_from_file(filename, chunksize = 1024):
	with open(filename, "rb") as f:
		while True:
			chunk = f.read(chunksize)
			if chunk:
				for b in chunk:
					yield b
			else:
				break

def send_file(filename):

	# # Need to tell server we are going to send file to server
	# socket.RTP_Send(bytearray(filename, 'utf-8'))
	rtpClientSocket.sendall(bytearray(filename, 'utf8'))
	# # load file
	
	fileBytes = open(filename, 'rb').read()

	# # Send file to server
	# socket.RTP_Send(fileBytes)
	# print(str(fileBytes))
	print(len(fileBytes))
	rtpClientSocket.sendall((len(fileBytes)).to_bytes(10, byteorder='big'))
	# rtpClientSocket.sendall(fileBytes)
	# rtpClientSocket.sendall(b"thisisatest")
	for b in bytes_from_file(filename):
		rtpClientSocket.sendall(b.to_bytes(1024, byteorder='big'))
	print(filename + " has been sent")

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


while True:
	commandInput = input('Enter a command on FTA client - \n[connect, get, post, window, disconnect, exit]: ')

	command = commandInput.split(' ')[0]
	if command == 'connect':
		connect(IP, port)
		isConnected = True
	elif command == 'get' and isConnected:
		fileG = input('Enter the file name you want to get: ')
		get_file(fileG)
	elif command == 'post' and isConnected:
		fileP = input('Enter the file name you want to post: ')
		send_file(fileP)
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