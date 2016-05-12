import socket
import threading

def main():
	openListenSocket(12005)





def openListenSocket(port):
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#serversocket.bind((socket.gethostname(), 80))
	serversocket.bind(('localhost', port))
	serversocket.listen(5)
	while True:
		print "In loop"
		# accept connections from outside
		(clientsocket, address) = serversocket.accept()
		# now do something with the clientsocket
		# in this case, we'll pretend this is a threaded server
		ct = threading.Thread(target=client_thread, args=(clientsocket, address))
		ct.run()

def client_thread(socket, address):
	message = socket.recv(2048)
	print message

if __name__ == "__main__":
	main()
