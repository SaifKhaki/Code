import socket
import psutil as p
import yaml
import os
import pynvml
import speedtest

#:<change>
# Read YAML file
with open("config.yaml", 'r') as stream:
    config_loaded = yaml.safe_load(stream)
    
# Global Fields
status = ''
    
# Connecting to server's ip address
ClientMultiSocket = socket.socket()
host = config_loaded["server"]["ip"]
port = config_loaded["server"]["port"]
#:</change>

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

#:<change>
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
#:</change>
    
# first check response received i.e "Server is working"
res = ClientMultiSocket.recv(1024)
print(res.decode('utf-8'))

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
res = ClientMultiSocket.recv(1024).decode('utf-8')
print(res)
print("/"*90 + "\n")
    
#:<change>
# receive status in kazaa architecture
status = ClientMultiSocket.recv(1024).decode('utf-8')[len("status:"):]
print("\n" + "/"*40 + " waiting for ack " + "/"*40)
print("You are appointed as " + ("Super node." if status=="s" else "Ordinary node."))
print("/"*90 + "\n")
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
    res = ClientMultiSocket.recv(1024)
    print(res.decode('utf-8'))

ClientMultiSocket.close()