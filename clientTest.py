# FTA-client.py

# import RTP
import sys
import socket
import os

def connect(IP, port): 
	print("About to connect...")
	try:
		rtpClientSocket.connect((IP,port))
	except:
		print ("Could not connect to server...quitting now")

	print("Connection Successful to: " + IP + ":" + str(port))

def bytes_from_file(filename, chunksize = 1024):
	with open(filename, "rb") as f:
		while True:
			chunk = f.read(chunksize)
			if chunk:
				for b in chunk:
					yield b
			else:
				yield -1
				break

def send_file(filename):
	if(os.path.exists(filename)):
		# # Need to tell server we are going to send file to server
		# socket.RTP_Send(bytearray(filename, 'utf-8'))
		rtpClientSocket.sendall(bytearray(filename, 'utf8'))
		# # load file
		rtpClientSocket.sendall(bytearray("post",'utf8'))

		fileBytes = open(filename, 'rb').read()

		# # Send file to server
		# socket.RTP_Send(fileBytes)
		# print(str(fileBytes))
		print(len(fileBytes))
		rtpClientSocket.sendall((len(fileBytes)).to_bytes(30, byteorder='little'))
		# rtpClientSocket.sendall(fileBytes)
		# rtpClientSocket.sendall(b"thisisatest")
		for b in bytes_from_file(filename):
			if(b != -1):
				rtpClientSocket.sendall(b.to_bytes(1024, byteorder='little'))
			else:
				rtpClientSocket.sendall(b"FAIL")	
		print(filename + " has been sent")
	else:
		print("Sorry, client can't find that file.")

def receive_file(filename):
	rtpClientSocket.sendall(bytearray(filename, 'utf8'))
	# # load file
	rtpClientSocket.sendall(bytearray("get",'utf8'))
	didPass  = rtpClientSocket.recv(1024)
	if(str(didPass) == str(b'pass')):
		filesize = rtpClientSocket.recv(30)
		intBytes = int.from_bytes(filesize, byteorder='little')
		
		dataset = bytearray()
		print("Finished Creating a dataset array... ")
		run = True
		while run:
			rcvData = rtpClientSocket.recv(1024)
			if (rcvData != b"FAIL"):
				dataset.append(int.from_bytes(rcvData, byteorder='little'))
				# print("Adding to dataset...")
			else:
				print("Nothing else left to add to dataset... exiting")
				run = False
		print(dataset)
		print("Finished getting a file...")
	else:
		print("No File Found on Server")
	

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
		receive_file(fileG)
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