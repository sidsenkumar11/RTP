import socket
import binascii
from struct import pack, unpack

# Computes the 16-bit BSD checksum on a byte array.
def checksum(bytearray):
	checksum = 0
	for byte in bytearray:
		checksum = (checksum >> 1) + ((checksum & 1) << 15)
		checksum += byte
		checksum &= 0xffff
	return checksum

# Data must be a bytearray.
def create_segment(source_port, destination_port, sequence_num, ack_num, window, data_size, data, syn=False, ack=False, fin=False):

	# Create reserved + special bits number
	special_bits = 0
	if fin:
		special_bits = special_bits + int('1', 2)
	if syn:
		special_bits = special_bits + int('10', 2)
	if ack:
		special_bits = special_bits + int('100', 2)

	# Create initial segment with checksum of 0.
	segment = pack("!HHLLHHHH", source_port, destination_port, sequence_num, ack_num, special_bits, window, 0, data_size)
	segment = bytearray(segment)
	segment = segment + data
	checksum_data = bytearray([len(segment)]) + segment

	# Compute checksum on [Segment Length] + [Segment]
	real_checksum = checksum(checksum_data)

	# Segment = Segment with correct checksum + data
	segment = pack("!HHLLHHHH", source_port, destination_port, sequence_num, ack_num, special_bits, window, real_checksum, data_size)
	segment = segment + data

	# print("Segment Contents: " + str(binascii.hexlify(segment)))
	# print("Real checksum   : " + str(real_checksum))
	return segment

# Parses a bytearray segment from data buffer.
def read_segment(buffer):

	# Get segment from buffer
	data_length = int.from_bytes(buffer[18:20], byteorder='big')
	segment = buffer[:20 + data_length]

	# Parse fields
	header = unpack("!HHLLHHHH", segment[:20])
	data = segment[20:]

	# Check checksum
	desired_checksum = header[6]
	orig_segment = pack("!HHLLHHHH", header[0], header[1], header[2], header[3], header[4], header[5], 0, header[7])
	orig_segment = bytearray(orig_segment)
	orig_segment = orig_segment + data
	orig_checksum_data = bytearray([len(orig_segment)]) + orig_segment
	real_checksum = checksum(orig_checksum_data)

	if desired_checksum != real_checksum:
		print("Transmission error")
	else:
		print("Checksum matches!")

	return (header[0], header[1], header[2], header[3], header[4], header[5], header[6], header[7], data)

data_array = bytearray([])
for i in range(0, 12):
	data_array.append(i)

y = create_segment(source_port=80, destination_port=20, sequence_num=123, ack_num=456, window=789, data_size=12, data=bytearray(data_array), syn = True)
print(read_segment(y))




class Connection:
	def __init__(self, info, client_socket):
		self.info = info
		self.client_socket = client_socket
		self.client_socket.bind('', 13)

		# Create SYN packet
		create_packet()
		print("Intialization stuff")

	def RTP_Send(self):
		print("RTP Send")

	def close(self):
		print("Closing")

	def RTP_Recv(self):
		print("Receiving data")

class RTP:

	def __init__(self):
		print("RTP init")

	def RTP_Connect(self, info):
		self.info = info
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		print("RTP Connect to: " + self.info[0] + ":" + str(self.info[1]))
		return Connection(info, client_socket)

	def RTP_Bind(self, info):
		print("RTP Bind")


	def RTP_Accept(self, info):
		print("RTP Accept")

	def get_IP(self):
		return 13

	def listen(self, info):
		return 1





# RTP_INSTANCE = RTP()
# x = RTP_INSTANCE.RTP_Connect(("10.0.0.1", 80))
# x.RTP_Send()
# x.RTP_Recv()
# x.close()