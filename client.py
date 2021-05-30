import socket
import psutil as p

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

#:<change>
def disk():
    total_bytes = 0
    free_bytes = 0
    for x in p.disk_partitions():
        dsk = p.disk_usage(x.mountpoint)
        total_bytes += dsk.total
        free_bytes += dsk.free
    return (total_bytes, free_bytes)

def memory():
    mem = p.virtual_memory()
    return (mem.total, mem.available)

def cpu():
    return (100-p.cpu_percent(), p.cpu_count(logical=True))

# first check response received i.e "Server is working"
res = ClientMultiSocket.recv(1024)
print(res.decode('utf-8'))

# sending system info
messages_to_send = 6
ClientMultiSocket.send(str.encode("rcv:"+str(messages_to_send)))
ClientMultiSocket.send(str.encode(str(disk()[0])))
ClientMultiSocket.send(str.encode(str(disk()[1])))
ClientMultiSocket.send(str.encode(str(memory()[0])))
ClientMultiSocket.send(str.encode(str(memory()[1])))
ClientMultiSocket.send(str.encode(str(cpu()[0])))
ClientMultiSocket.send(str.encode(str(cpu()[1])))
#:</change>

# receive acknowledge
print("\n" + "/"*40 + " waiting for ack " + "/"*40)
res = ClientMultiSocket.recv(1024)
print(res.decode('utf-8'))
print("/"*90 + "\n")
    
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