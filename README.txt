NAME:		Siddarth Senthilkumar
NAME:		Ashika Ganesh
EMAIL:		ssenthilkumar3@gatech.edu
EMAIL:		ashika789@gmail.com
CLASS:		CS3251 - Networking I
SECTION:	A
DATE:		11/24/16
ASSIGNMENT:	Sockets Programming Assignment 2 - Reliable Transport Protocol Implementation & FTA

Files:
rtp_socket.py		- Contains all reliable transport protocol implementation code.
rtp_lib.py			- Contains helper functions for rtp_socket.py. Must be in same directory as rtp_socket.py
FTA-server.py		- Contains File Transfer Application Server code.
FTA-client.py		- Contains File Transfer Application Client code. 

Before running client & server FTA programs, please ensure that a copy of rtp_socket.py and rtp_lib.py are in the same folder of the FTP files.
Example.
>root
--->client
------>rtp_socket.py
------>rtp_lib.py
------>FTA-client.py
--->server
------>rtp_socket.py
------>rtp_lib.py
------>FTA-server.py

EVERYTHING MUST BE RUN USING PYTHON3
=================================================================
HOW TO RUN A CLIENT
=================================================================
These commands should be executed in terminal.
Notes:
	-d denotes enabling debug mode.
	   This flag can only be put after IP and port number if IP and port number are entered.

------------------------------
1) To specify an IP and Port:
------------------------------
python3 FTA-client.py <IP_address> <port_num>

If no IP and port are specified, the default is 127.0.1.1:8080

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
- Encryption supported.

=================================================================
KNOWN BUGS AND ISSUES
=================================================================

1) To terminate the server or change the window size, the existing connection must finish or exit on error first. Similarly, to start a new connection with the server, you must go to the server terminal and move past the 'terminate' / 'window size' screens.

2) If the FTA-server.py does not print out the file contents to its console, the client seems to hang and wait indefinitely. So I have it printing any file it reads to the console.