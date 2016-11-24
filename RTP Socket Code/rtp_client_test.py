import rtp_socket

with open("huckfinn.txt", "rb") as f:
	data = f.read()

sock = rtp_socket.rtp_socket(debug=True)
sock2 = rtp_socket.rtp_socket(debug=True)
sock.connect(('127.0.1.1', 8080))
sock2.connect(('127.0.1.1', 8080))
sock.sendall(data)
sock2.sendall(data)
sock.close()
sock2.close()