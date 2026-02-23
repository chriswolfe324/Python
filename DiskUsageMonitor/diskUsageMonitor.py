import math
import smtplib
import ssl
import os
import requests
from email.message import EmailMessage
from proxmoxer import ProxmoxAPI

host = os.getenv("PVE_HOST")
user = os.getenv("PVE_USER")
token_name = os.getenv("PVE_TOKEN_NAME")
token_secret = os.getenv("PVE_TOKEN_SECRET")
gmail_user = os.getenv("GMAIL_USER")         
gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

if not all([host, user, token_name, token_secret]):
  raise SystemExit("Missing one or more environment variables: PVE_HOST, PVE_USER, PVE_TOKEN_NAME, PVE_TOKEN_SECRET, GMAIL_USER, or GMAIL_APP_PASSWORD")

proxmox = ProxmoxAPI(
  host,
  user=user,
  token_name=token_name,
  token_value=token_secret,
  verify_ssl=False
)

def percentage_used(used, total):
  if not total:
    return None
  return ( used / total ) * 100

def send_alert_email(gmail_user, gmail_app_password, subject, body):
  msg = EmailMessage()
  msg["Subject"] = subject
  msg["From"] = gmail_user
  msg["To"] = gmail_user
  msg.set_content(body)

  with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
    smtp.ehlo()
    smtp.starttls(context=ssl.create_default_context())
    smtp.ehlo()
    smtp.login(gmail_user, gmail_app_password)
    smtp.send_message(msg)


def main():
  nodes = proxmox.nodes.get()
  alerts = []
  for node in nodes:
    node_name = node["node"]
 #--------------------------------VM Section--------------------------------------------
 #--------------------------------------------------------------------------------------
    storages = proxmox.nodes(node_name).storage.get()
    for s in storages:
      storage_name = s.get("storage", "unknown-storage")
      used = s.get("used")
      total = s.get("total")
      pct = percentage_used(used, total)
      if pct is not None:
        pct_floor = math.floor(pct)
        if pct_floor >= 80:
          alerts.append(f"HOST {node_name} storage {storage_name}: {pct_floor}%")
    #--------------------------------VM Section--------------------------------------------
    #--------------------------------------------------------------------------------------
    vms = proxmox.nodes(node_name).qemu.get()
    for vm in vms:
      vm_name = vm.get("name", "unknown")
      vmid = vm.get("vmid")
      agent_net = proxmox.nodes(node_name).qemu(vmid).agent("network-get-interfaces").get()
      ip_list = agent_net[0].get("ip-addresses", [])
      for ip in ip_list:
        ip_addr = ip.get("ip-address")
        if ip_addr == "127.0.0.1":
           continue
        resp = requests.get(f"http://{ip_addr}:9100/metrics")
        lines = resp.text.splitlines()
        size_line = next((l for l in lines if "node_filesystem_size_bytes" in l and 'mountpoint="/"' in l), None)
        size_bytes = int(size_line.split()[-1]) if size_line else None
        avail_line = next((l for l in lines if "node_filesystem_avail_bytes" in l and 'mountpoint="/"' in l), None)
        avail_bytes = int(avail_line.split()[-1]) if avail_line else None
        used_bytes = (size_bytes - avail_bytes) if size_bytes and avail_bytes else None
        disk_pct = percentage_used(used_bytes, size_bytes)
        if disk_pct is not None and disk_pct >= 80:
           alerts.append(f"VM {vm_name} ({ip_addr}) disk usage: {math.floor(disk_pct)}%")
    #---------------------------------Container Section-------------------------------------
    #---------------------------------------------------------------------------------------
    containers = proxmox.nodes(node_name).lxc.get()
    for container in containers:
      cnt_name = container.get("name", "unknown")
      ctid = container.get("vmid")
      interfaces = proxmox.nodes(node_name).lxc(ctid).interfaces.get()
      for iface in interfaces:
        for addr in iface.get("inet", []):
          ip_addr = addr.get("address")
          if ip_addr == "127.0.0.1":
            continue
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
            if disk_pct is not None and disk_pct >= 80:
              alerts.append(f"CT {cnt_name} ({ip_addr}) disk usage: {math.floor(disk_pct)}%")

  if alerts:
    subject = "Proxmox Disk Alert: >= 80%"
    body = "The following systems are above 80 percent disk usage:\n\n" + "\n".join(alerts)
    send_alert_email(gmail_user, gmail_app_password, subject, body)
    print("Alert email sent.")
  else:
    print("No disk alerts.")

if __name__ == "__main__":
  main()