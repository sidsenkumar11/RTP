import socket
from struct import *
import binascii



def create_packet(source_port, destination_port, sequence_num, ack_num, window, data_size, data, syn=False, ack=False, fin=False):
	# I = int, 4 bytes
	# H = unsigned short, 2 bytes
	# ! = network byte order
	HEADER_FORMAT = "!HHIIHHHHb"
	# Create reserved + special bits number
	special_bits = 0
	if fin:
		special_bits = special_bits + int('1', 2)
	if syn:
		special_bits = special_bits + int('10', 2)
	if ack:
		special_bits = special_bits + int('100', 2)


	# y = pack('hhllhhhhX', source_port, destination_port, sequence_num, ack_num, special_bits, window, 0, data_size, data)
	y = pack(HEADER_FORMAT, source_port, destination_port, sequence_num, ack_num, special_bits, window, 0, data_size, data)
	print ("Packed(in ascii): " + str(binascii.hexlify(y)))
	
	ret = ""
	for bit in y: 
		ret += str(hex(ord(bit))) + " "
	print "Packed(in hex): " + ret
	
	unpack_packet(HEADER_FORMAT, y)

def unpack_packet(HEADER_FORMAT, packed_data):
	print ("Unpacked:" + str(unpack(HEADER_FORMAT, packed_data)))


create_packet(80, 20, 73, 456, 789, 6, 100, syn = True, ack = False, fin = False)
# data size : byte format requires -128 <= number <= 127

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