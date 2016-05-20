import socket
import threading
import sys
from urlparse import urlparse

serversocket = None

def main():
	argv = sys.argv

	if len(argv) != 2:
		sys.exit()

	port = int(argv[1])	
	openListenSocket(port)

def openListenSocket(port):
	global serversocket
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	serversocket.bind(('0.0.0.0', port))
	serversocket.listen(5)
	print "Proxy listening on 0.0.0.0:%d" % port
	while True:
		# accept connections from outside
		(clientsocket, address) = serversocket.accept()
		
		ct = threading.Thread(target=client_thread, args=(clientsocket, address))
		ct.run()

def client_listen_thread(client_socket, host_socket):
	try:
		keepOpen = True
		while keepOpen:
			response = client_socket.recv(1024)
			if response == "":
				keepOpen = False
			else:	
				host_socket.send(response)
		host_socket.close()
		client_socket.close()
	except Exception as e:
		return	

def host_listen_thread(client_socket, host_socket):
	try:
		keepOpen = True
		while keepOpen:
			response = host_socket.recv(1024)
			if response == "":
				keepOpen = False
			else:
				client.send(response)
		host_socket.close()
		client_socket.close()
	except Exception as e:
		return	

def client_thread(clientSocket, address):
	clientSocket.settimeout(1)
	keepOpen = True
	message = ""
	while keepOpen:
		try:
			response = clientSocket.recv(1024)
		except Exception as e:
			break
		if response == "":
			keepOpen = False
		message += response
	if len(message) > 0:
		s = message.split('\n')[0].split(' ')
		print ">>> %s %s" % (s[0], s[1])
	if message.startswith("CONNECT"):
		hostAddress = getAddressFromMessage(message)
		if hostAddress is not None:
			hostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			hostSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			hostSocket.bind(("",0)) #Binds to open port
			try:
				hostSocket.connect(hostAddress)
				clientSocket.send("HTTP/1.0 200 OK")
				tc = threading.Thread(target=client_listen_thread, args=(clientSocket, hostSocket))
				tc.run()
				ts = threading.Thread(target=host_listen_thread, args=(clientSocket, hostSocket))
				ts.run()
			except socket.error as e:
				clientSocket.send("HTTP/1.0 502 Bad Gateway")

	else: 	
		message = modifyMessage(message)
		hostAddress = getAddressFromMessage(message)
		if hostAddress is not None:
			hostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			hostSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			hostSocket.bind(("",0)) #Binds to open port
			try:
				hostSocket.connect(hostAddress)
				hostSocket.send(message)
				keepOpen = True
				while keepOpen:
					response = hostSocket.recv(1024)
					if response == "":
						keepOpen = False
					else:	
						clientSocket.send(response)
				hostSocket.close()
			except socket.error as socketerror:
				print("Error: ", socketerror)	
		clientSocket.close();		


def getAddressFromMessage(message):
	headers = message.split("\n")
	for header in headers:
		if header.lower().startswith("host"):
			url = header.split(":", 1)[1].strip()
			result = urlparse(url)
			host = result.hostname
			if host is None:
				host = result.path
			host = host.split(":")[0]
			port = result.port
			if port is None:
				url = headers[0].split(" ")[1]
				result = urlparse(url)
				port = result.port
				if port is None:
					if result.scheme == "https":
						port = 443
					else:	
						port = 80
			address = (host, port)		
			return address
	return None

def modifyMessage(message):
	lines = message.split("\n")
	lines[0] = lines[0].replace("HTTP/1.1", "HTTP/1.0")
	for i in range(1, len(lines)):
		if (lines[i].lower().startswith("connection") or
		 lines[i].lower().startswith("proxy-connection")):
			lines[i] = lines[i].replace("keep-alive", "close")
	return_message = "\n".join(lines) + "\n"
	return return_message


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		serversocket.close() 
		sys.exit(0)