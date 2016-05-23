import socket
import sys
from urlparse import urlparse
import datetime
import pyuv
import signal
from multiprocessing import Process

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
		p = Process(target=client_thread, args=(clientsocket,))
		p.start()

def client_listen_thread(client_socket, host_socket):
	try:
		keepOpen = True
		while keepOpen:
			try:
				response = client_socket.recv(1024)	
			except socket.timeout as e:
				continue	
			except socket.error as e:
				break	
			if response == "":
				keepOpen = False
			else:	
				host_socket.send(response)	
	
	except Exception as e:
		return	
	finally:
		host_socket.shutdown(socket.SHUT_RDWR)
		client_socket.shutdown(socket.SHUT_RDWR)
		host_socket.close()
		client_socket.close()	

def host_listen_thread(client_socket, host_socket):
	try:
		keepOpen = True
		while keepOpen:
			try:
				response = host_socket.recv(1024)
			except socket.timeout as e:
				continue	
			except socket.error as e:
				break	
			if response == "":
				keepOpen = False
			else:
				client_socket.send(response)
		
	except Exception as e:
		return	
	finally:
		host_socket.shutdown(socket.SHUT_RDWR)
		client_socket.shutdown(socket.SHUT_RDWR)
		host_socket.close()
		client_socket.close()	

def client_thread(clientSocket):
	clientSocket.settimeout(3)
	keepOpen = True
	message = ""
	try:
		message = clientSocket.recv(8192)	
	except Exception as e:
		print "TIMEOUT"	
		
	if len(message) > 0:
		s = message.split('\n')[0].split(' ')
		print ">>> %s %s" % (s[0], s[1])
	hostAddress = getAddressFromMessage(message)
	message = modifyMessage(message)	
	if hostAddress is not None:
		hostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		hostSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		hostSocket.bind(("",0)) #Binds to open port
		if message.startswith("CONNECT"):
			try:
				print 1
				hostSocket.connect(hostAddress)
				clientSocket.send("HTTP/1.0 200 OK")
				clientSocket.settimeout(1)
				hostSocket.settimeout(1)
				pc = Process(target=client_listen_thread, args=(clientSocket, hostSocket))
				pc.start()
				ps = Process(target=host_listen_thread, args=(clientSocket, hostSocket))
				ps.start()
				print 2
			except socket.error as e:
				clientSocket.send("HTTP/1.0 502 Bad Gateway")
		else: 	
			hostSocket.settimeout(1)
			try:
				hostSocket.connect(hostAddress)
				hostSocket.send(message)
				keepOpen = True
				while keepOpen:
					try:
						response = hostSocket.recv(1024)
					except socket.timeout as e:
						continue	
					except socket.error as e:
						break		
					if response == "":
						keepOpen = False
					else:	
						clientSocket.send(response)
				hostSocket.close()
			except socket.error as socketerror:
				print("Error: ", socketerror)
			finally:	
				hostSocket.close()	
				clientSocket.close();	

def getAddressFromMessage(message):
	headers = message.split("\n")
	host = None
	port = None
	for header in headers:
		if header.lower().startswith("host"):
			url = header.split(":", 1)[1].strip()
			result = urlparse(url)
			host = result.hostname
			if host is None:
				host = result.path
			host = host.split(":")[0]
			port = result.port
			break	
	if port is None:
		line = headers[0].split(" ")
		url = None
		if len(line) > 1:
			url = line[1]
		else: 
			return None			
		result = urlparse(url)	
		port = result.port
		if host == None:
			host = result.hostname
		if port is None:
			if result.scheme == "https":
				port = 443
			else:	
				port = 80		
	address = (host, port)	
	return address

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