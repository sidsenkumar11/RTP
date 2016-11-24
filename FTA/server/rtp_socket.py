import math
import threading
import signal
import socket
import sys

from rtp_lib import *

BUFFER_SIZE = 65536 # 64KB buffer size.
WINDOW_SIZE =  int(65535 / max_safe_data_size()) # Max num. segments in flight without any ACKs. Max allowable with a 16 bit ACK number.
TIMEOUT = 1 # Seconds before timeout.
MAX_NUM_ATTEMPTS = 3 # Before failed to send/receive in connection.
MAX_NUM_CONNECTIONS = 1 # Before refusing connections.

class rtp_socket:

    # Creates a UDP socket and initializes connection variables.
    def __init__(self, IPv6=False, window_size=WINDOW_SIZE, debug=False):

        # Create UDP socket.
        self.s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) if IPv6 else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.ack_num = 0
        self.debug = debug
        self.destination_IP = None
        self.destination_port = None
        self.IPv6 = IPv6
        self.is_conn = False
        self.listening = False
        self.sequence_num = 0
        self.source_port = 1111
        self.window_size = window_size if window_size * max_safe_data_size() <= 65535 else -1
        self.window_remaining = self.window_size

        if self.window_size == -1:
            raise Exception("Invalid Window Size")

    # Server: Binds UDP socket to an IP and Port.
    def bind(self, info):
        self.s.bind(info)

    # Server: Sets RTP socket to listen for connections.
    def listen(self, num_connections=MAX_NUM_CONNECTIONS):
        self.listening = True
        rtp_socket.current_num_connections = 0
        self.max_connections = num_connections

    # Server: Accepts a connection.
    def accept(self):

        if not self.listening:
            raise ConnectionRefusedError("Socket not listening for connections")

        if rtp_socket.current_num_connections >= self.max_connections:
            raise ConnectionRefusedError("All connections full")

        if self.debug:
            print("Accepting connections! Waiting for SYN...")

        # Wait for SYN segment.
        syn_seg, client_address = self.s.recvfrom(max_safe_data_size() + header_size())
        syn_seg = read_segment(syn_seg)

        while syn_seg == None or syn_seg[4] & 0x2 != 0x2:
            # Packet corrupted or packet was not SYN.
            if self.debug:
                print("Received a packet that was not SYN or was corrupted")

            # Wait for retransmission.
            syn_seg, client_address = self.s.recvfrom(max_safe_data_size() + header_size())
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
        self.s.settimeout(TIMEOUT)

        while not response_received:
            try:
                self.s.sendto(synack_seg, (client_address[0], client_address[1]))
                ack_seg = read_segment(self.s.recvfrom(max_safe_data_size() + header_size())[0])
                if ack_seg != None:
                    response_received = True
            except timeout:
                attempt_num = attempt_num + 1

            if attempt_num > MAX_NUM_ATTEMPTS:
                raise TimeoutError("Could not reach client destination: " + str(client_address[0]) + ":" + str(client_address[1]))

        # On ACK received:
        self.s.settimeout(None)
        if self.debug:
            print("Received the ACK! Connection established.")

        if ack_seg[4] & 0x4 != 0x4:
            con_sock_info['first_data_segment'] = read_segment(ack_seg)

        # Create connection socket.
        con_sock_info['socket'] = self.s.dup()
        conn = rtp_socket(IPv6=self.IPv6, window_size=self.window_size, debug=self.debug)
        conn.set_connection_info(con_sock_info)

        # Connection established.
        rtp_socket.current_num_connections = rtp_socket.current_num_connections + 1
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
        self.s.settimeout(TIMEOUT)
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

        self.s.settimeout(None)
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

        # data = bytearray(data)
        num_bytes = len(data)

        # Sends data through connection
        self.send_data(data, num_bytes)

        if self.debug:
            print("Sent_data finished execution.")

    # Send all the bytes of data.
    def send_data(self, data, num_bytes):

        # 0. GBN Sliding Window Protocol Variables.
        byte_num = 0
        segment_data_size = max_safe_data_size() if max_safe_data_size() <= self.window_size else self.window_size
        win_base = 0
        next_seg = 0
        segments_in_transit = 0

        # 1. Split data into segments.
        segments = [None] * math.ceil(float(num_bytes) / segment_data_size)
        ack_nums = [None] * len(segments)

        if len(segments) > 1:
            for i in range(0, len(segments) - 1):
                segments[i] = create_segment(self.source_port, self.destination_port, self.sequence_num + byte_num, self.ack_num, self.window_remaining, segment_data_size, data[byte_num:byte_num + segment_data_size])
                byte_num = byte_num + segment_data_size
                ack_nums[i] = self.sequence_num + byte_num

        if num_bytes % segment_data_size != 0:
            segments[len(segments) - 1] = create_segment(self.source_port, self.destination_port, self.sequence_num + byte_num, self.ack_num, self.window_remaining, num_bytes % segment_data_size, data[byte_num:byte_num + num_bytes % segment_data_size])
            byte_num = byte_num + num_bytes % segment_data_size
            ack_nums[len(segments) - 1] = self.sequence_num + byte_num
        else:
            segments[len(segments) - 1] = create_segment(self.source_port, self.destination_port, self.sequence_num + byte_num, self.ack_num, self.window_remaining, segment_data_size, data[byte_num:byte_num + segment_data_size])
            byte_num = byte_num + segment_data_size
            ack_nums[len(segments) - 1] = self.sequence_num + byte_num

        # 2. Send initial segments.
        while next_seg < len(segments) and segments_in_transit + 1 <= self.window_size:

            self.s.sendto(segments[next_seg], (self.destination_IP, self.destination_port))
            segments_in_transit = segments_in_transit + 1
            next_seg = next_seg + 1

        # 3. Send segments as we receive ACKs.
        signal.signal(signal.SIGALRM, self.timeout)
        attempt_num = 1

        while win_base < len(segments):

            try:
                signal.alarm(TIMEOUT)
                ack_seg = self.s.recv(header_size())
                ack_seg = read_segment(ack_seg)

                if ack_seg != None:

                    # No data corruption.
                    if ack_seg[4] & 0x4 == 0x4 and ack_seg[3] == ack_nums[win_base]:
                        # Received the proper ACK.
                        if self.debug:
                            print("Received ACK: " + str(ack_seg[3]))
                        signal.alarm(0)
                        self.sequence_num = self.sequence_num + len(segments[win_base]) - header_size()
                        segments_in_transit = segments_in_transit - 1
                        win_base = win_base + 1
                        attempt_num = 1

                        # While space in window, send another segment.
                        while next_seg < len(segments) and segments_in_transit + 1 <= self.window_size:
                            self.s.sendto(segments[next_seg], (self.destination_IP, self.destination_port))
                            segments_in_transit = segments_in_transit + 1
                            next_seg = next_seg + 1
                elif self.debug:
                    print("Packet was corrupted.")

            except TimeoutError:
                signal.alarm(0)

                if self.debug:
                    print("ACK NOT RECEIVED TIMED OUT - segments_length: " + str(len(segments)) + ", win_base: " + str(win_base) + ", next_seg: " + str(next_seg))
                attempt_num = attempt_num + 1
                if attempt_num > MAX_NUM_ATTEMPTS:
                    return

                # Retransmit window.
                for i in range(win_base, next_seg):
                    if i < len(segments):
                        self.s.sendto(segments[i], (self.destination_IP, self.destination_port))

            except:
                 print("Unexpected error: " + str(sys.exc_info()[0]))

    def timeout(self, signal_num, stack_frame):
        raise TimeoutError("Timeout. Connection seems to be lost.")

    def recv(self, data_size):

        data = bytearray()

        if self.first_data_segment != None:
            # Didn't receive an ACK; received a data segment which was the ACK.
            if self.first_data_segment[2] == self.ack_num:
                data.extend(self.first_data_segment[8])
                self.ack_num += self.first_data_segment[7]
                self.s.sendto(create_segment(self.source_port, self.destination_port, self.sequence_num, self.ack_num, self.window_remaining, 0, b'', ack=True), self.get_destination())
                self.first_data_segment = None

        signal.signal(signal.SIGALRM, self.timeout)
        while len(data) < data_size:
            try:
                signal.alarm(TIMEOUT)
                segment = self.s.recv(max_safe_data_size() + header_size())
                signal.alarm(0)

                # Received the whole segment.
                segment = read_segment(segment)

                if segment != None and segment[2] == self.ack_num:
                    # Checksum matched and segment_num was expected.
                    # Place data into receive_buffer
                    segment_data_size = segment[7]
                    data.extend(segment[8])
                    self.ack_num += segment_data_size
                    self.s.sendto(create_segment(self.source_port, self.destination_port, self.sequence_num, self.ack_num, self.window_remaining, 0, b'', ack=True), self.get_destination())

            except:
                signal.alarm(0)
                return data
        return data

    def close(self):

        # Closes the connection
        # Releases resoures associated with connection

        if self.debug:
            print("Closing connection...")

        if self.destination_IP != None and self.destination_port != None:
            if self.debug:
                print("Send FIN packet")

        # Free buffers and reset variables.
        self.ack_num = 0
        self.debug = False
        self.destination_IP = ''
        self.destination_port = 0
        self.IPv6 = False
        self.listening = False
        self.sequence_num = 0
        self.source_port = 1111
        self.window_remaining = 0
        self.window_size = 0
        self.s.close()
        if self.is_conn:
            rtp_socket.current_num_connections -= 1
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
        self.first_data_segment = con_info['first_data_segment']
        self.is_conn = True

        self.s.connect((self.destination_IP, self.destination_port))
        self.s = con_info['socket']

        if con_info['first_data_segment'] != None:
            if self.debug:
                print("Server got data for first data segment instead of ACK.")