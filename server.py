import socket
from _thread import *

# giving a dynamic IP to the server
ServerSideSocket = socket.socket()
host = socket.gethostname()
print("The server's IP address is (add this to the client's input): ", socket.gethostbyname(host))
port = 2057
clientId = -1
ThreadCount = 0
try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))

# maximum number of clients to listen to
print('Socket is listening..')
ServerSideSocket.listen(10)

# function to be run in independent thread
def multi_threaded_client(connection, id):
    connection.send(str.encode('Server is working:'))
    while True:
        data = connection.recv(2048)
        response = 'Server message: ' + data.decode('utf-8')
        if not data:
            break
        elif data.decode('utf-8').startswith("rcv:"):
            count = int(data.decode('utf-8')[4:])
            for i in range(count):
                data = connection.recv(2048).decode('utf-8')
                response += " " + data
                
        connection.sendall(str.encode(response))
    connection.close()

# always open for more clients to connect
while True:
    Client, address = ServerSideSocket.accept()
    clientId += 1
    start_new_thread(multi_threaded_client, (Client, clientId))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount) + " - " + 'Connected to: ' + address[0] + ':' + str(address[1]))
ServerSideSocket.close()