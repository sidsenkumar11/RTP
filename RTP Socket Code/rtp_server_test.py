import rtp_socket

sock = rtp_socket.rtp_socket(debug=True)
sock.bind(('', 8080))
sock.listen()

# while 1:
conn, addr = sock.accept()
# data = conn.recv(BUFFER_SIZE)
conn.close(parent_socket=sock)

sock.close()