This script will monitor the disk usage for my proxmox environment including the host, VMs, and containers.
The script uses the proxmox API and retreives metrics using the Prometheus Node Exporter.

A threshold will be set at 80%. If disk usage exceeds that, an email will automatically be sent to alert me.

The script will run regularly on my raspberry pi via a cron job.
