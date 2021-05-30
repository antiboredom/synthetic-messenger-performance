#!/usr/bin/env python3

"""
Manage Synthetic Messenger

Make sure to:

export DIGITALOCEAN_ACCESS_TOKEN="TOKEN"
export SYN_USER="USER"

before running this script

Usage:
  manage_do.py bootup <total>
  manage_do.py deploy
  manage_do.py destroy
  manage_do.py ips
  manage_do.py send <cmd>
  manage_do.py start
  manage_do.py stop
  manage_do.py status
  manage_do.py vnc
  manage_do.py -h | --help

Options:
  bootup <total>    Boot up <total> number of servers
  deploy            Pull newest changes to all servers
  destroy           Destroy all servers
  ips               List all ips
  send <cmd>        Send a command to all servers
  start             Start the zooms and the clicking
  stop              Stop zooming and clicking
  status            Get all servers' status
  vnc               VNC into the first server
  -h --help         Show this screen.
"""

from docopt import docopt
import os
import time
import digitalocean
from pssh.clients import ParallelSSHClient, SSHClient
import click
from subprocess import call


NAME = "synthetic-bot-do"
SIZE = "s-2vcpu-4gb"
REGION = "nyc3"
PERFORMERS = 5
USER = os.getenv("SYN_USER")
with open("key.txt", "r") as infile:
    SERVER_KEY = infile.read().strip()



def get_servers():
    manager = digitalocean.Manager()
    droplets = manager.get_all_droplets()
    droplets = [d for d in droplets if NAME in d.name]
    return droplets


def create_servers(image, size=SIZE, region=REGION, total=PERFORMERS):
    manager = digitalocean.Manager()
    keys = manager.get_all_sshkeys()

    # get the last server number
    servers = get_servers()
    if len(servers) > 0:
        names = [s.name for s in servers]
        nums = sorted([int(n.split("-")[-1]) for n in names], reverse=True)
        start = nums[0] + 1
    else:
        start = 0

    for i in range(start, start + total):
        name = f"{NAME}-{i}"
        droplet = digitalocean.Droplet(
            name=name,
            region=region,
            image=image.id,
            size_slug=size,
            ssh_keys=keys,
            backups=False,
        )
        droplet.create()


def get_image():
    """ Gets the most recent synthetic messenger image"""
    manager = digitalocean.Manager()
    images = manager.get_images(private=True)
    images = [i for i in images if "synthetic" in i.name]
    images = sorted(images, key=lambda k: k.created_at, reverse=True)
    image = images[0]
    return image


def get_sizes():
    manager = digitalocean.Manager()
    sizes = manager.get_all_sizes()
    for s in sizes:
        print(s.slug)


def destroy_servers():
    droplets = get_servers()
    for d in droplets:
        d.destroy()


def get_ips():
    droplets = get_servers()
    return [d.ip_address for d in droplets]


def status():
    """ Print the status of all bot servers """
    servers = get_servers()
    for s in servers:
        print(s.status, s.ip_address)


def send(cmd, user=USER, pause=0):
    droplets = get_servers()
    hosts = [d.ip_address for d in droplets]

    if pause == 0:
        client = ParallelSSHClient(hosts, user=user)
        output = client.run_command(cmd)
        for host_output in output:
            for line in host_output.stdout:
                print(line)
            exit_code = host_output.exit_code
    else:
        for host in hosts:
            client = SSHClient(host, user=user)
            output = client.run_command(cmd)
            for line in output.stdout:
                print(line)
            exit_code = output.exit_code
            time.sleep(pause)


def bootup(total=PERFORMERS):
    image = get_image()
    create_servers(image, total=total)


def deploy():
    send("cd bot;git pull")


def start_bots():
    """ Launch zoom and start clicking """
    send(
        "cd bot; echo '{}' > key.txt; ./joinzoom; DISPLAY=:1 pm2 start ad_clicker.js".format(
            SERVER_KEY
        )
    )


def stop_bots():
    """ Stop zoom and clicking """
    send("pm2 stop ad_clicker; killall zoom; killall node")


def deploy():
    """ Pull latest from github """
    # send("cd bot;git pull;npm install")
    send("cd bot;git pull")


def vnc(ip=None):
    """ VNC into the first server """
    if ip is None:
        ip = get_ips()[0]
    call(["ssh", "-L", "5901:localhost:5901", f"{USER}@{ip}"])


if __name__ == "__main__":
    args = docopt(__doc__)

    if args["bootup"]:
        total = int(args["<total>"])
        bootup(total=total)

    if args["deploy"]:
        deploy()

    if args["destroy"]:
        destroy_servers()

    if args["ips"]:
        for ip in get_ips():
            print(ip)

    if args["status"]:
        status()

    if args["start"]:
        start_bots()

    if args["stop"]:
        stop_bots()

    if args["vnc"]:
        vnc()

    if args["send"]:
        cmd = args["<cmd>"]
        send(cmd)
