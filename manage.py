import os
import digitalocean

NAME = "synthetic-bot"
SIZE = "s-2vcpu-4gb"
REGION = "nyc2"
PERFORMERS = 5


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
            image=image,
            size_slug=size,
            ssh_keys=keys,
            backups=False,
        )


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


def start():
    image = get_image()
    create_servers(image, total=5)


if __name__ == "__main__":
    start()
