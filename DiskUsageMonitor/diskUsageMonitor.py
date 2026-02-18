import math
import os
from proxmoxer import ProxmoxAPI
# proxmoxer is the library that talks to my proxmox server


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


    # give me all storage devices attached to this node
    storages = proxmox.nodes(node_name).storage.get()

    #get the VMs on my node. store them in a list
    vms = proxmox.nodes(node_name).qemu.get()
    
    # loop through each vm in that list and fetch the name, print it
    # try to get the name, but if it doesn't exist, use 'unknown'
    for vm in vms:
      vm_name = vm.get("name", "unknown")
   

    #get all the containers on my node. store them in a list
    containers = proxmox.nodes(node_name).lxc.get()
    # loop through each container in that list and fetch the name, print it
    # try to get the name, but if it doesn't exist, use 'unknown'
    for container in containers:
      cnt_name = container.get("name", "unknown")


if __name__ == "__main__":
  main()

# 1. Change it so that it reads disk usage instead (you'll read the disk usage via the node exporter that you need to install on each container and VM)
# 2. include disk usage for the host itself
# 3. if above 80, email you