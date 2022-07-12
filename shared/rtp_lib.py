import binascii
import logging
import math
import socket
from collections import namedtuple
from struct import pack, unpack

_logger = logging.getLogger(__name__)


"""
-----------------------------------
Theoretical Max UDP Datagram Size
-----------------------------------
UDP is a datagram-oriented protocol. This means that UDP messages are always
received in full. However, the "recvfrom" socket API allows the application to
supply a max number of bytes to receive. If the UDP message is 100 bytes, but
the app calls recvfrom(75), then only the first 75 bytes of the datagram are
returned to the app. So, the app must be sure to receive enough bytes such that
no data bytes are dropped. The UDP header provides 32 bits for datagram size,
so receiving 65535 bytes would definitely capture everything.

-----------------------------------
Theoretical Max IP Packet Size
-----------------------------------
The true max size of a UDP datagram is limited by the encapsulating IP packet.
IP packet headers also provide 32 bits for the size, so the theoretical max
size of an IP packet is 65535 bytes. The IP header is 20 bytes, and the UDP
header is 8 bytes, so the theoretical max application data that can be sent in
a single IP packet is 65535 - 20 - 8 = 65507 bytes.

-----------------------------------
Preventing IP Packet Fragmentation
-----------------------------------
While an IP packet could theoretically fit 65507 application data bytes, the
underlying link protocol (e.g. Ethernet) cannot send so much in a single frame.
The IP protocol will split the packet into multiple frames before sending and
reassemble them after receiving. This is known as fragmentation.

The max data size of a frame is also known as the MTU, or maximum transmission
unit. For Ethernet, the max frame size is 1518 bytes, which includes an 18 byte
header, so the MTU is 1500 bytes. To prevent IP fragmentation, the IP protocol
will send no more than 1500 bytes, including the IP header.

Since the IP header is 20 bytes, the maximum UDP datagram size should be:
1500 - 20 = 1480 bytes. Subtracting another 8 bytes for the UDP header, the max
application data that can be sent in a single frame is 1472 bytes.
"""

# Ethernet / IP / UDP Sizes
MAX_FRAME_SIZE = 1518
FRAME_HEADER_SIZE = 18
MAX_FRAME_DATA_SIZE = MAX_FRAME_SIZE - FRAME_HEADER_SIZE
IP_HEADER_SIZE = 20
UDP_HEADER_SIZE = 8
MAX_SAFE_UDP_DATA_SIZE = MAX_FRAME_DATA_SIZE - IP_HEADER_SIZE - UDP_HEADER_SIZE

# RTP Sizes
MAX_RTP_SEGMENT_SIZE = MAX_SAFE_UDP_DATA_SIZE
HEADER_SIZE = 160
MAX_DATA_PER_SEGMENT = MAX_SAFE_UDP_DATA_SIZE - HEADER_SIZE

# Max value of ACK is 2^32-1
# ACK represents next expected sequence number,
# so acknowledging 2^32-1 means we have received 2^32-2.
MAX_ACK_VAL = math.pow(2, 32) - 1
MAX_BUFFER_SIZE = MAX_ACK_VAL - 1
MAX_WINDOW_SIZE = math.floor(MAX_BUFFER_SIZE / MAX_DATA_PER_SEGMENT)

# In practice, our buffer and window will be much smaller.
# We'll assume a default 65536 byte application data buffer to match real TCP.
DEFAULT_BUFFER_SIZE = math.pow(2, 16)
DEFAULT_WINDOW_SIZE = math.floor(DEFAULT_BUFFER_SIZE / MAX_DATA_PER_SEGMENT)

Segment = namedtuple("Segment", "src_port dest_port seq_num ack_num special_bits window checksum data_size data")

# Computes the 16-bit BSD checksum on a byte array.
def checksum(bytearray):
    checksum = 0
    for byte in bytearray:
        checksum = (checksum >> 1) + ((checksum & 1) << 15)
        checksum += byte
        checksum &= 0xFFFF
    return checksum


# Data must be a bytearray.
def create_segment(src_port, dest_port, seq_num, ack_num, window, data=b"", syn=False, ack=False, fin=False, win=False):

    # Create reserved + special bits number
    special_bits = 0
    if fin:
        special_bits |= 0b1
    if syn:
        special_bits |= 0b10
    if ack:
        special_bits |= 0b100
    if win:
        special_bits |= 0b1000

    # Create initial segment with checksum of 0.
    segment = pack("!HHLLHHHH", src_port, dest_port, seq_num, ack_num, special_bits, window, 0, len(data))
    segment = bytearray(segment)
    segment = segment + data
    checksum_data = bytearray(pack("H", len(segment))) + segment

    # Compute checksum on [Segment Length] + [Segment]
    real_checksum = checksum(checksum_data)

    # Segment = Segment with correct checksum + data
    segment = pack(
        "!HHLLHHHH",
        src_port,
        dest_port,
        seq_num,
        ack_num,
        special_bits,
        window,
        real_checksum,
        len(data),
    )
    segment = segment + data

    # print("Segment Contents: " + str(binascii.hexlify(segment)))
    # print("Real checksum   : " + str(real_checksum))
    return segment


# Parses a bytearray segment from data buffer.
def read_segment(buffer):

    # Get segment from buffer
    data_length = int.from_bytes(buffer[18:20], byteorder="big")
    segment = buffer[: 20 + data_length]

    # Parse fields
    header = unpack("!HHLLHHHH", segment[:20])
    data = segment[20:]

    # Check checksum
    desired_checksum = header[6]
    orig_segment = pack("!HHLLHHHH", header[0], header[1], header[2], header[3], header[4], header[5], 0, header[7])
    orig_segment = bytearray(orig_segment)
    orig_segment = orig_segment + data
    orig_checksum_data = bytearray(pack("H", len(orig_segment))) + orig_segment
    real_checksum = checksum(orig_checksum_data)

    if desired_checksum != real_checksum:
        _logger.info(f"Transmission error: \n{binascii.hexlify(segment)}\n{binascii.hexlify(orig_segment)}")
        return None
    else:
        _logger.debug("Checksum matches!")

    return Segment(header[0], header[1], header[2], header[3], header[4], header[5], header[6], header[7], data)


if __name__ == "__main__":

    # Testing segment creation and reading.

    # Data array is simply list of 12 bytes containing 0...11
    data = bytearray([])
    for i in range(12):
        data.append(i)

    # Segment created,
    segment = create_segment(
        src_port=80,
        dest_port=20,
        seq_num=123,
        ack_num=456,
        window=789,
        data=data,
        syn=True,
    )

    print("Created Segment: " + str(binascii.hexlify(segment)))
    print("Parsed Segment : " + str(read_segment(segment)))
