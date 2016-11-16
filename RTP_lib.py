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

if __name__ == '__main__':

	# Testing segment creation and reading.

	# Data array is simply list of 12 bytes containing 0...11
	data_array = bytearray([])
	for i in range(0, 12):
		data_array.append(i)

	# Segment created,
	segment = create_segment(source_port=80, destination_port=20, sequence_num=123, ack_num=456, window=789, data_size=12, data=bytearray(data_array), syn = True)
	print("Created Segment: " + str(binascii.hexlify(segment)))
	print("Parsed Segment : " + str(read_segment(segment)))