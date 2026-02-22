import math
import os
import requests #library for making HTTP calls
from proxmoxer import ProxmoxAPI # library that talks to my proxmox server

# loading environment variables from rasp pi
host = os.getenv("PVE_HOST") #IP of machine
user = os.getenv("PVE_USER") #API user you created
token_name = os.getenv("PVE_TOKEN_NAME")
token_secret = os.getenv("PVE_TOKEN_SECRET")

# if one or more env variables fails to load, exit program
if not all([host, user, token_name, token_secret]):
  raise SystemExit("Missing one or more environment variables: PVE_HOST, PVE_USER, PVE_TOKEN_NAME, or PVE_TOKEN_SECRET")

# assigning the connection object to a variable
proxmox = ProxmoxAPI(
  host,
  user=user,
  token_name=token_name,
  token_value=token_secret,
  verify_ssl=False   #don't give me certificate errors
)

def percentage_used(used, total):
  if not total:
    return None
  return ( used / total ) * 100

def main():
  # get my proxmox nodes
  nodes = proxmox.nodes.get()
  # loop through each node in my cluster and get the node name
  for node in nodes:
    node_name = node["node"]
    print(f"\nNode: {node_name} (storage usage)")
    # give me all storage devices attached to this node
    storages = proxmox.nodes(node_name).storage.get()
    for s in storages:
      # get the storage name. if no name, set it equal to "unknown-storage"
      storage_name = s.get("storage", "unknown-storage")
      used = s.get("used")
      total = s.get("total")
      # call the function, pass in used and total
      pct = percentage_used(used, total)
      if pct is None:
        print(f"- {storage_name}: unknown")
      else:
        print(f"- {storage_name}: {math.floor(pct)}%")

    #--------------------------------VM Section--------------------------------------------
    #--------------------------------------------------------------------------------------
    #get the VMs on my node. store them in a list
    vms = proxmox.nodes(node_name).qemu.get()
    
    # loop through each vm in that list and fetch the name
    # try to get the name, but if it doesn't exist, use 'unknown'
    # print the name along with the VM ID
    for vm in vms:
      vm_name = vm.get("name", "unknown")
      vmid = vm.get("vmid")
      print(f"VM: {vm_name} (vmid={vmid})")
      #select the node, select the VM by ID, ask the agent inside for the network interfaces
      agent_net = proxmox.nodes(node_name).qemu(vmid).agent("network-get-interfaces").get()
      print(f"  agent interfaces returned: {len(agent_net)}")
      print(agent_net[0]) #look inside first interface object
      #look inside for ip address, return it if it exists, if not, return an empty list
      ip_list = agent_net[0].get("ip-addresses", [])
      for ip in ip_list:
        print(f"    found IP: {ip.get('ip-address')}")
        ip_addr = ip.get("ip-address")
        if ip_addr == "127.0.0.1":
           continue
        # get the metrics, store it in resp
        resp = requests.get(f"http://{ip_addr}:9100/metrics")
        # 200 = success   404 = wrong URL
        print(f"         node_exporter HTTP status: {resp.status_code}")
        print(f" metrics bytes: {len(resp.text)}")
        lines = resp.text.splitlines()
        #loop through each metric line. filter for disk size
        # / ensures we get the root filesystem
        # returns first match or None
        size_line = next((l for l in lines if "node_filesystem_size_bytes" in l and 'mountpoint="/"' in l), None)
        size_bytes = int(size_line.split()[-1]) if size_line else None
        avail_line = next((l for l in lines if "node_filesystem_avail_bytes" in l and 'mountpoint="/"' in l), None)
        avail_bytes = int(avail_line.split()[-1]) if avail_line else None
        used_bytes = (size_bytes - avail_bytes) if size_bytes and avail_bytes else None
        disk_pct = percentage_used(used_bytes, size_bytes)
        if disk_pct is not None:
           print(f"      disk usage: {math.floor(disk_pct)}%")
        if disk_pct and disk_pct >= 80:
          print("      WARNING: disk usage above 80%")
    
    #---------------------------------Container Section-------------------------------------
    #---------------------------------------------------------------------------------------
    #get all the containers on my node. store them in a list
    containers = proxmox.nodes(node_name).lxc.get()
    # loop through each container in that list and fetch the name, print it
    # try to get the name, but if it doesn't exist, use 'unknown'
    for container in containers:
      cnt_name = container.get("name", "unknown")
      ctid = container.get("vmid")
      # get container network interfaces from Proxmox
      interfaces = proxmox.nodes(node_name).lxc(ctid).interfaces.get()
      # loop through interfaces and find IP addresses
      for iface in interfaces:
          for addr in iface.get("inet", []):
              ip_addr = addr.get("address")
              # skip localhost
              if ip_addr == "127.0.0.1":
                  continue
              print(f"CT: {cnt_name} ({ip_addr})")
              # connect to node exporter
              resp = requests.get(f"http://{ip_addr}:9100/metrics")
              lines = resp.text.splitlines()
              size_line = next(
                  (l for l in lines if "node_filesystem_size_bytes" in l and 'mountpoint="/"' in l),
                  None
              )

              avail_line = next(
                  (l for l in lines if "node_filesystem_avail_bytes" in l and 'mountpoint="/"' in l),
                  None
              )

              if size_line and avail_line:
                  size_bytes = int(size_line.split()[-1])
                  avail_bytes = int(avail_line.split()[-1])
                  used_bytes = size_bytes - avail_bytes
                  disk_pct = percentage_used(used_bytes, size_bytes)
                  print(f"      disk usage: {math.floor(disk_pct)}%")
                  if disk_pct >= 80:
                      print("      WARNING: disk usage above 80%")

if __name__ == "__main__":
  main()
 
# 1. if above 80, email you

# you need to upgrade pihole so you can install node exporter on it
# figure out how to install node exporter on Home Assistant