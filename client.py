import socket

# Connecting to server's ip address
ClientMultiSocket = socket.socket()
host = input("Specify server's IP address: ")
port = 2057
username = input("Input your username: ")
print('Waiting for connection response')
try:
    ClientMultiSocket.connect((host, port))
except socket.error as e:
    print(str(e))

# first check response received 
res = ClientMultiSocket.recv(1024)
print(res.decode('utf-8'))

# series of many to one communication between server and client
while True:
    messages_to_send = input('Write number of messages you want to send >>>> ')
    ClientMultiSocket.send(str.encode("rcv:"+messages_to_send))
    for i in range(int(messages_to_send)):
        Input = input('>>>> ')
        ClientMultiSocket.send(str.encode(Input))
    if messages_to_send == "0":
        break
    res = ClientMultiSocket.recv(1024)
    print(res.decode('utf-8'))

ClientMultiSocket.close()