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





def main():
  # get my proxmox nodes
  nodes = proxmox.nodes.get()


  # loop through each node in my cluster and get the node name
  for node in nodes:
    node_name = node["node"]
    #get the VMs on my node. store them in a list
    vms = proxmox.nodes(node_name).qemu.get()
    
    # loop through each vm in that list and fetch the name, print it
    # try to get the name, but if it doesn't exist, use 'unknown'
    for vm in vms:
      vm_name = vm.get("name", "unknown")
      print(f"VM: {vm_name}")

    #get all the containers on my node. store them in a list
    containers = proxmox.nodes(node_name).lxc.get()
    # loop through each container in that list and fetch the name, print it
    # try to get the name, but if it doesn't exist, use 'unknown'
    for container in containers:
      cnt_name = container.get("name", "unknown")
      print(f"CT: {cnt_name}")


if __name__ == "__main__":
  main()



# 1. Change it so that it reads disk usage instead
# 2. include disk usage for the host itself
# 3. if above 80, email you




# import subprocess

# du = subprocess.run(["df", "/"],
#     capture_output=True,
#     text=True)

# print(int(du.stdout.splitlines()[1].split()[4][:-1]))

# if int(du.stdout.splitlines()[1].split()[4][:-1]) > 12:
#   print("bigger than 12")





#capture the whole output of "df /". split it into lines a grab the second line. Split that on the whitespaces and grab the 5th data. Remove the % from the end. Turn it into an int

