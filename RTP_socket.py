import socket
import RTP_lib

# Returns this machine's IP address.
def get_IP():
	return socket.gethostbyname(socket.gethostname())

class rtp_socket:

	# Creates a UDP socket with IPv4 or IPv6.
	def __init__(self, IPv6 = False):

		# rtp_socket supports both IPv4 and IPv6.
		self.s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) if IPv6 else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	# Server: Binds UDP socket to an IP and Port.
	def bind(self, info):
		self.s.bind(info)

	# Server: Sets UDP socket to listen for connections.
	def listen(self, num_connections):
		self.s.listen(num_connections)

	# Server: Accepts a connection.
	def accept():

		# Send an ACK when a SYN packet comes.
		# When SYN/ACK comes, the connection is accepted.

		data, client_address = s.recvfrom()
		return (rtp_socket(), (client_IP, client_port))


	# Client: Perform 3-way handshake and set up buffers.
	def connect(self, info):
		self.info = info

	def sendall(self, data):

		# Sends data through connection

	def receive(self, BUFFER_SIZE):

		# Receives data and puts into a buffer of buffer size.
		# Return buffer

	def close(self):

		# Closes the connection
		# Releases resoures associated with connection
