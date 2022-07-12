NAME:		Siddarth Senthilkumar
NAME:		Ashika Ganesh
EMAIL:		ssenthilkumar3@gatech.edu
EMAIL:		ashika789@gmail.com
CLASS:		CS3251 - Networking I
SECTION:	A
DATE:		11/24/16
ASSIGNMENT:	Sockets Programming Assignment 2 - Reliable Transport Protocol Implementation & FTA

Files:
shared/rtp_socket.py - Contains all reliable transport protocol implementation code.
shared/rtp_lib.py    - Contains helper functions for rtp_socket.py
shared/fta_lib.py    - Contains helper functions for FTA-client.py and FTA-server.py
client/FTA-server.py - Contains File Transfer Application Server code.
server/FTA-client.py - Contains File Transfer Application Client code. 

EVERYTHING MUST BE RUN USING PYTHON3
=================================================================
HOW TO RUN A CLIENT
=================================================================
These commands should be executed in terminal.
Notes:
	-d denotes enabling debug mode.
	   This flag can only be put after IP and port number if IP and port number are entered.
	
	-r use real TCP instead of RTP

------------------------------
1) To specify an IP and Port:
------------------------------
python3 FTA-client.py <IP_address> <port_num>

If no IP and port are specified, the default is 127.0.0.1:8080

-----------
2) Example
-----------
python3 FTA-client.py 127.0.0.1 8080 -d

=================================================================
HOW TO RUN A CLIENT
=================================================================
These commands should be executed in terminal.
Notes:
	-d denotes enabling debug mode.
	   This flag can only be put after port number if port number is entered.

	-r use real TCP instead of RTP

----------------------
1) To specify a Port:
----------------------
python3 FTA-server.py <port_num>

If no port is specified, the default is 8080

-----------
2) Example
-----------
python3 FTA-server.py 8080 -d

=================================================================
FEATURES
=================================================================
- Both GET and POST supported

=================================================================
KNOWN BUGS AND ISSUES
=================================================================

1) SEQ and ACK numbers don't wrap around, so the connection can service at most pow(2, 32) - 1 bytes.

2) If clients terminate ungracefully, the server still holds the connection.
