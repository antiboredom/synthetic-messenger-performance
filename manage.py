#!/usr/bin/env python3

"""
Manage Synthetic Messenger

Make sure to:

export HCLOUD_TOKEN="TOKEN"
export SYN_USER="USER"

before running this script

Usage:
  manage.py bootup <total>
  manage.py deploy
  manage.py destroy
  manage.py ips
  manage.py send <cmd>
  manage.py start
  manage.py stop
  manage.py status
  manage.py vnc
  manage.py -h | --help

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
from hcloud import Client
from hcloud.images.domain import Image
from hcloud.server_types.domain import ServerType
from pssh.clients import ParallelSSHClient, SSHClient
from subprocess import call


NAME = "synthetic-bot"
SIZE = "cx21"  # cpx31
PERFORMERS = 5
USER = os.getenv("SYN_USER")
TOKEN = os.getenv("HCLOUD_TOKEN")

with open("key.txt", "r") as infile:
    SERVER_KEY = infile.read().strip()


def get_servers():
    """ Retrieve all servers """
    client = Client(token=TOKEN)
    servers = client.servers.get_all()
    servers = [s for s in servers if NAME in s.name]
    return servers


def status():
    """ Print the status of all bot servers """
    servers = get_servers()
    for s in servers:
        print(s.status, s.public_net.ipv4.ip)


def create_servers(size=SIZE, total=PERFORMERS):
    """create some servers"""

    # get the last server number
    servers = get_servers()
    if len(servers) > 0:
        names = [s.name for s in servers]
        nums = sorted([int(n.split("-")[-1]) for n in names], reverse=True)
        start = nums[0] + 1
    else:
        start = 0

    client = Client(token=TOKEN)
    key = get_key()
    image = get_image()
    st = ServerType(SIZE)

    for i in range(start, start + total):
        name = f"{NAME}-{i}"
        response = client.servers.create(
            name=name, server_type=st, image=image, ssh_keys=[key]
        )
        print(response)


def get_image():
    """ Gets the most recent synthetic messenger image"""
    client = Client(token=TOKEN)
    images = client.images.get_all()
    images = [i for i in images if "synthetic" in i.description]
    return images[-1]


def get_key():
    """ Gets the most recent synthetic messenger image"""
    client = Client(token=TOKEN)
    keys = client.ssh_keys.get_list()
    return keys[0][0]


def destroy_servers():
    """ Destroy all bots """
    servers = get_servers()
    for s in servers:
        s.delete()


def get_ips():
    """ Get all ips """
    servers = get_servers()
    ips = [s.public_net.ipv4.ip for s in servers]
    return ips


def send(cmd, pause=0, user=USER):
    """ Send a command to all bots """
    hosts = get_ips()

    if pause == 0:
        client = ParallelSSHClient(hosts, user=user)
        output = client.run_command(cmd)
        # for host_output in output:
        #     for line in host_output.stdout:
        #         print(line)
        #     exit_code = host_output.exit_code
    else:
        for host in hosts:
            client = SSHClient(host, user=user)
            output = client.run_command(cmd)
            # for line in output.stdout:
            #     print(line)
            # exit_code = output.exit_code
            time.sleep(pause)


def start_bots():
    """ Launch zoom and start clicking """
    send(
        "cd bot; echo '{}' > key.txt; ./joinzoom; DISPLAY=:1 pm2 start ad_clicker.js".format(
            SERVER_KEY
        ),
        pause=0,
    )


def stop_bots():
    """ Stop zoom and clicking """
    send("pm2 stop ad_clicker; killall zoom; killall node")


def deploy():
    """ Pull latest from github """
    # send("cd bot;git pull;npm install")
    send("cd bot;git pull")


def bootup(total=PERFORMERS):
    """ Bootup some bots """
    create_servers(total=total)


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
