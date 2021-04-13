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
  manage.py vnc
  manage.py send <cmd>
  manage.py -h | --help

Options:
  -h --help     Show this screen.
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


def get_servers():
    client = Client(token=TOKEN)
    servers = client.servers.get_all()
    servers = [s for s in servers if NAME in s.name]
    return servers


def create_servers(size=SIZE, total=PERFORMERS):
    """create some servers"""

    # get the last server number
    servers = get_servers()
    names = [s.name for s in servers]
    nums = sorted([int(n.split("-")[-1]) for n in names], reverse=True)
    start = nums[0] + 1

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
    servers = get_servers()
    for s in servers:
        s.delete()


def get_ips():
    servers = get_servers()
    ips = [s.public_net.ipv4.ip for s in servers]
    return ips


def send(cmd, pause=0, user=USER):
    hosts = get_ips()

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
    create_servers(total=total)


def deploy():
    send("cd bot;git pull")


def vnc(ip=None):
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

    if args["vnc"]:
        vnc()

    if args["send"]:
        cmd = args["<cmd>"]
        send(cmd)

    # get_keys()
    # bootup()
    # start()
    # send("cd bot; ./joinzoom 94682594244", pause=20)
    # print(USER)
    # destroy_servers()
