import socket
import binascii
from struct import pack

def checksum(bytearray):
	checksum = 0
	for byte in bytearray:
		checksum = (checksum >> 1) + ((checksum & 1) << 15)
		checksum += byte
		checksum &= 0xffff
	return checksum

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

	return segment
	# print(binascii.hexlify(segment))
create_segment(source_port=80, destination_port=20, sequence_num=123, ack_num=456, window=789, data_size=12, data=bytearray([9, 11]), syn = True)






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


	def RTP_Accept(self):
		print("RTP Accept")





# RTP_INSTANCE = RTP()
# x = RTP_INSTANCE.RTP_Connect(("10.0.0.1", 80))
# x.RTP_Send()
# x.RTP_Recv()
# x.close()