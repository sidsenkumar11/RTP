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


def connect(): 
	print("Got to connect.")
	try:
		rtpClientSocket.connect((IP,port))
	except:
		print ("Could not connect to server...quitting now")
		sys.exit()

	print("Connection Successful to: " + IP)


def send_file(filename):

	# # Need to tell server we are going to send file to server
	# socket.RTP_Send(bytearray(filename, 'utf-8'))

	# # load file
	# fileBytes = open(command.split(' ')[i], 'rb').read()

	# # Send file to server
	# socket.RTP_Send(fileBytes)
	rtpClientSocket.sendall("thisisatest")
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

	print ("get_file got data: " + data)

# def set_window(newSize):
# 	# epdate window size
# 	windowSize = newSize
# 	socket.setMaxWindowSize(newSize)

# 	print('New window size set')


def disconnect():
	# Disconnect from the server
	rtpClientSocket.close()

	# Print a confirmation to the user
	print('Disconnected...')


connect()
send_file("temp")
get_file("temp")
disconnect()
# while True:
# 	user_input = input('Enter a command on FTA client:')

# 	command = user_input.split(' ')[0]
# 	if command == 'connect':
# 		connect()
# 	elif command == 'get':
# 		get_file(user_input)
# 	elif command == 'post':
# 		send_file(user_input)
# 	elif command == 'window':
# 		set_window(int(user_input.split(' ')[1]))
# 	elif command == 'disconnect':
# 		disconnect()
# 	elif command == 'exit':
# 		print ("Disconnecting....")
# 		sys.exit()
# 	else:
# 		print('That was not valid. Please enter a valid command')