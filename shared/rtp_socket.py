from shared.rtp_lib import *
from enum import Enum
import logging
import math
import random
import signal
import socket
import sys
import threading
import time

# Connection constants.
TIMEOUT         = 1     # Seconds before timeout.
MAX_ATTEMPTS    = 3     # Before failed to send/receive in connection.
MAX_CONNECTIONS = 3     # Before refusing connections.

# Logging setup.
_logger = logging.getLogger(__name__)

class rtp_socket:

    class connection_state(Enum):
        UNINITIALIZED = 0
        BOUND = 1
        SENT_SYN = 2
        SENT_SYNACK = 3
        CONNECTED = 4

    class socket_type(Enum):
        UNINITIALIZED = 0
        LISTENING = 1
        CONNECTION = 2

    def __init__(self, IPv6=False):
        """Creates a virtual TCP socket ready to be used as a client or server."""

        # Create underlying UDP socket and buffers.
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.init_buffers()

        # Connection state
        self.src_ip = None
        self.src_port = None
        self.dest_ip = None
        self.dest_port = None
        self.seq_num = 0
        self.ack_num = 0
        self.state = rtp_socket.connection_state.UNINITIALIZED
        self.type = rtp_socket.socket_type.UNINITIALIZED

        # Server state
        self.max_connections = MAX_CONNECTIONS
        self.listening_thread = None
        self.connections = {}
        self.connections_queue = []
        self.connections_cond = threading.Condition()

    def __init__(self, udp_socket, src_ip, src_port, dest_ip, dest_port):
        """Creates a virtual TCP socket connected to a remote host."""

        # Create underlying UDP socket and buffers.
        self.s = udp_socket
        self.init_buffers()

        # Connection state.
        self.src_ip = src_ip
        self.src_port = src_port
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.seq_num = 1
        self.ack_num = 1
        self.state = rtp_socket.connection_state.SENT_SYNACK
        self.type = rtp_socket.socket_type.CONNECTION

        # Send the SYNACK
        synack_seg = create_segment(
            self.src_port,
            self.dest_port,
            seq_num=0,
            ack_num=1,
            window_remaining=INITIAL_WINDOW_SIZE,
            data_size=0,
            data=bytearray([]),
            syn=True,
            ack=True)

        # TODO: Create a thread with timeouts to handle retries
        self.s.sendall(synack_seg, (self.dest_ip, self.dest_port))

    def init_buffers(self):
        """Initializes connection buffers and windows."""
        self.buffer_remaining = INITIAL_BUFFER_SIZE
        self.window_remaining = INITIAL_WINDOW_SIZE

        self.application_rcv_buffer = bytearray([])
        self.segment_rcv_buffer = {}
        self.segment_send_buffer = []

    def close(self):
        """Closes the connection."""

        # TODO: Releases resoures associated with connection
        _logger.info("Closing connection...")

        if self.dest_ip != None and self.dest_port != None:
            _logger.info("Send FIN packet")

        # Server socket cleanup - careful; these might get called after every client exits!
        # self.listening_thread = None
        # self.connection_queue = []

        # Free buffers and reset variables.
        # self.ack_num = 0
        # self.dest_ip = ''
        # self.dest_port = 0
        # self.IPv6 = False
        # self.seq_num = 0
        # self.src_port = 1111
        # self.window_remaining = 0
        # self.window_size = 0
        # self.s.close()
        _logger.info("Connection closed!")

    def check_valid_server_socket(self, should_be_unbound=True, should_be_listening=False):
        """Validates socket is allowed to listen or accept connections."""
        if should_be_unbound and self.src_port != None:
            raise ConnectionRefusedError("Socket cannot be rebound")
        if not should_be_listening and self.listening_thread is not None:
            raise ConnectionRefusedError("Socket already listening")
        if should_be_listening and self.listening_thread is None:
            raise ConnectionRefusedError("Socket not yet listening")

    def bind(self, dest_info):
        """Server: Binds UDP socket to given tuple (IP, port)."""
        self.check_valid_server_socket()
        self.s.bind(dest_info)
        self.src_ip = dest_info[0]
        self.src_port = dest_info[1]
        self.state = rtp_socket.connection_state.BOUND
        _logger.info(f"Bound to: {dest_info}")

    def listen(self, max_connections=MAX_CONNECTIONS):
        """Server: Sets RTP socket to listen for connections."""
        self.check_valid_server_socket(should_be_unbound=False)
        self.max_connections = max_connections
        self.listening_thread = threading.Thread(target=self.buffer_incoming_server_data, args=(self), daemon=True)
        self.listening_thread.start()
        self.type = rtp_socket.socket_type.LISTENING
        _logger.info(f"Max connections set to {max_connections} and listening thread started")

    def accept(self):
        """Server: Accepts a new connection."""
        self.check_valid_server_socket(should_be_unbound=False, should_be_listening=True)
        with self.connections_cond:
            while len(self.connections_queue) <= 0:
                self.connections_cond.wait()
            return self.connections_queue.pop(0)

    def buffer_incoming_server_data(self):
        """Server: Thread that listens for segments sent to the server port."""
        _logger.info("Listening for data...")
        while True:
            buffer, client_addr = self.s.recvfrom(MAX_RTP_SEGMENT_SIZE)
            _logger.info(f"Received data from: {client_addr}")

            # The underlying UDP socket would discard incomplete UDP datagrams,
            # and RTP fits the full segment in a single datagram,
            # so we can be sure that a full RTP segment was received.
            segment = read_segment(buffer)
            if segment is None:
                _logger.info("Received a corrupted packet. Segment dropped.")
                continue

            if client_addr not in self.connections:
                _logger.info("Client address unknown")

                if len(self.connections) >= self.max_connections:
                    _logger.info("All connections full. Segment dropped.")
                    continue

                if segment.special_bits & 0x2 == 0x2:
                    _logger.info("New connection didn't send SYN. Segment dropped.")
                    continue

                if segment.seq_num == 0:
                    _logger.info("New connection didn't have sequence number 0. Segment dropped.")
                    continue

                # Start a thread which keeps trying to send SYN/ACK until acknowledged.
                _logger.info(f"Received SYN from {client_addr}; responding with SYN/ACK")
                con = rtp_socket(self.s, self.src_ip, self.src_port, client_addr[0], client_addr[1])

                with self.connections_cond:
                    self.connections[client_addr] = con
                    self.connections_queue.append((con, client_addr))
                    self.connections_cond.notify()
            else:
                if segment.special_bits & 0x4 != 0x4:
                    _logger.info("Received response segment without ACK flag. Segment dropped.")
                    continue

                # Send data to appropriate connection
                con = self.connections[client_addr]
                con.buffer_segment(segment)

    def buffer_segment(self, segment: Segment):
        """Server: Buffers a segment, and if possible, flushes the segment buffer to the application data buffer.
        Normally the application data would be returned immediately to the app, but since the app is not waiting on this
        thread, we have to buffer it and have the waiting thread pick up on it."""

        # TODO: Lock access to buffers
        if self.ack_num == segment.seq_num:
            self.application_rcv_buffer.extend(segment.data)
            self.ack_num += segment.data_size
            _logger.info(f"{segment.data_size} bytes of app data received and buffered")

            # Iterate through segment buffer for next seq num packet, if exists
            while True:
                wanted_seq_num = self.ack_num
                if wanted_seq_num not in self.segment_rcv_buffer:
                    _logger.info("No other buffered segments ready")
                    break

                segment = self.segment_recv_buffer[wanted_seq_num]
                self.application_rcv_buffer.extend(segment.data)
                self.ack_num += segment.data_size
                self.buffer_remaining += segment.data_size + HEADER_SIZE
                _logger.info(f"{segment.data_size} bytes of app data received and buffered")
                del(self.segment_recv_buffer[wanted_seq_num])
                # TODO: send signal to recv, which can check if new data is present

        else:
            _logger.info(f"Received seq num: {segment.seq_num} but expected {self.ack_num}.")
            if self.buffer_remaining < segment.data_size + HEADER_SIZE:
                _logger.info("Too much unexpected data buffered. Dropping segment.")
                return
            
            if segment.seq_num in self.segment_rcv_buffer:
                _logger.info("Already buffered this segment. Dropping segment.")
                return

            self.buffer_remaining -= segment.data_size + HEADER_SIZE
            self.segment_rcv_buffer[segment.seq_num] = segment
            _logger.info("Buffered segment")

        # this might need to happen  in a separate thread
        #
        self.s.sendto(
            create_segment(
                self.src_port,
                self.dest_port,
                self.seq_num,
                self.ack_num,
                self.window_remaining, # what is this
                0,
                b'',
                ack=True),
                (self.dest_ip, self.dest_port))
        _logger.info("Sent ACK segment")

    # ------------------------------------------
    # CLIENT
    # ------------------------------------------


    # Client: Perform 3-way handshake and set up buffers.
    def connect(self, destination):

        _logger.info("Initiating a connection...")

        self.src_port = random.randint(1024, 65535)

        # Set destination information.
        self.dest_ip = destination[0]
        self.dest_port = destination[1]

        # Set segment variables.
        data_size = 0
        data = bytearray([])

        # Create a SYN segment.
        syn_seg = create_segment(self.src_port, self.dest_port, self.seq_num, self.ack_num, self.window_remaining, data_size, data, syn=True)

        # Send SYN and wait for SYN/ACK.
        _logger.info("Sending a SYN...")

        response_received = False
        attempt_num = 1
        synack_seg = b''
        signal.signal(signal.SIGALRM, self.timeout)
        while not response_received:
            try:
                self.s.sendto(syn_seg, (self.dest_ip, self.dest_port))
                signal.alarm(TIMEOUT)
                synack_seg = read_segment(self.s.recvfrom(BUFFER_SIZE)[0])
                signal.alarm(0)
                if synack_seg != None and synack_seg[4] & 0x6 == 0x6:
                    response_received = True
            except socket.timeout:
                signal.alarm(0)
                attempt_num = attempt_num + 1

            if attempt_num > MAX_ATTEMPTS:
                raise TimeoutError("Could not reach server destination: " + self.dest_ip + ":" + str(self.dest_port))

        # TODO: Parse synack_seg
        self.opp_host_window = synack_seg[5]

        _logger.info("Received the SYN/ACK, sending an ACK...")

        # Create and send the ACK segment.
        self.seq_num = self.seq_num + 1
        self.ack_num = self.ack_num + 1

        ack_seg = create_segment(self.src_port, self.dest_port, self.seq_num, self.ack_num, self.window_remaining, data_size, data, ack=True)
        self.s.sendto(ack_seg, (self.dest_ip, self.dest_port))

        _logger.info("ACK sent. Connection established!")

    def sendall(self, data):

        # data = bytearray(data)

        # Sends data through connection
        t = threading.Thread(target=self.send_data, args=(self, data), daemon=True)

        _logger.info("Sent_data finished execution.")
        self.s.sendto(segment, (self.dest_ip, self.dest_port))

    # Send all the bytes of data.
    def send_data(self, data):

        num_bytes = len(data)

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
                segments[i] = create_segment(self.src_port, self.dest_port, self.seq_num + byte_num, self.ack_num, self.window_remaining, segment_data_size, data[byte_num:byte_num + segment_data_size])
                byte_num = byte_num + segment_data_size
                ack_nums[i] = self.seq_num + byte_num

        if num_bytes % segment_data_size != 0:
            segments[len(segments) - 1] = create_segment(self.src_port, self.dest_port, self.seq_num + byte_num, self.ack_num, self.window_remaining, num_bytes % segment_data_size, data[byte_num:byte_num + num_bytes % segment_data_size])
            byte_num = byte_num + num_bytes % segment_data_size
            ack_nums[len(segments) - 1] = self.seq_num + byte_num
        else:
            segments[len(segments) - 1] = create_segment(self.src_port, self.dest_port, self.seq_num + byte_num, self.ack_num, self.window_remaining, segment_data_size, data[byte_num:byte_num + segment_data_size])
            byte_num = byte_num + segment_data_size
            ack_nums[len(segments) - 1] = self.seq_num + byte_num

        # 2. Send initial segments.
        while next_seg < len(segments) and segments_in_transit + 1 <= self.window_size:

            self.s.sendto(segments[next_seg], (self.dest_ip, self.dest_port))
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
                        _logger.info("Received ACK: " + str(ack_seg[3]))
                        signal.alarm(0)
                        self.seq_num = self.seq_num + len(segments[win_base]) - HEADER_SIZE
                        segments_in_transit = segments_in_transit - 1
                        win_base = win_base + 1
                        attempt_num = 1

                        # While space in window, send another segment.
                        while next_seg < len(segments) and segments_in_transit + 1 <= self.window_size:
                            self.s.sendto(segments[next_seg], (self.dest_ip, self.dest_port))
                            segments_in_transit = segments_in_transit + 1
                            next_seg = next_seg + 1
                else:
                    _logger.info("Packet was corrupted.")

            except TimeoutError:
                signal.alarm(0)

                _logger.info("ACK NOT RECEIVED TIMED OUT - segments_length: " + str(len(segments)) + ", win_base: " + str(win_base) + ", next_seg: " + str(next_seg))
                attempt_num = attempt_num + 1
                if attempt_num > MAX_ATTEMPTS:
                    return

                # Retransmit window.
                for i in range(win_base, next_seg):
                    if i < len(segments):
                        self.s.sendto(segments[i], (self.dest_ip, self.dest_port))

            except:
                 _logger.info("Unexpected error: " + str(sys.exc_info()[0]))

    def timeout(self, signal_num, stack_frame):
        raise TimeoutError("Timeout. Connection seems to be lost.")

    def recv(self, data_size):

        data = bytearray()
        _logger.info("Attempting to receive data")

        if self.first_data_segment != None:
            # Didn't receive an ACK; received a data segment which was the ACK.
            if self.first_data_segment[2] == self.ack_num:
                data.extend(self.first_data_segment[8])
                self.ack_num += self.first_data_segment[7]
                self.s.sendto(
                    create_segment(
                        self.src_port,
                        self.dest_port,
                        self.seq_num,
                        self.ack_num,
                        self.window_remaining,
                        0,
                        b'',
                        ack=True),
                    (self.dest_ip, self.dest_port))
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
                            self.src_port,
                            self.dest_port,
                            self.seq_num,
                            self.ack_num,
                            self.window_remaining,
                            0,
                            b'',
                            ack=True),
                            (self.dest_ip, self.dest_port))
                    received_something = True
            except:
                _logger.info('Error occurred in rtp_socket.recv')
        return data
