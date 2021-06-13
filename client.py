import socket
import psutil as p
import yaml
import os
import pynvml
from _thread import *
import speedtest
# ML Specific
import pandas as pd

# Read YAML file
with open("config.yaml", 'r') as stream:
    config_loaded = yaml.safe_load(stream)
    
# Global Fields
status = ''
onodes = []
snodes = []

######################################## Connections ################################
# format: [(ip,port,connection)i] for i=onode_count
onodes_connections = []
# format: connection_object
snode_connection = None
server_connection = None
    
# Connecting to server's ip address
server_connection = socket.socket()
host = config_loaded["server"]["ip"]
port = config_loaded["server"]["port"]
o_nodes_count = config_loaded["kazaa"]["o_node_per"]

username = input("Input your username: ")
print('Waiting for connection response')
try:
    server_connection.connect((host, port))
except socket.error as e:
    print(str(e))

def memory():
    mem = p.virtual_memory()
    return (mem.total, mem.available)

def cpu():
    return (100-p.cpu_percent(), p.cpu_count(logical=True))

def gpu_memory():
    try:
        pynvml.nvmlInit()
        # 1 here is the GPU id
        handle = pynvml.nvmlDeviceGetHandleByIndex(1)
        meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return meminfo.free
    except:
        return 0

def download_speed():
    st = speedtest.Speedtest()
    return st.download()/8
   
def multi_threaded_client(connection, id):
    print(str(id) + " inside")
        
# first check response received i.e "Server is working"
res = server_connection.recv(1024).decode('utf-8')
print(res)

# sending system info
messages_to_send = 5
server_connection.send(str.encode("rcv:"+str(messages_to_send)))

# download speed in bytes
server_connection.send(str.encode(str(download_speed())))
# available GPU ram in bytes
server_connection.send(str.encode(str(gpu_memory())))
# available ram in bytes
server_connection.send(str.encode(str(memory()[1])))
# cpu free in percentage
server_connection.send(str.encode(str(cpu()[0])))
# cpu cores in count
server_connection.send(str.encode(str(cpu()[1])))

# receive acknowledge
print("\n" + "/"*40 + " waiting for ack " + "/"*40)
res = server_connection.recv(1024).decode('utf-8')
print(res)
print("/"*90 + "\n")
    
# receive status in kazaa architecture
status = server_connection.recv(1024).decode('utf-8')[len("status:"):]
print("\n" + "/"*40 + " waiting for status " + "/"*40)
print("You are appointed as " + ("Super node." if status=="s" else "Ordinary node."))
print("/"*90 + "\n")

def receive_rows_snode():
    row_count_str = server_connection.recv(1024).decode('utf-8')
    if row_count_str.startswith("rcv:"):
        row_count = int(row_count_str[len("rcv:"):])
        headers = server_connection.recv(1024).decode('utf-8')[len("rcv:"):].split(":")
        print("row_count:", row_count, "headers:", headers)
        data = []
        for i in range(row_count):
            data_rcvd = server_connection.recv(32768).decode('utf-8')
            while(data_rcvd.count(":") > 3):
                server_connection.send(str.encode("resend"))
                data_rcvd = server_connection.recv(32768).decode('utf-8')
            data.append(data_rcvd.split(":"))
            server_connection.send(str.encode("rcvd"))
            print("Rcvd row:", data[-1][:-1])
    return pd.DataFrame(data, columns=headers)

def send_rows_onode(connection, df, div, index, headers):
    connection.send(str.encode("rcv:"+str(div)))
    connection.send(str.encode("rcv:"+headers))
    for i, row in df[int(div*index):int(div*(index+1))].iterrows():
    # for i, row in df[:30].iterrows():
        connection.send(str.encode(str(row[0])+":"+str(row[1])+":"+str(row[2])+":"+str(row[3])))
        ack = connection.recv(1024).decode('utf-8')
        while(ack != "rcvd"):
            connection.send(str.encode(str(row[0])+":"+str(row[1])+":"+str(row[2])+":"+str(row[3])))
            ack = connection.recv(1024).decode('utf-8')
            
if status == "s":
    onodesSocket = socket.socket()
    host = socket.gethostname()
    oport = port + 1
    while(True):
        try:
            onodesSocket.bind((host, oport))
            print("Socket for listening to", o_nodes_count,"ordinary nodes is listening at "+host+":"+str(onodesSocket.getsockname()[1])+"\n")
            break
        except:
            oport += 1
    
    server_connection.send(str.encode(str(host+":"+str(onodesSocket.getsockname()[1]))))
    onodesSocket.listen(o_nodes_count)
    
    # open your onode socket for onodes to get connect
    id = 0
    while(id != o_nodes_count):
        Client, address = onodesSocket.accept()
        onodes_connections.append((address[0], address[1], Client))
        start_new_thread(multi_threaded_client, (Client, id))
        print('Thread Number: ' + str(id) + " - " + 'Connected to ordinary node: ' + address[0] + ':' + str(address[1]))
        id += 1
        
    # receive data from server
    df = receive_rows_snode()
    print("data rcvd from server for",df.shape[0],"rows with headers:\n",df.columns)
    
    # decide each nodes data
    
    # send data to respective ordinary nodes
    # df = receive_rows_snode()
    
elif status == "o":
    ip_port = server_connection.recv(1024).decode('utf-8').split(":")
    snodes.append((ip_port[0], int(ip_port[1])))
    
    for ip,port in snodes:
        print("Snode of my region is present at "+ip+":"+str(port))
    
    # starting connections with onodes:
    i = 0
    for ip,port in snodes:
        try:
            snode_connection = socket.socket()
            snode_connection.connect((ip, port))
            print("Connected to the supernode.\n")
        except socket.error as e:
            print(str(e))
        i += 1

# series of many to one communication between server and client
while True:
    messages_to_send = input('Write number of messages you want to send >>>> ')
    # send_socket_str(ClientMultiSocket, "rcv:"+messages_to_send)
    server_connection.send(str.encode("rcv:"+messages_to_send))
    for i in range(int(messages_to_send)):
        Input = input('>>>> ')
        # send_socket_str(ClientMultiSocket, Input)
        server_connection.send(str.encode(Input))
    if messages_to_send == "0":
        break
    # res = rcv_socket_str(ClientMultiSocket)
    res = server_connection.recv(1024).decode('utf-8')
    print(res)

server_connection.close()