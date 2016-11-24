import rtp_socket

sock = rtp_socket.rtp_socket(debug=True)
sock.bind(('127.0.1.1', 8080))
sock.listen()

# while 1:
data = b''
conn, addr = sock.accept()
try:
	data = conn.recv(566799)
	conn.close(parent_socket=sock)
except:
	conn.close()
sock.close()

print("Received " + str(len(data)) + " bytes")
