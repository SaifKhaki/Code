import socket
import psutil as p
import yaml
import os
import pynvml
import speedtest

# Read YAML file
with open("config.yaml", 'r') as stream:
    config_loaded = yaml.safe_load(stream)
    
# Global Fields
status = ''
onodes = []
snodes = []
    
# Connecting to server's ip address
ClientMultiSocket = socket.socket()
host = config_loaded["server"]["ip"]
port = config_loaded["server"]["port"]
o_nodes_count = config_loaded["kazaa"]["o_node_per"]

username = input("Input your username: ")
print('Waiting for connection response')
try:
    ClientMultiSocket.connect((host, port))
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
   
def rcv_socket_str(connection):
    rcvd_bytes = 0
    rcvd_str = ""
    to_be_rcvd_bytes = int(connection.recv(1024).decode('utf-8'))
    while(rcvd_bytes < to_be_rcvd_bytes):
        rcvd = connection.recv(1024)
        rcvd_bytes += len(rcvd)
        rcvd_str += rcvd.decode('utf-8')
    return rcvd_str
    
# first check response received i.e "Server is working"
res = rcv_socket_str(ClientMultiSocket)
print(res)

# sending system info
messages_to_send = 5
ClientMultiSocket.send(str.encode("rcv:"+str(messages_to_send)))

# download speed in bytes
ClientMultiSocket.send(str.encode(str(download_speed())))
# available GPU ram in bytes
ClientMultiSocket.send(str.encode(str(gpu_memory())))
# available ram in bytes
ClientMultiSocket.send(str.encode(str(memory()[1])))
# cpu free in percentage
ClientMultiSocket.send(str.encode(str(cpu()[0])))
# cpu cores in count
ClientMultiSocket.send(str.encode(str(cpu()[1])))

# receive acknowledge
print("\n" + "/"*40 + " waiting for ack " + "/"*40)
res = rcv_socket_str(ClientMultiSocket)
print(res)
print("/"*90 + "\n")
    
# receive status in kazaa architecture
status = rcv_socket_str(ClientMultiSocket)[len("status:"):]
print("\n" + "/"*40 + " waiting for ack " + "/"*40)
print("You are appointed as " + ("Super node." if status=="s" else "Ordinary node."))
print("/"*90 + "\n")

#:<change>
# receiving ip addresses of onode under me if I am a supernode
if status == "s":
    data = rcv_socket_str(ClientMultiSocket)
    if data.startswith("rcv:"):
        rcv_onodes_count = int(data[len("rcv:"):])
        if(rcv_onodes_count == o_nodes_count):
            for i in range(rcv_onodes_count):
                ip_port = rcv_socket_str(ClientMultiSocket).split(":")
                onodes.append((ip_port[0], ip_port[1]))
    print("My onodes are:")
    print(onodes)
elif status == "o":
    ip_port = rcv_socket_str(ClientMultiSocket).split(":")
    snodes.append((ip_port[0], ip_port[1]))
    print("My snodes are:")
    print(snodes)
#:</change>

    

# series of many to one communication between server and client
while True:
    messages_to_send = input('Write number of messages you want to send >>>> ')
    ClientMultiSocket.send(str.encode("rcv:"+messages_to_send))
    for i in range(int(messages_to_send)):
        Input = input('>>>> ')
        ClientMultiSocket.send(str.encode(Input))
    if messages_to_send == "0":
        break
    res = rcv_socket_str(ClientMultiSocket)
    print(res)

ClientMultiSocket.close()