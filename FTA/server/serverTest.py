# FTA-server.py

# import RTP
import sys
import socket
import os

def initialize(IPnum, portnum):
	IP = IPnum
	port = portnum
	# Not using IP to bind yet
	# socket.RTP_Bind(('', port))
	# socket.RTP_listen(1)
	rtpServerSocket.bind(('', port))
	rtpServerSocket.listen(1)
	print ("Finished Initializing...")

def prompt():
	#try:
	command = input('Enter some command for the FTA Server - \n [terminate, window, none]: ')

	# Check for the type of command input by the user
	if (command == 'terminate'):
		exit()
	elif (command == 'window'):
		s = input('Enter the new window size:')
		set_window(s)
	elif (command == 'none'):
		print("No command entered.")

	print('Waiting for new connection.')

def wait_and_receive_file():
	print("Came to wait_and_receive_file in server")
	con, addr = rtpServerSocket.accept()

	finished = False
	while not finished:
		finished = receive_file(con)
	# closeConnection(con)

def receive_file(con):
	print("entering receive_file")

	command = con.recv(1024)
	command = command.decode('utf-8')

	if command != "disconnect":
		command = command.split(' ')
		filename = command[1]
		command = command[0]

	# print("filename is: " + str(filename))
	# print("command is: " + str(command))

	if (str(command) == "get"):
		print("Switching to get function!")
		send_file(filename, con)
		return False
	elif (command == "post"):
		filesize = con.recv(30)
		print(filename)
		intBytes = int.from_bytes(filesize, byteorder='little')
		print(intBytes)
		# print(filesize)
		dataset = bytearray()
		print("Finished Creating a dataset array... ")
		# print (dataset)

		run = True
		while run:
			rcvData = con.recv(1024)
			if (rcvData != b"FAIL"):
				dataset.append(int.from_bytes(rcvData, byteorder='little'))
				# print("Adding to dataset...")
			else:
				print("Nothing else left to add to dataset... exiting")
				run = False
		
		print (dataset)
		write_file(filename, dataset)
		print("File uplaoded to server....")
		return False
	elif (command == "disconnect"):
		closeConnection(con)
		return True

def write_file(filename, dataset):

	print("Entering write_file function on server")
# 	# Write file; wb = write and binary

	with open('new' + filename, 'wb') as out:
		print("Finished creating a new file")
		out.write(dataset)
		print("File written on server successfully")


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

def send_file(filename, con):

	if(os.path.exists(filename)):
		con.sendall(bytearray("pass",'utf8'))
		print("File has been found on server")

		with open(filename, 'rb') as f:
			fileBytes = f.read()

		con.sendall((len(fileBytes)).to_bytes(30, byteorder='little'))
		for b in bytes_from_file(filename):
			if(b != -1):
				con.sendall(b.to_bytes(1024, byteorder='little'))
			else:
				con.sendall(b"FAIL")
		print("File has been sent to the client.")	
	else:
		con.sendall(bytearray("didNotPass",'utf8'))
		print("File was not found on the server")

def set_window(newSize):
	# epdate window size
	pass
	# socket.setMaxWindowSize(newSize)

	print('New window size set to: ' + str(newSize))

def closeConnection(con):
	con.close()

def exit():
	rtpServerSocket.close()
	sys.exit()


if (len(sys.argv) > 1):
	port = int(sys.argv[1])
	print("Port is: " + str(port))
else:
	print("Port is not given. Auto set to 8080.")
	port = 8080

rtpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
IP = socket.gethostbyname(socket.gethostname())
print ("IP is: " + str(IP))

initialize(IP, port)
while True:
	prompt()
	wait_and_receive_file()
	print("finished wait_and_receive_file in server")
