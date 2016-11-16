import socket
from RTP_lib import *

# Returns this machine's IP address.
def get_IP():
	return socket.gethostbyname(socket.gethostname())

class rtp_socket:

	# Creates a UDP socket with IPv4 or IPv6.
	def __init__(self, IPv6 = False):

		# rtp_socket supports both IPv4 and IPv6.
		self.s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) if IPv6 else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.window_size = 
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

		# info = (Destination IP, Destination Port)
		self.destination_info = info

		# Construct a SYN packet.

		# The below gets the source_port being used for this connection.
		# Might be useful if ever implement multiplexing functionality.
		# source_port = self.s.getsockname()[1]
		source_port = 1111
		destination_port = destination_info[1]
		sequence_num = 999
		ack_num = 444
		window = 1024
		data_size = 0
		data = bytearray([])

		syn_seg = create_segment(source_port, destination_port, sequence_num, ack_num, window, data_size, data, syn=True)
		return syn_seg

	def sendall(self, data):
		pass
		# Sends data through connection

	def receive(self, BUFFER_SIZE):
		pass
		# Receives data and puts into a buffer of buffer size.
		# Return buffer

	def close(self):

		# Closes the connection
		# Releases resoures associated with connection
		self.s.close()

	def set_window_size(self, n):
		self.window_size = n

sock = rtp_socket(IPv6=True)
print(read_segment(sock.connect(('10.0.0.1', 8080))))
sock.close()
