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
	if(debug): print ("Initializion Successful.")

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
		if(debug): print("No command entered.")
	else:
		print("Invalid entry.")
		exit()

	print('Waiting for new connection...')

def wait_and_receive_file():
	try:
		con, addr = rtpServerSocket.accept()

		finished = False
		while not finished:
			finished = receive_file(con)
		# closeConnection(con)
	except:
		if(debug): print("Something went wrong in wait_and_receive_file. Restarting.")
		# closeConnection()
		# initialize(IP, port)
		# wait_and_receive_file()

def receive_file(con):
	try:
		command = con.recv(1024)
		command = command.decode('utf-8')

		if command != "disconnect":
			command = command.split(' ')
			filename = command[1]
			command = command[0]

		# print("filename is: " + str(filename))
		# print("command is: " + str(command))

		if (str(command) == "get"):
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
				i = 0
				while i < intBytes:
					rcvData = con.recv(1024)
					t = bytearray(rcvData)
					dataset.extend(t)
					i = i + len(rcvData)
					
				write_file(filename, dataset)
				if(debug): print("File uploaded to server.")
				return False
			elif(str(check) == str(b'n')):
				if(debug): print("File not uploaded to server.")
				return False
		elif (command == "disconnect"):
			closeConnection(con)
			return True
	except:
		if(debug): print("Something went wrong in receive_file. Restarting.")
		# closeConnection()
		# initialize(IP, port)
		# receive_file()

def write_file(filename, dataset):

	with open(filename, 'wb') as out:
		out.write(dataset)
		if(debug): print("File written on server successfully.")


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
		if(debug): print("File has been found on server.")

		with open(filename, 'rb') as f:
			fileBytes = f.read()

		con.sendall((len(fileBytes)).to_bytes(30, byteorder='little'))
		for b in bytes_from_file(filename):
			if(b != -1):
				con.sendall(b)

		if(debug): print(filename + " has been sent to client.")
	else:
		con.sendall(bytearray("didNotpass",'utf8'))
		if(debug): print("File was not found on the server.")

def set_window(newSize):
	# epdate window size
	pass
	# socket.setMaxWindowSize(newSize)

	if(debug): print('New window size set to: ' + str(newSize))

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
debug = False
isDebug = input("Would you like to turn on debug mode? [y/n] ")
if(isDebug):
	debug = True

rtpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
IP = socket.gethostbyname(socket.gethostname())
print ("IP is: " + str(IP))

initialize(IP, port)
while True:
	prompt()
	wait_and_receive_file()
	if(debug): print("finished wait_and_receive_file in server")
