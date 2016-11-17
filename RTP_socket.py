import socket
from RTP_lib import *

# UDP socket Max Data returned.
BUFFER_SIZE = 65535
MAX_NUM_ATTEMPTS = 10 # Before failed connection.
TIMEOUT = 5

class rtp_socket:

	# Creates a UDP socket with IPv4 or IPv6.
	def __init__(self, IPv6=False, window_size=BUFFER_SIZE, debug=False):

		# rtp_socket supports both IPv4 and IPv6.
		self.s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) if IPv6 else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.settimeout(TIMEOUT)
		self.debug = debug
		self.IPv6 = IPv6
		self.window_size = window_size
		self.window_remaining = window_size
		self.sequence_num = 0
		self.ack_num = 0
		# The below gets the source_port being used for this connection.
		# Might be useful if ever implement multiplexing functionality.
		# source_port = self.s.getsockname()[1]
		self.source_port = 1111
		self.max_connections = 0


	# Server: Binds UDP socket to an IP and Port.
	def bind(self, info):
		self.my_info = info
		self.s.bind(info)

	# Server: Sets RTP socket to listen for connections.
	def listen(self, num_connections):
		self.max_connections = num_connections

	# Server: Accepts a connection.
	def accept(self):

		# conn = rtp_socket(IPv6=self.IPv6)
		# conn.bind(self.my_info)
		self.complete_handshake()
		return (self, self.get_destination())

	# Client: Perform 3-way handshake and set up buffers.
	def connect(self, info):

		if self.debug:
			print("Initiating a connection...")

		# info = (Destination IP, Destination Port)
		self.destination_IP = info[0]
		self.destination_port = info[1]

		# Set segment variables.
		data_size = 0
		data = bytearray([])

		# Allocate buffers
		self.send_buffer = bytearray(BUFFER_SIZE)
		self.receive_buffer = bytearray(BUFFER_SIZE)

		# Create and send the SYN segment.
		# Then receive the SYN/ACK segment.
		syn_seg = create_segment(self.source_port, self.destination_port, self.sequence_num, self.ack_num, self.window_remaining, data_size, data, syn=True)
		synack_seg = b''

		if self.debug:
			print("Sending a SYN...")
		response_received = False
		attempt_num = 0
		while not response_received:
			try:
				self.s.sendto(syn_seg, (self.destination_IP, self.destination_port))
				synack_seg = read_segment(self.s.recvfrom(BUFFER_SIZE)[0])
				if synack_seg != None and synack_seg[4] & 0x6 == 0x6:
					response_received = True
			except socket.timeout:
				attempt_num = attempt_num + 1

			if attempt_num > MAX_NUM_ATTEMPTS:
				raise TimeoutError("Could not reach server destination: " + self.destination_IP + ":" + str(self.destination_port))

		# TODO: Parse synack_seg
		self.opp_host_window = synack_seg[5]

		if self.debug:
			print("Received the SYN/ACK, sending an ACK...")

		# Create and send the ACK segment.
		self.sequence_num = self.sequence_num + 1
		self.ack_num = self.ack_num + 1

		ack_seg = create_segment(self.source_port, self.destination_port, self.sequence_num, self.ack_num, self.window_remaining, data_size, data, ack=True)
		self.s.sendto(ack_seg, (self.destination_IP, self.destination_port))

		if self.debug:
			print("ACK sent. Connection established!")

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

		if self.debug:
			print("Closing connection...")
		self.s.close()

		if self.debug:
			print("Connection closed!")

	def set_window_size(self, n):
		self.window_size = n

	def get_destination(self):
		return (self.destination_IP, self.destination_port)

	def complete_handshake(self):

		if self.debug:
			print("Waiting for SYN...")

		# Wait for SYN segment.
		self.s.settimeout(None)
		syn_seg, client_address = self.s.recvfrom(BUFFER_SIZE)
		syn_seg = read_segment(syn_seg)
		num_attempts = 0

		if self.debug:
			print("Received a packet.")

		while syn_seg == None or syn_seg[4] & 0x2 != 0x2:
			# Packet corrupted or packet was not SYN.
			if self.debug:
				print("Packet was not SYN or was corrupted")
			if num_attempts > MAX_NUM_ATTEMPTS:
				raise TimeoutError("Could not accept connection")
			else:
				num_attempts = num_attempts + 1

			# Wait for retransmission.
			syn_seg, client_address = self.s.recvfrom(BUFFER_SIZE)
			syn_seg = read_segment(syn_seg)

		if self.debug:
			print("Packet was SYN! Sending a SYN/ACK, waiting for an ACK...")

		# On SYN received:
		self.opp_host_window = syn_seg[5]
		self.send_buffer = bytearray(BUFFER_SIZE)
		self.receive_buffer = bytearray(BUFFER_SIZE)

		self.s.settimeout(TIMEOUT)
		self.ack_num = self.ack_num + 1
		self.destination_IP = client_address[0]
		self.destination_port = client_address[1]

		# Create a SYN/ACK segment.
		data_size = 0
		data = bytearray([])
		synack_seg = create_segment(self.source_port, self.destination_port, self.sequence_num, self.ack_num, self.window_remaining, data_size, data, syn=True, ack=True)
		self.sequence_num = self.sequence_num + 1

		# Send SYN/ACK.
		response_received = False
		attempt_num = 0
		while not response_received:
			try:
				self.s.sendto(synack_seg, (self.destination_IP, self.destination_port))
				ack_seg = read_segment(self.s.recvfrom(BUFFER_SIZE)[0])
				if ack_seg != None:
					response_received = True
			except timeout:
				attempt_num = attempt_num + 1

			if attempt_num >= 10:
				raise TimeoutError("Could not reach client destination: " + self.destination_IP + ":" + str(self.destination_port))

		print("Received the ACK! Connection established.")

		# When ACK comes, the connection is accepted.
		# TODO: Parse ACK segment.