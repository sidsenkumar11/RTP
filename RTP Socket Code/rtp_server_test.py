import rtp_socket

sock = rtp_socket.rtp_socket(debug=True)
sock.bind(('127.0.1.1', 8080))
sock.listen()

while 1:
	data = b''
	conn, addr = sock.accept()
	conn2, addr2 = sock.accept()

	try:
		data = conn.recv(600000)
		conn.close()
	except:
		conn.close()

	print("Got all of data from sock1: " + str(len(data)))
	try:
		data2 = conn2.recv(40)
		conn2.close()
	except:
		conn2.close()
	print("Got all of data from sock2: " + str(len(data2)))

sock.close()

print("Received " + str(len(data)) + " bytes")
