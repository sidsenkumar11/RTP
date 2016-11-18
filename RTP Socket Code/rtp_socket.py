import threading
import socket
from rtp_lib import *

# UDP socket Max Data returned.
# BUFFER_SIZE = 2097152 # 2 MB Send/Receive Buffers. Buffer minimum size is one segment (2^16ish)
BUFFER_SIZE = 65536 # 64KB Buffer size.
WINDOW_SIZE =  65535 # Num. Segments in flight without any ACKs. Max allowable with a 16 bit ACK number,
TIMEOUT = 2 # Before timeout.
MAX_NUM_ATTEMPTS = 3 # Before failed connection.
MAX_NUM_CONNECTIONS = 2 # Before refusing connections.

class rtp_socket:

	# Creates a UDP socket and initializes connection variables.
	def __init__(self, IPv6=False, window_size=WINDOW_SIZE, debug=False):

		self.debug = debug
		self.IPv6 = IPv6
		self.source_port = 1111
		self.window_size = window_size
		self.window_remaining = window_size
		self.send_buffer = bytearray(BUFFER_SIZE)
		self.receive_buffer = bytearray(BUFFER_SIZE)
		self.sequence_num = 0
		self.ack_num = 0
		self.listening = False

		self.s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) if IPv6 else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.settimeout(TIMEOUT)


	# Server: Binds UDP socket to an IP and Port.
	def bind(self, info):
		self.s.bind(info)


	# Server: Sets RTP socket to listen for connections.
	def listen(self, num_connections=MAX_NUM_CONNECTIONS):
		self.listening = True
		self.current_num_connections = 0
		self.max_connections = num_connections


	# Server: Accepts a connection.
	def accept(self):

		if not self.listening:
			raise ConnectionRefusedError("Socket not listening for connections")

		if self.current_num_connections >= self.max_connections:
			raise ConnectionRefusedError("All connections full")

		if self.debug:
			print("Accepting connections! Waiting for SYN...")

		# Wait for SYN segment.
		self.s.settimeout(None)
		syn_seg, client_address = self.s.recvfrom(BUFFER_SIZE)
		syn_seg = read_segment(syn_seg)

		while syn_seg == None or syn_seg[4] & 0x2 != 0x2:
			# Packet corrupted or packet was not SYN.
			if self.debug:
				print("Received a packet that was not SYN or was corrupted")

			# Wait for retransmission.
			syn_seg, client_address = self.s.recvfrom(BUFFER_SIZE)
			syn_seg = read_segment(syn_seg)

		if self.debug:
			print("Received SYN! Sending SYN/ACK, waiting for an ACK...")

		# On SYN received:
		con_sock_info = {}
		con_sock_info['opp_host_window'] = syn_seg[5]
		con_sock_info['ack_num'] = 1
		con_sock_info['seq_num'] = 1
		con_sock_info['destination_IP'] = client_address[0]
		con_sock_info['destination_port'] = client_address[1]
		con_sock_info['first_data_segment'] = None

		# Create a SYN/ACK segment.
		data_size = 0
		data = bytearray([])
		synack_seg = create_segment(self.source_port, client_address[1], self.sequence_num, self.ack_num, self.window_remaining, data_size, data, syn=True, ack=True)

		# Send SYN/ACK.
		response_received = False
		attempt_num = 1
		ack_seg = b''
		while not response_received:
			try:
				self.s.sendto(synack_seg, (client_address[0], client_address[1]))
				ack_seg = read_segment(self.s.recvfrom(BUFFER_SIZE)[0])
				if ack_seg != None:
					response_received = True
			except timeout:
				attempt_num = attempt_num + 1

			if attempt_num > MAX_NUM_ATTEMPTS:
				raise TimeoutError("Could not reach client destination: " + str(client_address[0]) + ":" + str(client_address[1]))

		# On ACK received:
		if self.debug:
			print("Received the ACK! Connection established.")

		if ack_seg[4] & 0x4 != 0x4:
			con_sock_info['first_data_segment'] = ack_seg

		# Create connection socket.
		conn = rtp_socket(IPv6=self.IPv6, window_size=self.window_size, debug=self.debug)
		conn.set_connection_info(con_sock_info)
		conn.s.connect((conn.destination_IP, conn.destination_port))

		# Connection established.
		self.s.settimeout(TIMEOUT)
		self.current_num_connections = self.current_num_connections + 1
		return (conn, client_address)

	# Client: Perform 3-way handshake and set up buffers.
	def connect(self, destination):

		if self.debug:
			print("Initiating a connection...")

		# Set destination information.
		self.destination_IP = destination[0]
		self.destination_port = destination[1]

		# Set segment variables.
		data_size = 0
		data = bytearray([])

		# Create a SYN segment.
		syn_seg = create_segment(self.source_port, self.destination_port, self.sequence_num, self.ack_num, self.window_remaining, data_size, data, syn=True)

		# Send SYN and wait for SYN/ACK.
		if self.debug:
			print("Sending a SYN...")

		response_received = False
		attempt_num = 1
		synack_seg = b''
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

		# Sends data through connection
	    send_thread = threading.Thread(target=send_data, args = (data))
	    # ack_thread = threading.Thread(target=receive_ack, args = ())

	    send_thread.daemon = True
	    send_thread.start()
	    send_thread.join()

	    print("Finished inserting data into sendbuffer")
	    # ack_thread.daemon = True
	    # ack_thread.start()

	def send_data(self, data):
		data = bytearray(data)
		num_bytes = len(data)

		for i in range(0, len(data)):
			send_buffer[i] = data[i]

	def receive_ack(self, data):
		pass
		

	def recv(self, BUFFER_SIZE):
		pass
		# Receives data and puts into a buffer of buffer size.
		# Return buffer

	def close(self, parent_socket=None):

		# Closes the connection
		# Releases resoures associated with connection

		if self.debug:
			print("Closing connection...")

		# Free buffers and reset variables.
		self.send_buffer = bytearray([])
		self.receive_buffer = bytearray([])
		self.sequence_num = 0
		self.ack_num = 0
		self.destination_IP = ''
		self.destination_port = 0

		if self.debug:
			print("Connection closed!")

	# TODO: Move contents of buffer into new buffer of new window size.
	def set_window_size(self, n):
		self.window_size = n

	def get_destination(self):
		return (self.destination_IP, self.destination_port)

	# Server: Initializes variables for a new server connection.
	def set_connection_info(self, con_info):
		self.opp_host_window = con_info['opp_host_window']
		self.ack_num = con_info['ack_num']
		self.seq_num = con_info['seq_num']
		self.destination_IP = con_info['destination_IP']
		self.destination_port = con_info['destination_port']

		# TODO: Handle this.
		if con_info['first_data_segment'] != None:
			print("Server got data for first segment instead of ACK.")