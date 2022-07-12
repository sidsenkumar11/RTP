import logging
import math
import random
import select
import socket
import threading
import time
from enum import Enum

from shared.rtp_lib import (
    DEFAULT_WINDOW_SIZE,
    MAX_DATA_PER_SEGMENT,
    MAX_RTP_SEGMENT_SIZE,
    Segment,
    create_segment,
    read_segment,
)

# Connection constants.
SEND_ACK_TIMEOUT = 10  # Seconds before send() times out due to not receiving ACKs.
RECV_TIMEOUT = 0.5  # Seconds before recv() times out
BUFFERING_THREAD_TIMEOUT = 4  # Seconds before the buffering thread wakes up to check if it should die
HANDSHAKE_TIMEOUT = 3
MAX_ATTEMPTS = 3  # Before failed to send/receive in connection
MAX_CONNECTIONS = 3  # Before refusing connections

# Logging setup.
_logger = logging.getLogger(__name__)


class rtp_socket:
    class socket_type(Enum):
        UNINITIALIZED = 0
        LISTENING = 1
        CONNECTION = 2

    def __init__(self, window_size=DEFAULT_WINDOW_SIZE):
        """Creates a virtual TCP socket ready to be used as a client or server."""

        # Create underlying UDP socket and buffers.
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.window_size = window_size
        self.appdata_recv_buffer = bytearray([])

        # Connection state
        self.src_ip = None
        self.src_port = None
        self.dest_ip = None
        self.dest_port = None
        self.seq_num = 0
        self.ack_num = 0
        self.last_ack_received = 0
        self.type = rtp_socket.socket_type.UNINITIALIZED
        self.appdata_cond = threading.Condition()
        self.recv_ack_cond = threading.Condition()
        self.buffering_thread = None

        # Server state
        self.max_connections = MAX_CONNECTIONS
        self.connections: dict[(str, int), rtp_socket] = {}
        self.connections_queue = []
        self.connections_cond = threading.Condition()
        self.syned_clients = set()
        self.syned_clients_lock = threading.Lock()

    def _init_connection(self, udp_socket, src_ip, src_port, dest_ip, dest_port, window_size):
        """Creates a virtual TCP socket connected to a remote host. This should NOT be called by users; it is only intended for internal use. Listening server sockets will use this to construct new connection sockets. So, this socket will not have an active listening thread as data will be sent by the listening server socket when it calls `_buffer_segment` in this socket."""

        # Create underlying UDP socket and buffers.
        self.s = udp_socket
        self.window_size = window_size
        self.appdata_recv_buffer = bytearray([])

        # Connection state.
        self.src_ip = src_ip
        self.src_port = src_port
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.seq_num = 0
        self.ack_num = 0
        self.last_ack_received = 0
        self.type = rtp_socket.socket_type.CONNECTION
        self.appdata_cond = threading.Condition()
        self.recv_ack_cond = threading.Condition()
        self.buffering_thread = None

    def close(self):
        """Closes the socket and/or connection."""

        if self.type == rtp_socket.socket_type.UNINITIALIZED:
            return

        # TODO: Releases resoures associated with connection
        _logger.info("Closing connection...")

        if self.dest_ip != None and self.dest_port != None:
            _logger.info("Send FIN packet")

        # Close any listening threads
        # self.buffering_thread = None
        # self.appdata_recv_buffer = bytearray([])

        # Server socket cleanup - careful; these might get called after every client exits!
        # self.connection_queue = []
        # self.connections = {}
        # self.syned_clients = set()

        # Free buffers and reset variables.
        # self.ack_num = 0
        # self.src_ip = ''
        # self.src_port = 0
        # self.dest_ip = ''
        # self.dest_port = 0
        # self.seq_num = 0
        # self.ack_num = 0
        # self.last_ack_received = 0
        # self.type = rtp_socket.socket_type.UNINITIALIZED
        # self.window_size = 0
        _logger.info("Connection closed!")

    # ------------------------------------------
    # SERVER
    # ------------------------------------------

    def check_valid_server_socket(self, should_be_unbound=True, should_be_listening=False):
        """Validates socket is allowed to listen or accept connections."""
        if should_be_unbound and self.src_port != None:
            raise ConnectionRefusedError("Socket cannot be rebound")
        if not should_be_listening and self.type == rtp_socket.socket_type.LISTENING:
            raise ConnectionRefusedError("Socket already listening")
        if should_be_listening and self.type != rtp_socket.socket_type.LISTENING:
            raise ConnectionRefusedError("Socket not yet listening")

    def bind(self, dest_info):
        """Server: Binds UDP socket to given tuple (IP, port)."""
        self.check_valid_server_socket()
        self.s.bind(dest_info)
        self.src_ip = dest_info[0]
        self.src_port = dest_info[1]
        _logger.info(f"Bound to: {dest_info}")

    def listen(self, max_connections=MAX_CONNECTIONS):
        """Server: Sets RTP socket to listen for connections."""
        self.check_valid_server_socket(should_be_unbound=False)
        self.max_connections = max_connections
        self.buffering_thread = threading.Thread(target=self._buffer_incoming_server_data, args=(), daemon=True)
        self.buffering_thread.start()
        self.type = rtp_socket.socket_type.LISTENING
        _logger.info(f"Max connections set to {max_connections} and listening thread started")

    def accept(self):
        """Server: Accepts a new connection."""
        self.check_valid_server_socket(should_be_unbound=False, should_be_listening=True)
        with self.connections_cond:
            self.connections_cond.wait_for(lambda: len(self.connections_queue) > 0)
            client_addr = self.connections_queue.pop(0)
            return self.connections[client_addr], client_addr

    def _buffer_incoming_server_data(self):
        """Server: Thread that listens for segments sent to the server port."""
        _logger.info("Listening for data...")
        while self.buffering_thread:

            ready = select.select([self.s], [], [], BUFFERING_THREAD_TIMEOUT)
            if ready[0]:
                buffer, client_addr = self.s.recvfrom(MAX_RTP_SEGMENT_SIZE)
                _logger.info(f"Received segment from: {client_addr}")
            else:
                continue

            # The underlying UDP socket would discard incomplete UDP datagrams,
            # and RTP fits the full segment in a single datagram,
            # so we can be sure that a full RTP segment was received.
            segment = read_segment(buffer)
            if segment is None:
                _logger.info("Received a corrupted packet. Segment dropped.")
                continue

            if client_addr in self.connections:
                # TODO: Not sure if client needs this flag when closing connections
                # Send data to appropriate connection
                _logger.info("Buffering data for known client")
                con = self.connections[client_addr]
                con._buffer_segment(segment, client_addr)
                continue

            # TODO: Lock syned_clients usage
            if client_addr in self.syned_clients:
                # TODO: Not sure if client needs this flag when closing connections
                _logger.info("Client address is one that recently SYNed the server.")
                if segment.special_bits != 0x4:
                    _logger.info("Received response to SYN/ACK segment without only ACK flag. Segment dropped.")
                    continue

                _logger.info(f"Received ACK from {client_addr}. Connection established!")
                con = rtp_socket(window_size=segment.window)
                con._init_connection(
                    self.s, self.src_ip, self.src_port, client_addr[0], client_addr[1], self.window_size
                )
                self.syned_clients.remove(client_addr)

                # Notify the accept() thread that a new connection is available
                with self.connections_cond:
                    self.connections[client_addr] = con
                    self.connections_queue.append(client_addr)
                    self.connections_cond.notify()
                continue

            else:
                _logger.info("Received SYN from new client")

                if len(self.connections) >= self.max_connections:
                    _logger.info("Reached max num connections. Segment dropped.")
                    continue

                if segment.special_bits & 0x2 != 0x2:
                    _logger.info("New connection didn't send SYN. Segment dropped.")
                    continue

                if segment.seq_num != 0:
                    _logger.info("New connection didn't have sequence number 0. Segment dropped.")
                    continue

                # Start a thread which keeps trying to send SYN/ACK until acknowledged.
                _logger.info(f"Received SYN from {client_addr}; sending SYN/ACK")
                self.syned_clients.add(client_addr)
                threading.Thread(target=self._complete_handshake, args=(client_addr,), daemon=True).start()

        _logger.info("Exiting buffering thread")

    def _complete_handshake(self, client_addr):
        """Server: This function should be run from a new thread upon receiving a client SYN. This function will send a SYN/ACK repeatedly until the client sends an ACK."""
        synack_seg = create_segment(
            self.src_port,
            client_addr[1],
            0,
            0,
            self.window_size,
            syn=True,
            ack=True,
        )

        for i in range(MAX_ATTEMPTS):
            if client_addr not in self.syned_clients:
                _logger.info(f"Handshake thread exited successfully; {client_addr} acknowledged SYN/ACK")
                return

            _logger.info(f"Handshake thread sending SYN/ACK. Attempt {i+1} for {client_addr}")
            self.s.sendto(synack_seg, client_addr)
            time.sleep(HANDSHAKE_TIMEOUT)

        _logger.info(
            f"Handshake thread for {client_addr} never received acknowledgement for SYN/ACK. Dropping SYNed segment"
        )

        with self.syned_clients_lock:
            self.syned_clients.remove(client_addr)

    # ------------------------------------------
    # CLIENT
    # ------------------------------------------

    def connect(self, dest_addr):
        """Client: Perform a 3-way handshake and set up client segment-receiver thread."""

        _logger.info("Initiating a connection...")

        # Bind to a random port.
        self.src_port = random.randint(1024, 65535)
        self.type = rtp_socket.socket_type.CONNECTION
        self.s.bind(("", self.src_port))

        # Set destination information.
        self.dest_ip = dest_addr[0]
        self.dest_port = dest_addr[1]

        # Send a SYN and wait for a SYN/ACK.
        self.seq_num = 0
        self.ack_num = 0
        syn_seg = create_segment(
            self.src_port,
            self.dest_port,
            self.seq_num,
            self.ack_num,
            self.window_size,
            syn=True,
        )

        _logger.info("Sending a SYN...")
        synack_seg = None
        for i in range(MAX_ATTEMPTS):
            self.s.sendto(syn_seg, (self.dest_ip, self.dest_port))
            ready = select.select([self.s], [], [], HANDSHAKE_TIMEOUT)
            if ready[0]:
                data, _ = self.s.recvfrom(MAX_RTP_SEGMENT_SIZE)
                synack_seg = read_segment(data)
                if synack_seg is not None and synack_seg[4] & 0x6 == 0x6:
                    break
                _logger.info("Invalid synack segment")
            else:
                _logger.info("Timed out waiting for SYN/ACK")
        else:
            raise TimeoutError(f"Could not reach server: {dest_addr}")

        # Start listening for data from the connection
        _logger.info("Received the SYN/ACK, sending an ACK...")
        self.buffering_thread = threading.Thread(target=self._buffer_incoming_client_data, args=(), daemon=True)
        self.buffering_thread.start()

        # Create and send the ACK segment.
        ack_seg = create_segment(
            self.src_port,
            self.dest_port,
            self.seq_num,
            self.ack_num,
            self.window_size,
            ack=True,
        )
        self.s.sendto(ack_seg, dest_addr)
        _logger.info("ACK sent. Connection established!")

    def _buffer_incoming_client_data(self):
        """Client: Thread that listens for segments sent to the client port."""
        _logger.info("Client incoming buffer thread started")
        while self.buffering_thread:
            ready = select.select([self.s], [], [], BUFFERING_THREAD_TIMEOUT)
            if ready[0]:
                buffer, client_addr = self.s.recvfrom(MAX_RTP_SEGMENT_SIZE)
                _logger.info(f"Received data from: {client_addr}")
            else:
                continue

            # The underlying UDP socket would discard incomplete UDP datagrams,
            # and RTP fits the full segment in a single datagram,
            # so we can be sure that a full RTP segment was received.
            segment = read_segment(buffer)
            if segment is None:
                _logger.info("Received a corrupted packet. Segment dropped.")
                continue

            self._buffer_segment(segment, client_addr)

    def sendall(self, data):
        """Client: Sends all the given data through the connection using GBN Sliding Window protocol."""

        if self.type != rtp_socket.socket_type.CONNECTION:
            raise ConnectionRefusedError("This socket cannot be used to send data!")

        # Split data into segments.
        # Pin the window size here in case we get a window update packet during the send.
        window_size = self.window_size
        num_bytes = len(data)
        segments: list[Segment] = [None] * math.ceil(float(num_bytes) / MAX_DATA_PER_SEGMENT)

        # Create all the "full" segments.
        # Note: ack_num and window_size will be ignored by the recipient.
        byte_num = 0
        if len(segments) > 1:
            for i in range(len(segments) - 1):
                segments[i] = create_segment(
                    self.src_port,
                    self.dest_port,
                    self.seq_num + byte_num,
                    self.ack_num,
                    window_size,
                    data[byte_num : byte_num + MAX_DATA_PER_SEGMENT],
                    ack=True,
                )
                byte_num += MAX_DATA_PER_SEGMENT

        # Create last segment, which might not be full.
        last_seg_bytes_to_send = num_bytes % MAX_DATA_PER_SEGMENT
        segments[len(segments) - 1] = create_segment(
            self.src_port,
            self.dest_port,
            self.seq_num + byte_num,
            self.ack_num,
            window_size,
            data[byte_num : byte_num + last_seg_bytes_to_send],
            ack=True,
        )
        byte_num += last_seg_bytes_to_send

        # Sliding window Go-Back-N (GBN).
        win_base = 0
        timed_out_count = 0
        _logger.info(f"Sending data in windows of {window_size} segments")
        while win_base < len(segments):

            if timed_out_count == MAX_ATTEMPTS:
                raise TimeoutError("The remote application is not acknowleding sent segments!")

            # Send window
            ack_num_waiting = -1
            segments_sent = 0
            bytes_sent = 0
            while win_base + segments_sent < len(segments) and segments_sent < window_size:
                seg_to_send = read_segment(segments[win_base + segments_sent])
                ack_num_waiting = seg_to_send.seq_num + seg_to_send.data_size
                self.s.sendto(segments[win_base + segments_sent], (self.dest_ip, self.dest_port))
                segments_sent += 1
                bytes_sent += seg_to_send.data_size

            # Wait for all sent data to get ACK'd, or timeout while waiting
            with self.recv_ack_cond:
                received_ack = self.recv_ack_cond.wait_for(
                    lambda: self.last_ack_received >= ack_num_waiting, SEND_ACK_TIMEOUT
                )
                if not received_ack:
                    timed_out_count += 1
                    _logger.info(f"Timed out waiting for ACKs: timed_out_count={timed_out_count}")
                    continue

            # We successfully received ACKs for all data; move onto next window
            timed_out_count = 0
            win_base += segments_sent
            self.seq_num += bytes_sent
            _logger.info(f"Successfully received ACKs. Window base now at {win_base}")

        _logger.info("Successfully sent all data!")

    def recv(self, data_size):
        if self.type != rtp_socket.socket_type.CONNECTION:
            raise ConnectionRefusedError("This socket cannot be used to send data!")

        _logger.info("Attempting to receive data")

        with self.appdata_cond:
            self.appdata_cond.wait_for(lambda: len(self.appdata_recv_buffer) >= data_size, RECV_TIMEOUT)
            data = self.appdata_recv_buffer[:data_size]
            self.appdata_recv_buffer = self.appdata_recv_buffer[data_size:]
            return data

    def set_window(self, window_size):
        _logger.info("Updating client's window_size and trying to ask server to update as well.")
        self.window_size = window_size
        window_seg = create_segment(
            self.src_port,
            self.dest_port,
            self.seq_num,
            self.ack_num,
            window_size,
            ack=True,
            win=True,
        )

        self.s.sendto(window_seg, (self.dest_ip, self.dest_port))

    # ------------------------------------------
    # SHARED
    # ------------------------------------------

    def _buffer_segment(self, segment: Segment, client_addr):
        """Server and Client: Buffers a segment and notifies any recv() threads that new app data is available or any send() threads that a new ACK is available."""

        # TODO: Client who wants to abruptly quit might not have ACK flag
        if segment.special_bits & 0x4 != 0x4:
            _logger.info("Received response segment without ACK flag. Segment dropped.")
            return

        if segment.data_size == 0:
            _logger.info("Received ACK segment with no data")

            # Check if this is a WIN segment to update the window.
            if segment.special_bits & 0x8 == 0x8:
                _logger.info("Received request to increase window size from client")
                self.window_size = segment.window

            # Check if this is an ACK segment for sent data.
            if segment.ack_num > self.last_ack_received:
                self.last_ack_received = segment.ack_num
                _logger.info(f"New ACK: {self.last_ack_received}")
                with self.recv_ack_cond:
                    self.recv_ack_cond.notify()
            else:
                _logger.info(
                    f"Ignoring ACK ({segment.ack_num}) as it is older than what we have ({self.last_ack_received})"
                )
            return

        # This is a data segment that should be buffered for the app and ACK'd.
        if self.ack_num == segment.seq_num:
            _logger.info("Waiting for appdata_cond")
            with self.appdata_cond:
                _logger.info("Received appdata_cond")
                self.appdata_recv_buffer.extend(segment.data)
                self.ack_num += segment.data_size
                _logger.info(f"{segment.data_size} bytes of app data received and buffered")

                # Send ACK. We don't need to retry sending it if it gets lost.
                # The sender will resend the segment and we'll resend the ACK.
                # Note: seq_num and window_size will be ignored by the recipient.
                self.s.sendto(
                    create_segment(
                        self.src_port,
                        client_addr[1],
                        self.seq_num,
                        self.ack_num,
                        self.window_size,
                        ack=True,
                    ),
                    client_addr,
                )

                _logger.info("Sent ACK segment")
                self.appdata_cond.notify()

        elif self.ack_num > segment.seq_num:
            _logger.info("Received old seq num that was already ACKed. Resending the ACK.")
            self.s.sendto(
                create_segment(
                    self.src_port,
                    client_addr[1],
                    self.seq_num,
                    self.ack_num,
                    self.window_size,
                    ack=True,
                ),
                client_addr,
            )

        else:
            _logger.info(
                f"Sender sent us seq_num > the last thing we ack'd. Ignoring the segment: segment.seq_num={segment.seq_num}, self.ack_num={self.ack_num}"
            )
