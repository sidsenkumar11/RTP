# FTA-server.py

# import RTP
import sys
import socket



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
	# # Check to see what the command is
	# if command is None:
	# 	global con
	# 	con = False      
	# elif command.decode('utf-8').split(' ')[0] == 'get':
	# 	# send_file(command)
	# 	print ("Got a get command")
	# 	con.send('Got get')
	# elif command.decode('utf-8').split(' ')[0] == 'post':
	# 	# get_file(command)
	# 	print ("Got a post command")
	# 	con.send('Got post')
	# else:
	# 	print("Invalid command received")
	# 	con.send('Got none')
	print('Waiting for new connection.')

def wait_and_receive_file():
	print("Came to wait_and_receive_file in server")
	con, addr = rtpServerSocket.accept()
	receive_file(con)
	closeConnection(con)

def receive_file(con):
	print("entering receive_file")

	filename = con.recv(1024)
	filesize = con.recv(30)

	print(filename)
	intBytes = int.from_bytes(filesize, byteorder='little')
	print(intBytes)
	# print(filesize)
	dataset = bytearray()
	print("Finidhsed Creating a dataset array... ")
	# print (dataset)

	run = True
	while run:
		rcvData = con.recv(1024)
		if (rcvData != b"FAIL"):
			dataset.append(int.from_bytes(rcvData, byteorder='little'))
			print("Adding to dataset...")
		else:
			print("Nothing else left to add to dataset... exiting")
			run = False
		
	print (dataset)
	print("Exiting receive_file function....")

	write_file(filename, dataset,con)
	# file_data = get_file(con)
	# send_file("filename")

def write_file(filename, dataset, con):

	print("Entering write_file function on server")
# 	# Write file; wb = write and binary
	file = open('new_' + str(filename.decode('utf8')), 'wb')
	print("Finished creating a new file...About to write")
	file.write(dataset)
	

	print("File written on server successfully")

def send_file(filename):

# 	# Need to tell server we are going to send file to server
# 	socket.RTP_Send(bytearray(filename, 'utf-8'))

# 	# load file
# 	fileBytes = open(command.split(' ')[i], 'rb').read()

# 	# Send file to server
# 	socket.RTP_Send(fileBytes)
	con.send(b'madeit')
	print("File has been sent by server")

def set_window(newSize):
	# epdate window size
	windowSize = int(newSize)
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
