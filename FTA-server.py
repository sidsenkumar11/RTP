import RTP
import sys


isConnected = False

UDPport = int(sys.argv[1])

def initial(IPnum, portnum):
	IP = IPnum
	UDPport = portnum

	global socket

	socket = RTP.Connection()

	socket.RTP_Bind(IP, UDPport)
	socket.listen()


def waitForConnect():
    global con
    if(con):
        waitForCommands()   
    else:    
        con = socket.acceptRTPConnection(IP,UDPport)

def terminate():
	sys.exit(0)
    raise Exception('terminate')


def prompt():
    #try:
    print('Enter a command for the FTA Server:')
    command = input()

    # Check for the type of command input by the user
    if command == 'terminate':
        terminate()
    else:
        print('That was not a valid command')


initial(IP, UDPport)

while True:
    waitForConnect()