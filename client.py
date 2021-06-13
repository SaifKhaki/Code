import socket
import psutil as p
import yaml
import os
import pynvml
from _thread import *
import speedtest
import math
# ML Specific
import pandas as pd
import numpy as np

# Read YAML file
with open("config.yaml", 'r') as stream:
    config_loaded = yaml.safe_load(stream)
    
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

# Global Fields
status = ''
onodes = []
snodes = []
self_kazaa_constant = 0
onodes_kazaa_constant = [0]*o_nodes_count

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
   
def receive_rows_snode(connection):
    row_count_str = connection.recv(1024).decode('utf-8')
    if row_count_str.startswith("rcv:"):
        row_count = int(row_count_str[len("rcv:"):])
        headers = connection.recv(1024).decode('utf-8')[len("rcv:"):].split(":")
        print("row_count:", row_count, "headers:", headers)
        data = []
        for i in range(row_count):
            data_rcvd = connection.recv(32768).decode('utf-8')
            while(data_rcvd.count(":") > 3):
                connection.send(str.encode("resend"))
                data_rcvd = connection.recv(32768).decode('utf-8')
            data.append(data_rcvd.split(":"))
            connection.send(str.encode("rcvd"))
            print("Rcvd row:", data[-1][:-1])
    return pd.DataFrame(data, columns=headers)

def send_rows_onode(connection, df, division, index, headers):
    start = division[index - 1] if index > 0 else 0
    end = division[index]
    connection.send(str.encode("rcv:"+str(end - start)))
    connection.send(str.encode("rcv:"+headers))
    for i, row in df[end:start].iterrows():
        connection.send(str.encode(str(row[0])+":"+str(row[1])+":"+str(row[2])+":"+str(row[3])))
        ack = connection.recv(1024).decode('utf-8')
        while(ack != "rcvd"):
            connection.send(str.encode(str(row[0])+":"+str(row[1])+":"+str(row[2])+":"+str(row[3])))
            ack = connection.recv(1024).decode('utf-8')

def ensemble_distribution():
    # receive data from server
    df = receive_rows_snode(server_connection)
    print("data rcvd from server for",df.shape[0],"rows with headers:\n",df.columns)
    division = []
    for i in onodes_kazaa_constant:
        division.append(math.ceil((df.shape[0]*i)/sum(onodes_kazaa_constant)))
    # also adding self division
    division.append((df.shape[0]*self_kazaa_constant)/sum(onodes_kazaa_constant))
    division = list(np.cumsum(division))
    # headers
    headers = ":".join(list(df.columns))
    
    # data for regional ordinary nodes
    index = 0
    print("Sending data...")
    for onode_connection in onodes_connections:
        send_rows_onode(onode_connection[2], df, division, index, headers)
        print("Sent all data to", onode_connection[0], "at port", onode_connection[1])
        index += 1
        
    # data for yourself
    df = df[division[-2]:division[-1]]
            
# here snode is sender and onode is receiver
def snode_onode_socket(connection, id):
    print("Waiting for kazaa_constant of",id,"ordinary node.")
    onodes_kazaa_constant[id] = float(connection.recv(1024).decode('utf-8')[len("k_const:"):])
    
    if(id+1 == o_nodes_count):
        ensemble_distribution()
        
# here onode is sender and snode is receiver
def onode_snode_socket(connection):
    connection.send(str.encode("k_const:"+str(self_kazaa_constant)))
    df = receive_rows_snode(connection)
    print("df received from supernode of my region has shape: ", df.shape)
 
def send_system_info():
    messages_to_send = 5
    server_connection.send(str.encode("rcv:"+str(messages_to_send)))
    ack = server_connection.recv(1024).decode('utf-8')
    # download speed in bytes
    server_connection.send(str.encode("dsp:"+str(download_speed())))
    ack = server_connection.recv(1024).decode('utf-8')
    # available GPU ram in bytes
    server_connection.send(str.encode("gpu:"+str(gpu_memory())))
    res = server_connection.recv(1024).decode('utf-8')
    # available ram in bytes
    server_connection.send(str.encode("ram:"+str(memory()[1])))
    res = server_connection.recv(1024).decode('utf-8')
    # cpu free in percentage
    server_connection.send(str.encode("cpu:"+str(cpu()[0])))
    res = server_connection.recv(1024).decode('utf-8')
    # cpu cores in count
    server_connection.send(str.encode("cor:"+str(cpu()[1])))
    res = server_connection.recv(1024).decode('utf-8')
    
# first check response received i.e "Server is working"
res = server_connection.recv(1024).decode('utf-8')
print(res)

# sending system info
send_system_info()

# receive acknowledge
print("\n" + "/"*40 + " waiting for ack " + "/"*40)
res = server_connection.recv(1024).decode('utf-8')
print(res)
print("/"*90 + "\n")
    
# receive status in kazaa architecture
status = server_connection.recv(1024).decode('utf-8')[len("status:"):]
server_connection.send(str.encode("ack"))
self_kazaa_constant = server_connection.recv(1024).decode('utf-8')[len("k_const:"):]
server_connection.send(str.encode("ack"))
print("\n" + "/"*40 + " waiting for status " + "/"*40)
print("You are appointed as " + ("Super node." if status=="s" else "Ordinary node.") + " with kazaa constant as", self_kazaa_constant)
print("/"*90 + "\n")
            
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
        start_new_thread(snode_onode_socket, (Client, id))
        print('Thread Number: ' + str(id) + " - " + 'Connected to ordinary node: ' + address[0] + ':' + str(address[1]))
        id += 1
    
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
            onode_snode_socket(snode_connection)
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