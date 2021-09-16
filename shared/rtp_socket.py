from shared.rtp_lib import *
import math
import random
import signal
import socket
import sys

# Connection constants.
TIMEOUT         = 1     # Seconds before timeout.
MAX_ATTEMPTS    = 3     # Before failed to send/receive in connection.
MAX_CONNECTIONS = 1     # Before refusing connections.

class rtp_socket:
    connection_count = 0

    # Creates a UDP socket and initializes connection variables.
    def __init__(self, IPv6=False, debug=False):

        # Create UDP socket.
        if IPv6:
            self.s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        else:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.source_port = random.randint(1024, 65535)
        self.destination_port = None
        self.sequence_num = 0
        self.ack_num = 0

        self.buffer_size = INITIAL_BUFFER_SIZE
        self.window_size = INITIAL_WINDOW_SIZE
        self.buffer_remaining = INITIAL_BUFFER_SIZE
        self.window_remaining = INITIAL_WINDOW_SIZE

        self.debug = debug
        self.destination_IP = None
        self.listening = False
        self.IPv6 = IPv6

        self.first_data_segment = None
        self.connected_to_client = False

    def set_window_size(self, n):
        """Updates the window size to at most n segments of data."""
        if n <= 0:
            raise ValueError("Window size must be > 0")
        self.window_size = n
        self.buffer_size = n * MAX_DATA_PER_SEGMENT

    def set_buffer_size(self, n):
        """Updates the buffer size to at most n bytes of data."""
        if n <= HEADER_SIZE:
            raise ValueError(f"Buffer size must be greater than the header size ({HEADER_SIZE})")
        self.buffer_size = n
        self.window_size = math.ceil(n / MAX_SAFE_UDP_SIZE)

    def close(self):

        # Closes the connection
        # Releases resoures associated with connection

        if self.debug:
            print("Closing connection...")

        if self.destination_IP != None and self.destination_port != None:
            if self.debug:
                print("Send FIN packet")

        # Free buffers and reset variables.
        # self.ack_num = 0
        # self.debug = False
        # self.destination_IP = ''
        # self.destination_port = 0
        # self.IPv6 = False
        # self.listening = False
        # self.sequence_num = 0
        # self.source_port = 1111
        # self.window_remaining = 0
        # self.window_size = 0
        # self.s.close()
        if self.debug:
            print("Connection closed!")


    def bind(self, info):
        """Server: Binds UDP socket to (IP, port)."""
        self.s.bind(info)
        self.source_port = info[1]

    def listen(self, max_connections=MAX_CONNECTIONS):
        """Server: Sets RTP socket to listen for connections."""
        self.listening = True
        self.max_connections = max_connections

    def accept(self):
        """Server: Accepts a connection."""

        if not self.listening:
            raise ConnectionRefusedError("Socket not listening for connections.")

        if rtp_socket.connection_count >= self.max_connections:
            raise ConnectionRefusedError("All connections full.")

        if self.debug:
            print("Accepting connections! Waiting for client SYNs...")

        # Wait for SYN segment.
        while True:
            buffer, client_address = self.s.recvfrom(self.buffer_size)
            buffer = read_segment(buffer)

            if buffer is not None and buffer[4] & 0x2 == 0x2:
                break
            elif self.debug:
                print("Received a packet that was not SYN or was corrupted")

        if self.debug:
            print("Received SYN! Sending SYN/ACK, waiting for an ACK...")

        # On SYN received:
        con_sock_info = {}
        con_sock_info['opp_host_window'] = buffer[5]
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
        signal.signal(signal.SIGALRM, self.timeout)

        while not response_received:
            try:
                self.s.sendto(synack_seg, (client_address[0], client_address[1]))
                signal.alarm(TIMEOUT)
                ack_seg = read_segment(self.s.recvfrom(MAX_DATA_PER_SEGMENT + HEADER_SIZE)[0])
                signal.alarm(0)
                if ack_seg != None:
                    response_received = True
            except TimeoutError:
                signal.alarm(0)
                attempt_num = attempt_num + 1

            if attempt_num > MAX_ATTEMPTS:
                raise TimeoutError("Could not reach client destination: " + str(client_address[0]) + ":" + str(client_address[1]))

        # On ACK received:
        if self.debug:
            print("Received the ACK! Connection established.")

        if ack_seg[4] & 0x4 != 0x4:
            con_sock_info['first_data_segment'] = read_segment(ack_seg)

        # Create connection socket.
        con_sock_info['socket'] = self.s.dup()
        conn = rtp_socket(IPv6=self.IPv6, debug=self.debug)
        conn.set_connection_info(con_sock_info)

        # Connection established.
        rtp_socket.connection_count += 1
        return (conn, client_address)

    # Server: Initializes variables for a new server connection.
    def from_connection_info(info, debug):

        s = rtp_socket(IPv6=info['IPv6'], debug=debug)
        s.set_buffer_size(info['buffer_size'])
        s.ack_num = info['ack_num']
        s.sequence_num = info['seq_num']
        s.destination_IP = info['destination_IP']
        s.destination_port = info['destination_port']
        s.first_data_segment = info['first_data_segment']
        s.connected_to_client = True
        s.s.connect((s.destination_IP, s.destination_port))
        self.s = con_info['socket']

        if con_info['first_data_segment'] != None:
            if self.debug:
                print("Server got data for first data segment instead of ACK.")

    # Server: Initializes variables for a new server connection.
    def set_connection_info(self, con_info):
        self.window_size = con_info['opp_host_window']
        self.ack_num = con_info['ack_num']
        self.sequence_num = con_info['seq_num']
        self.destination_IP = con_info['destination_IP']
        self.destination_port = con_info['destination_port']
        self.first_data_segment = con_info['first_data_segment']
        self.connected_to_client = True

        self.s.connect((self.destination_IP, self.destination_port))
        self.s = con_info['socket']

        if con_info['first_data_segment'] != None:
            if self.debug:
                print("Server got data for first data segment instead of ACK.")


    # ------------------------------------------
    # CLIENT
    # ------------------------------------------


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
        signal.signal(signal.SIGALRM, self.timeout)
        while not response_received:
            try:
                self.s.sendto(syn_seg, (self.destination_IP, self.destination_port))
                signal.alarm(TIMEOUT)
                synack_seg = read_segment(self.s.recvfrom(BUFFER_SIZE)[0])
                signal.alarm(0)
                if synack_seg != None and synack_seg[4] & 0x6 == 0x6:
                    response_received = True
            except socket.timeout:
                signal.alarm(0)
                attempt_num = attempt_num + 1

            if attempt_num > MAX_ATTEMPTS:
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
        segment_data_size = MAX_DATA_PER_SEGMENT if MAX_DATA_PER_SEGMENT <= self.window_size else self.window_size
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
                ack_seg = self.s.recv(HEADER_SIZE)
                ack_seg = read_segment(ack_seg)

                if ack_seg != None:

                    # No data corruption.
                    if ack_seg[4] & 0x4 == 0x4 and ack_seg[3] == ack_nums[win_base]:
                        # Received the proper ACK.
                        if self.debug:
                            print("Received ACK: " + str(ack_seg[3]))
                        signal.alarm(0)
                        self.sequence_num = self.sequence_num + len(segments[win_base]) - HEADER_SIZE
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
                if attempt_num > MAX_ATTEMPTS:
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
        if self.debug:
            print("Attempting to receive data")

        if self.first_data_segment != None:
            # Didn't receive an ACK; received a data segment which was the ACK.
            if self.first_data_segment[2] == self.ack_num:
                data.extend(self.first_data_segment[8])
                self.ack_num += self.first_data_segment[7]
                self.s.sendto(
                    create_segment(
                        self.source_port,
                        self.destination_port,
                        self.sequence_num,
                        self.ack_num,
                        self.window_remaining,
                        0,
                        b'',
                        ack=True),
                    (self.destination_IP, self.destination_port))
                self.first_data_segment = None

        received_something = False
        while not received_something:
            try:
                segment = self.s.recv(MAX_DATA_PER_SEGMENT + HEADER_SIZE)
                # Received the whole segment.
                segment = read_segment(segment)
                if segment != None and segment[2] == self.ack_num:
                    # Checksum matched and segment_num was expected.
                    # Place data into receive_buffer
                    segment_data_size = segment[7]
                    data.extend(segment[8])
                    self.ack_num += segment_data_size
                    self.s.sendto(
                        create_segment(
                            self.source_port,
                            self.destination_port,
                            self.sequence_num,
                            self.ack_num,
                            self.window_remaining,
                            0,
                            b'',
                            ack=True),
                            (self.destination_IP, self.destination_port))
                    received_something = True
            except:
                print('Error occurred in rtp_socket.recv')
        return data
