"""
Managers the server farm
Make sure to run export:

export DIGITALOCEAN_ACCESS_TOKEN="TOKEN"

and

export SYN_USER="USER"

before running this script
"""

import os
import time
import digitalocean
from pssh.clients import ParallelSSHClient, SSHClient
import click


NAME = "synthetic-bot"
SIZE = "s-2vcpu-4gb"
REGION = "nyc1"
PERFORMERS = 5
USER = os.getenv("SYN_USER")


@click.group()
def cli():
    pass


def get_servers():
    manager = digitalocean.Manager()
    droplets = manager.get_all_droplets()
    droplets = [d for d in droplets if NAME in d.name]
    return droplets


def create_servers(image, size=SIZE, region=REGION, total=PERFORMERS):
    manager = digitalocean.Manager()
    keys = manager.get_all_sshkeys()

    for i in range(total):
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


@click.command(name="destroy", help="Destroy all servers")
def destroy_servers():
    droplets = get_servers()
    for d in droplets:
        d.destroy()


@click.command(name="ips", help="Print server ip addresses")
def print_servers():
    droplets = get_servers()
    for d in droplets:
        print(d.ip_address)


@click.command(name="send", help="Send a command to all servers")
@click.argument("cmd", required=True)
@click.option(
    "--pause",
    "-p",
    default=0,
    type=int,
    help="Pause in seconds between sending to each server",
)
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


@click.command(name="bootup", help="Boot up servers")
@click.option(
    "--total",
    "-t",
    type=int,
    required=True,
    default=PERFORMERS,
    help="Total servers to boot up",
)
def bootup(total=PERFORMERS):
    image = get_image()
    create_servers(image, total=total)


cli.add_command(bootup)
cli.add_command(send)
cli.add_command(print_servers)
cli.add_command(destroy_servers)

if __name__ == "__main__":
    cli()
    # bootup()
    # start()
    # send("cd bot; ./joinzoom 94682594244", pause=20)
    # print(USER)
    # destroy_servers()
