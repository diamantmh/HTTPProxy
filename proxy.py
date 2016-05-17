import socket
import threading
import sys
from urlparse import urlparse

serversocket = None

def main():
	openListenSocket(12016)

def openListenSocket(port):
	global serversocket
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	serversocket.bind(('0.0.0.0', port))
	serversocket.listen(5)
	while True:
		# accept connections from outside
		(clientsocket, address) = serversocket.accept()
		
		ct = threading.Thread(target=client_thread, args=(clientsocket, address))
		#ct = threading.Thread(target=test_thread)
		ct.run()	

def client_thread(clientSocket, address):
	message = None
	while message == None:
		print "In Loop"
		message = clientSocket.recv(2048)
	if message.startswith("CONNECT"):
		print "Implement Connect"
	else: 	
		message = modifyMessage(message)
		hostAddress = getAddressFromMessage(message)
		if hostAddress is not None:
			hostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			hostSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			hostSocket.bind(("",0)) #Binds to open port
			try:
				hostSocket.connect(hostAddress)
			except socket.error as socketerror:
				print("Error: ", socketerror)
			hostSocket.send(message)
			keepOpen = True
			counter = 1
			while keepOpen:
				print counter
				counter += 1
				response = hostSocket.recv(1024)
				#print response
				if response == "":
					keepOpen = False
				else:	
					clientSocket.send(response)
			hostSocket.close()
		else:
			print "hostAddress was None"	
	print "Connection Terminated"	
	clientSocket.close();		


def getAddressFromMessage(message):
	headers = message.split("\n")
	for header in headers:
		if header.lower().startswith("host"):
			url = header.split(":", 1)[1].strip()
			print url
			result = urlparse(url)
			print result
			host = result.hostname
			if host is None:
				host = result.path
			print host
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
			print address	
			return address
	return None

def modifyMessage(message):
	message = message.replace("keep-alive", "close")
	message = message.replace("HTTP/1.1", "HTTP/1.0")
	return message

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		serversocket.close() 
		sys.exit(0)