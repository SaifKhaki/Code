import psutil as p

#Function to get info about Disk Usage.
def disk():
    print("-"*50, "Disk Information", "-"*50)
    total_bytes = 0
    free_bytes = 0
    # getting all of the disk partitions
    for x in p.disk_partitions():
        dsk = p.disk_usage(x.mountpoint)
        total_bytes += dsk.total
        free_bytes += dsk.free
    print("Total disk:", total_bytes, "bytes")
    print("Total disk free:", free_bytes, "bytes")
    print("Percentage of disk free:", free_bytes/total_bytes, "% \n")
    main()

#Function to Get memory/Ram usage.
def memory():
    print("-"*50, "Memory Information", "-"*50)
    #Getting the Memory/Ram Data.
    mem = p.virtual_memory()
    print("Total RAM:", mem.total, "bytes")
    print("Total RAM free:", mem.available, "bytes")
    print("Percentage of RAM free:", mem.available/mem.total,"% \n")
    main()

#Function to get CPU information.
def cpu():
    print("-"*50, "CPU Information", "-"*50)
    #Getting the logical and physical core count.
    print("Percentage of CPU free:", 100-p.cpu_percent(),"%")
    print("Logical/Total Core Count: ", p.cpu_count(logical=True) )
    main()

#Main Function
def main():
    print("\nPress 1 for Disk Info. \nPress 2 for Memory/Ram Info. \nPress 3 for CPU Info. \nPress 0 to exit.")
    choice=int(input(">>> "))
    if choice==1: 
        disk()
    elif choice==2:
        memory()
    elif choice==3:
        cpu()
    elif choice==0:
        pass
    else:
        print("Please provide a valid input")

#Driver Function
if __name__ == "__main__":
    main()