import rtp_socket

with open("huckfinn.txt", "rb") as f:
	data = f.read()

# data = b'hello world'
sock = rtp_socket.rtp_socket(debug=True)
# sock.bind(('127.0.1.1', 11223))
sock.connect(('127.0.1.1', 8080))
print(sock.s.getsockname())
sock.sendall(data)
sock.close()