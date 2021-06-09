import socket
import os
from _thread import *
import yaml
import io

#:<change>
# Read YAML file
with open("config.yaml", 'r') as stream:
    config_loaded = yaml.safe_load(stream)

# reading from config file
port = config_loaded["server"]["port"]
datasets = config_loaded["datasets"]
s_nodes = config_loaded["kazaa"]["s_nodes"]
o_nodes = config_loaded["kazaa"]["o_node_per"]
all_nodes = s_nodes + (s_nodes*o_nodes)

# Global fields
clientId = -1
ThreadCount = 0
connections = []
download_speed = [0]*all_nodes
gpu_ram_free = [0]*all_nodes
ram_free = [0]*all_nodes
cpu_free = [0]*all_nodes
cpu_cores = [0]*all_nodes
status = ['']*all_nodes
kazaa_constant = [0]*all_nodes
#:</change>

# giving a dynamic IP and reuseable port to the server
ServerSideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ServerSideSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = socket.gethostname()
print("The server's IP address: ", socket.gethostbyname(host))
try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))
ServerSideSocket.listen(all_nodes)

#:<change>
# Write server host to config.yaml file
config_loaded["server"]["ip"] = socket.gethostbyname(host)
with io.open('config.yaml', 'w', encoding='utf8') as outfile:
    yaml.dump(config_loaded, outfile, default_flow_style=False, allow_unicode=True)

# giving minimum requirement of RAM for supernode
def get_required_ram(fileSize, node="s"):
    amount = fileSize/s_nodes
    if(node == "o"):
        amount /= o_nodes
    return amount
        
def cal_kazaa_constant(id):
    data_per_region = get_required_ram(size)
    # /10 means to get data downloaded in max 10 secs
    bytes_ps = data_per_region/10
    kazaa_constant[id] = (((gpu_ram_free[id]+ram_free[id] >= data_per_region)*0.5)
                          +(1 if (download_speed[id]/bytes_ps) >= 1 else (download_speed[id]/bytes_ps))*0.2
                          +((gpu_ram_free[id]/(max(gpu_ram_free) if max(gpu_ram_free) != 0 else 1))*0.15)
                          +((ram_free[id]/(max(ram_free) if max(ram_free) != 0 else 1))*0.075)
                          +((cpu_free[id]/100)*0.05)
                          +(1 if (cpu_cores[id]/8)>=1 else (cpu_cores[id]/8)*0.025)
                          )

# classifying nodes into supernode or ordinary node
def get_node_status(id):
    const = kazaa_constant[id]
    a = kazaa_constant.copy()
    a.sort()
    if const in a[len(a)-s_nodes:]:
        return "s"
    else:
        return "o"

# initiating formation of kazaa architecture
def initiate_kazaa():
    for i in range(len(connections)):
        cal_kazaa_constant(i)
    
    print("Constants calculated are: ", kazaa_constant)
    
    for i in range(len(connections)):
        status[i] = get_node_status(i)
        
    print("Statuses calculated are: ", status)
        
    for connection in connections:
        send_str = "status:" + status[connections.index(connection)]
        connection.sendall(str.encode(send_str))
#:</change>
        
    

# function to be run in independent thread
def multi_threaded_client(connection, id):
    connection.sendall(str.encode('Server is working:'))
    
    # receiving system info
    data = connection.recv(2048)
    if data.decode('utf-8').startswith("rcv:"):
        count = int(data.decode('utf-8')[4:])
        if(count == 5):
            download_speed[id] = float(connection.recv(2048).decode('utf-8'))
            gpu_ram_free[id] = float(connection.recv(2048).decode('utf-8'))
            ram_free[id] = float(connection.recv(2048).decode('utf-8'))
            cpu_free[id] = float(connection.recv(2048).decode('utf-8'))
            cpu_cores[id] = int(connection.recv(2048).decode('utf-8'))

            # sending ack
            send_str = "ack: received following system info:  Download_speed = " + str(download_speed[id]) + "B Free_GPU_RAM = " + str(gpu_ram_free[id]) + "B Free_RAM = " + str(ram_free[id]) + "B Free_CPU = " + str(cpu_free[id]) + " CPU_Cores = " + str(cpu_cores[id])
            connection.sendall(str.encode(send_str))
#:<change>
    connections.append(connection)
    if(len(connections) >= all_nodes):
        initiate_kazaa()
#:</change>

    while True:
        data = connection.recv(2048)
        response = 'Server message: ' + data.decode('utf-8')
        if not data:
            break
        elif data.decode('utf-8').startswith("rcv:"):
            count = int(data.decode('utf-8')[len("rcv:"):])
            for i in range(count):
                data = connection.recv(2048).decode('utf-8')
                response += " " + data
                
        connection.sendall(str.encode(response))
    connection.close()

#:<change>
# assuming dataset uploaded by the user
fileNumber = int(input("Which dataset you want to use from 0 - " + str(len(datasets)-1) + " : "))
size = os.path.getsize(datasets[fileNumber]) 
#:</change>

# always open for more clients to connect
print('Socket is listening..')
while True:
    Client, address = ServerSideSocket.accept()
    clientId += 1
    start_new_thread(multi_threaded_client, (Client, clientId))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount) + " - " + 'Connected to: ' + address[0] + ':' + str(address[1]))
ServerSideSocket.close()