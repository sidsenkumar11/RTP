import rtp_socket

sock = rtp_socket.rtp_socket(debug=True)
sock.connect(('127.0.1.1', 8080))
sock.close()