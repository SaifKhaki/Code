import socket
from _thread import *

#:<change>
# config
max_clients = 10
port = 2057

# giving a dynamic IP and reuseable port to the server
ServerSideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ServerSideSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#:</change>
host = socket.gethostname()
print("The server's IP address is (add this to the client's input): ", socket.gethostbyname(host))
try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))
    
#:<change>
# Global fields
clientId = -1
ThreadCount = 0
disk_total = [0]*max_clients
disk_free = [0]*max_clients
ram_total = [0]*max_clients
ram_free = [0]*max_clients
cpu_free = [0]*max_clients
cpu_cores = [0]*max_clients
#:</change>

# maximum number of clients to listen to
print('Socket is listening..')
ServerSideSocket.listen(max_clients)

# function to be run in independent thread
def multi_threaded_client(connection, id):
    connection.send(str.encode('Server is working:'))
    
    #:<change>
    # receiving system info
    data = connection.recv(2048)
    if data.decode('utf-8').startswith("rcv:"):
        count = int(data.decode('utf-8')[4:])
        if(int(count) == 6):
            disk_total[id] = float(connection.recv(2048).decode('utf-8'))
            disk_free[id] = float(connection.recv(2048).decode('utf-8'))
            ram_total[id] = float(connection.recv(2048).decode('utf-8'))
            ram_free[id] = float(connection.recv(2048).decode('utf-8'))
            cpu_free[id] = float(connection.recv(2048).decode('utf-8'))
            cpu_cores[id] = int(connection.recv(2048).decode('utf-8'))

            # sending ack
            send_str = "ack: received following system info: Total_disk = " + str(disk_total[id]) + " Free_disk = " + str(disk_free[id]) + " Total_RAM = " + str(ram_total[id]) + " Free_RAM = " + str(ram_free[id]) + " Free_CPU = " + str(cpu_free[id]) + " CPU_Cores = " + str(cpu_cores[id])
            connection.sendall(str.encode(send_str))
    #:</change>

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