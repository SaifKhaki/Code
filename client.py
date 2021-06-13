import socket
import psutil as p
import yaml
import os
import pynvml
import threading
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
onodes_threads = [None]*o_nodes_count
snodes = []
self_kazaa_constant = 0
onodes_kazaa_constant = [0]*o_nodes_count

username = input("Input your username: ")
print('Waiting for connection response')
try:
    server_connection.connect((host, port))
except socket.error as e:
    print(str(e))

# socket send consistent method 
# it sends the string, waits for the length of string client received, compares this length to the actual length. If both are equal
# it sends ack else, it resends the same txt again.
def socket_send(connection, txt):
    ack = False
    print(">>sending",txt+"...")
    while(not ack):
        connection.send(str.encode(txt))
        len_txt = int(connection.recv(1024).decode('utf-8'))
        if len_txt == len(txt):
            connection.send(str.encode("ack"))
            ack = True
        else:
            connection.send(str.encode("resending"))

# socket receive consistent method 
# it receives the string, then sends its size back to the server and then it waits for an acknowledgement, If ack is received it 
# breaks out of the loop
def socket_rcv(connection, size=1024):
    ack = False
    while(not ack):
        txt = connection.recv(size).decode('utf-8')
        connection.send(str.encode(str(len(txt))))
        ack = True if connection.recv(size).decode('utf-8') == "ack" else False
    print(">>received", txt+"...")
    return txt

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
    try:
        st = speedtest.Speedtest()
        return st.download()/8
    except:
        return 0
   
def receive_rows(connection):
    print("starting receiving rows")
    row_count_str = socket_rcv(connection)
    if row_count_str.startswith("rcv:"):
        row_count = int(row_count_str[len("rcv:"):])
        headers = socket_rcv(connection)[len("rcv:"):].split(":")
        print("row_count:", row_count, "headers:", headers)
        data = []
        for i in range(row_count):
            data_rcvd = socket_rcv(connection, 32768)
            while(data_rcvd.count(":") > 3):
                socket_send(connection, "resend")
                data_rcvd = socket_rcv(connection, 32768)
            data.append(data_rcvd.split(":"))
            socket_send(connection, "rcvd")
            print("Rcvd row:", data[-1][:-1])
    return pd.DataFrame(data, columns=headers)

def send_rows_onode(connection, df, division, index, headers):
    start = division[index - 1] if index > 0 else 0
    end = division[index]
    socket_send(connection, "rcv:"+str(end - start))
    socket_send(connection, "rcv:"+headers)
    for i, row in df[end:start].iterrows():
        socket_send(connection, str(row[0])+":"+str(row[1])+":"+str(row[2])+":"+str(row[3]))
        ack = socket_rcv(connection)
        while(ack != "rcvd"):
            socket_send(connection, str(row[0])+":"+str(row[1])+":"+str(row[2])+":"+str(row[3]))
            ack = socket_rcv(connection)

def ensemble_distribution():
    # receive data from server
    df = receive_rows(server_connection)
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
    onodes_kazaa_constant[id] = float(socket_rcv(connection)[len("k_const:"):])
    
    if((id+1) == o_nodes_count):
        ensemble_distribution()
        
# here onode is sender and snode is receiver
def onode_snode_socket(connection):
    socket_send(connection, "k_const:"+str(self_kazaa_constant))
    df = receive_rows(connection)
    print("df received from supernode of my region has shape: ", df.shape)
 
def send_system_info():
    messages_to_send = 5
    socket_send(server_connection, "rcv:"+str(messages_to_send))
    # download speed in bytes
    socket_send(server_connection, "dsp:"+str(download_speed()))
    # available GPU ram in bytes
    socket_send(server_connection, "gpu:"+str(gpu_memory()))
    # available ram in bytes
    socket_send(server_connection, "ram:"+str(memory()[1]))
    # cpu free in percentage
    socket_send(server_connection, "cpu:"+str(cpu()[0]))
    # cpu cores in count
    socket_send(server_connection, "cor:"+str(cpu()[1]))
    
# first check response received i.e "Server is working"
res = socket_rcv(server_connection)
print(res)

# sending system info
print("\n" + "/"*40 + " waiting for ack " + "/"*40)
send_system_info()

# receive acknowledge
res = socket_rcv(server_connection)
print(res)
    
# receive status in kazaa architecture
print("\n" + "/"*40 + " waiting for status " + "/"*40)
status = socket_rcv(server_connection)[len("status:"):]
self_kazaa_constant = socket_rcv(server_connection)[len("k_const:"):]
print("You are appointed as " + ("Super node." if status=="s" else "Ordinary node.") + " with kazaa constant as", self_kazaa_constant)
            
if status == "s":
    onodesSocket = socket.socket()
    host = socket.gethostname()
    oport = port + 1
    while(True):
        try:
            onodesSocket.bind((host, oport))
            print("\n" + "/"*40 + " Supernode Socket " + "/"*40)
            print("Socket for listening to", o_nodes_count,"ordinary nodes is listening at "+host+":"+str(onodesSocket.getsockname()[1])+"\n")
            break
        except:
            oport += 1
    
    socket_send(server_connection, str(host+":"+str(onodesSocket.getsockname()[1])))
    # server_connection.send(str.encode(str(host+":"+str(onodesSocket.getsockname()[1]))))
    onodesSocket.listen(o_nodes_count)
    
    # open your onode socket for onodes to get connect
    id = 0
    while(id != o_nodes_count):
        Client, address = onodesSocket.accept()
        onodes_connections.append((address[0], address[1], Client))
        onodes_threads[id] = threading.Thread(target = snode_onode_socket, args=(Client, id))
        onodes_threads[id].start()
        # print('Thread Number: ' + str(id) + " - " + 'Connected to ordinary node: ' + address[0] + ':' + str(address[1]))
        id += 1
    
    # joining all the threads
    for i in onodes_threads:
        i.join()
    
elif status == "o":
    print("\n" + "/"*40 + " Ordinary Node Socket " + "/"*40)
    ip_port = socket_rcv(server_connection).split(":")
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