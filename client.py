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
    while(True):
        try:
            print("waiting to rcv count")
            to_be_rcvd_bytes = int(connection.recv(1024).decode('utf-8'))
            connection.send(str.encode("rcvd"))
            break
        except:
            connection.send(str.encode("0"))
            
    while(rcvd_bytes < to_be_rcvd_bytes):
        rcvd = connection.recv(1024)
        rcvd_bytes += len(rcvd)
        rcvd_str += rcvd.decode('utf-8')
        print("waiting to rcv whole string, rcvd yet: " + rcvd_str)
    print("whole string rcvd")
    return rcvd_str

# a generalized method for sending all data requested
def send_socket_str(connection, text):
    sent_bytes = 0
    to_be_send_bytes = len(text.encode('utf-8'))
    while(True):
        print("sending rcv count")
        connection.send(str.encode(str(to_be_send_bytes)))
        ack = connection.recv(2048).decode('utf-8')
        if(ack == "rcvd"):
            break
        
    while(sent_bytes < to_be_send_bytes):
        sent_bytes += connection.send(str.encode(text[sent_bytes:]))
        print("sending all bytes:"+str(sent_bytes)+"/",str(to_be_send_bytes))
    print("sent")
        
# first check response received i.e "Server is working"
res = rcv_socket_str(ClientMultiSocket)
print(res)

# sending system info
messages_to_send = 5
send_socket_str(ClientMultiSocket, "rcv:"+str(messages_to_send))

# download speed in bytes
send_socket_str(ClientMultiSocket, str(download_speed()))
# available GPU ram in bytes
send_socket_str(ClientMultiSocket, str(gpu_memory()))
# available ram in bytes
send_socket_str(ClientMultiSocket, str(memory()[1]))
# cpu free in percentage
send_socket_str(ClientMultiSocket, str(cpu()[0]))
# cpu cores in count
send_socket_str(ClientMultiSocket, str(cpu()[1]))

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
    send_socket_str(ClientMultiSocket, "rcv:"+messages_to_send)
    for i in range(int(messages_to_send)):
        Input = input('>>>> ')
        send_socket_str(ClientMultiSocket, Input)
    if messages_to_send == "0":
        break
    res = rcv_socket_str(ClientMultiSocket)
    print(res)

ClientMultiSocket.close()