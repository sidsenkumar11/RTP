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
	try:
		print("Came to wait_and_receive_file in server")
		con, addr = rtpServerSocket.accept()

		finished = False
		while not finished:
			finished = receive_file(con)
		# closeConnection(con)
	except:
		print("Something went wrong in wait_and_receive_file. Restarting.")
		wait_and_receive_file()

def receive_file(con):
	try:
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
			intBytes = int.from_bytes(filesize, byteorder='little')
			if(os.path.exists(filename)):
				con.sendall(b'FILEEXISTS')
			check = con.recv(1024)
			if (str(check) == str(b'y')):
				dataset = bytearray()
				print("Finished Creating a dataset array... ")
				i = 0
				while i < intBytes:
					rcvData = con.recv(1024)
					t = bytearray(rcvData)
					dataset.extend(t)
					i = i + len(rcvData)
					
				print("Nothing else left to add to dataset... exiting")
				write_file(filename, dataset)
				print("File uploaded to server....")
				return False
			elif(str(check) == str(b'n')):
				print("File not uploaded to server....")
				return False
		elif (command == "disconnect"):
			closeConnection(con)
			return True
	except:
		print("Something went wrong in receive_file. Restarting.")
		receive_file()

def write_file(filename, dataset):

	print("Entering write_file function on server")
# 	# Write file; wb = write and binary

	with open(filename, 'wb') as out:
		print("Finished creating a new file")
		out.write(dataset)
		print("File written on server successfully")


def bytes_from_file(filename, chunksize = 1024):
	with open(filename, "rb") as f:
		while True:
			chunk = f.read(chunksize)
			if chunk:
				yield chunk
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
				con.sendall(b)

		print(filename + " has been sent to client.")
	else:
		con.sendall(bytearray("didNotpass",'utf8'))
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
