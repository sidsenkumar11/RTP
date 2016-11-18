# FTA-client.py

# import RTP
import sys
import socket
import os


def connect(IP, port): 
	try:
		rtpClientSocket.connect((IP,port))
	except:
		print ("Could not connect to server.")

	print("Connection Successful to: " + IP + ":" + str(port))

def receive_file(filename):
	# # load file
	rtpClientSocket.sendall(bytearray("get " + str(filename),'utf8'))

	didPass  = rtpClientSocket.recv(1024)
	if(str(didPass) == str(b'pass')):
		filesize = rtpClientSocket.recv(30)
		intBytes = int.from_bytes(filesize, byteorder='little')
		
		dataset = bytearray()

		i = 0
		while i < intBytes:
			rcvData = rtpClientSocket.recv(1024)
			t = bytearray(rcvData)
			dataset.extend(t)
			i = i + len(rcvData)

		print("Finished adding to dataset...")
		write_file(filename, dataset)
		print("Completed getting a file from server.")
	else:
		print("No File Found on Server.")

def write_file(filename, dataset):

	if(os.path.exists(filename)):
		check = input('This file already exists, do you want to overwrite it? [y,n] ')
		if (check == 'y'):
			print("Okay. Going to overwrite the file.")
			with open(filename, 'wb') as out:
				out.write(dataset)
				print("File written on client successfully...")
		elif(check == 'n'):
			print("Okay. Will not overwrite the file.")
		else:
			print("Invalid input. Did not overwrite the file.")


def bytes_from_file(filename, chunksize = 1024):
	with open(filename, "rb") as f:
		while True:
			chunk = f.read(chunksize)
			if chunk:
				yield chunk
			else:
				yield -1
				break

def send_file(filename):
	if(os.path.exists(filename)):
		# # Need to tell server we are going to send file to server
		# socket.RTP_Send(bytearray(filename, 'utf-8'))
		rtpClientSocket.sendall(bytearray("post " + str(filename),'utf8'))
		# # load file
		with open(filename, 'rb') as f:
			fileBytes = f.read()

		# Sending Length of file in bytes to server
		rtpClientSocket.sendall((len(fileBytes)).to_bytes(30, byteorder='little'))
		check = rtpClientSocket.recv(1024)
		if(str(check) == str(b'FILEEXISTS')):
			check = input('This file already exists on the server, do you want to overwrite it? [y,n] ')
		if (check == 'y'):
			rtpClientSocket.sendall(b'y')
			# Send chunks of 1024 bytes to server
			for b in bytes_from_file(filename):
				if(b != -1):
					rtpClientSocket.sendall(b)
		
			print(filename + " has been sent to server.")
		elif(check == 'n'):
			rtpClientSocket.sendall(b'n')
			print('Okay. Will not send this file.')
		else:
			rtpClientSocket.sendall(b'n')
			print('Invalid Input. Did not send file.')
	else:
		print("Sorry, client can't find that file.")




def set_window(newSize):
	# epdate window size
	windowSize = newSize
	# socket.setMaxWindowSize(newSize)

	print('New window size set to: ' + str(newSize))


def disconnect():
	# Disconnect from the server
	rtpClientSocket.sendall(bytearray("disconnect", 'utf8'))
	rtpClientSocket.close()

	print('Disconnected...')

def exit():
	
	if isConnected:
		disconnect()
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
		isConnected = False
		disconnect()
	elif command == 'exit':
		exit()
	elif not isConnected:
		print ("Currently not connected. Please connect.")
	else:
		print('That was not valid. Please enter a valid command')