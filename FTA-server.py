# FTA-server.py

import RTP
import sys


isConnected = False

port = int(sys.argv[1])

def initial(IPnum, portnum):
	IP = IPnum
	port = portnum

	global socket

	socket = RTP.RTP()

	socket.RTP_Bind(('', port))
	socket.listen(1)


def waitForConnect():
	global con
	if(con):
		waitForCommands()   
	else:    
		con = socket.acceptRTPConnection(IP,port)

def terminate():
	sys.exit()
	raise Exception('terminate')

def set_window(newSize):
	# epdate window size
	windowSize = newSize
	socket.setMaxWindowSize(newSize)

	print('New window size set')

def prompt():
	#try:
	print('Enter a command for the FTA Server:')
	command = input()

	# Check for the type of command input by the user
	if command == 'terminate':
		terminate()
	elif command == 'window':
		set_window(int(user_input.split(' ')[1]))
	else:
		print('That was not a valid command')


initial(IP, port)

while True:
	waitForConnect()