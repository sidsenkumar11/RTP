import rtp_socket

sock = rtp_socket.rtp_socket(debug=True)
sock.bind(('127.0.1.1', 8080))
sock.listen()

# while 1:
conn, addr = sock.accept()
data = conn.recv(11)
conn.close(parent_socket=sock)
print("Received Data: " + str(data))

sock.close()