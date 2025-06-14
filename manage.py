#!/usr/bin/env -S uv run --script

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
  manage.py record
  manage.py stop_record
  manage.py combine_record
  manage.py count_recordings
  manage.py download
  manage.py start
  manage.py stop
  manage.py status
  manage.py vnc
  manage.py showimage
  manage.py -h | --help

Options:
  bootup <total>    Boot up <total> number of servers
  deploy            Pull newest changes to all servers
  destroy           Destroy all servers
  ips               List all ips
  send <cmd>        Send a command to all servers
  record            Record the bots
  stop_record       Stop record bots
  combine_record    Combine recorded videos
  count_recordings  Count recordings on all hosts
  download          Download recordings
  start             Start the zooms and the clicking
  stop              Stop zooming and clicking
  status            Get all servers' status
  vnc               VNC into the first server
  showimage         Show which image we're using
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
from functools import lru_cache
from gevent import joinall

NAME = "synthetic-bot"
# SIZE = "cx21"  # cpx31
# SIZE = "ccx11"  # cpx31
# SIZE = "ccx21"  # cpx31
# SIZE = "cx51"  # cpx31
SIZE = "cpx51"  # cpx31
PERFORMERS = 5
USER = os.getenv("SYN_USER")
TOKEN = os.getenv("HCLOUD_TOKEN")

with open("key.txt", "r") as infile:
    SERVER_KEY = infile.read().strip()


@lru_cache
def get_servers():
    """Retrieve all servers"""
    client = Client(token=TOKEN)
    servers = client.servers.get_all()
    servers = [s for s in servers if NAME in s.name]
    return servers


def status():
    """Print the status of all bot servers"""
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
    """Gets the most recent synthetic messenger image"""
    client = Client(token=TOKEN)
    images = client.images.get_all()
    images = [i for i in images if "synthetic" in i.description]
    return images[-1]


def get_key():
    """Gets the most recent synthetic messenger image"""
    client = Client(token=TOKEN)
    keys = client.ssh_keys.get_list()
    return keys[0][0]


def destroy_servers():
    """Destroy all bots"""
    servers = get_servers()
    for s in servers:
        s.delete()


def get_ips():
    """Get all ips"""
    servers = get_servers()
    ips = [s.public_net.ipv4.ip for s in servers]
    return ips


def send(cmd, pause=0, user=USER):
    """Send a command to all bots"""
    hosts = get_ips()

    if pause == 0:
        client = ParallelSSHClient(hosts, user=user)
        output = client.run_command(cmd, stop_on_errors=True)
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


def count_recordings():
    hosts = get_ips()
    client = ParallelSSHClient(hosts, user=USER)
    output = client.run_command(f"ls /home/{USER}/bot/recordings/*.mkv | wc -l")
    for host_output in output:
        for line in host_output.stdout:
            print(line)


def start_bots():
    """Launch zoom and start clicking"""
    send(
        "cd bot; echo '{}' > key.txt; ./joinzoom; DISPLAY=:1 pm2 start ad_clicker.js".format(
            SERVER_KEY
        ),
        pause=0,
    )


def record_bots():
    """Launch bot and record output"""

    # UNUSED!
    # WIDTH = 1280
    # HEIGHT = 720
    # WIDTH = 1536
    # HEIGHT = 864

    # for desktop
    WIDTH = 1406
    HEIGHT = 792

    # for mobile
    # too big still!!!
    WIDTH = 792
    HEIGHT = 1406

    WIDTH = 400
    HEIGHT = 800

    print("killing vnc")
    send("vncserver -kill :1")

    print("starting vnc")
    send(f"vncserver :1 -geometry {WIDTH}x{HEIGHT}")

    print("killing ffmpg")
    send("killall ffmpeg")

    print("minimizing window")
    send('DISPLAY=:1 xdotool search --name "VNC config" windowminimize')

    print("moving mouse")
    send(f"DISPLAY=:1 xdotool mousemove {WIDTH} {HEIGHT}")

    # ffmpeg_command = "killall -9 ffmpeg; ffmpeg -y -f x11grab -r 25 -s 1280x720 -i :1.0+0,0 -threads 0 -f pulse -ac 2 -i default recording.mkv"

    # small file, big cpu
    # ffmpeg_command = f"killall -9 ffmpeg; ffmpeg -y  -f pulse -ac 2 -i default -video_size {WIDTH}x{HEIGHT} -framerate 60 -f x11grab -i :1.0+0,0 -vcodec libx264 -pix_fmt yuv420p -preset veryfast -crf 15 -threads 0 recording.mkv"

    # big file, small cpu
    # ffmpeg_command = f"killall -9 ffmpeg; ffmpeg -y  -f pulse -ac 2 -i default -video_size {WIDTH}x{HEIGHT} -framerate 25 -f x11grab -i :1.0+0,0 -vcodec libx264 -pix_fmt yuv420p -preset ultrafast -crf 0 -threads 0 recording.mkv"
    # send(ffmpeg_command, pause=0)

    print("start pm2 and record")
    start_command = f"cd bot; echo '{SERVER_KEY}' > key.txt; DISPLAY=:1 WIDTH={WIDTH} HEIGHT={HEIGHT} pm2 start ad_clicker_record.js"
    send(start_command, pause=0)


def stop_record():
    send("pm2 stop ad_clicker_record; killall zoom; killall node; killall ffmpeg")


def combine_recordings():
    send("""printf "file '%s'\n" bot/recordings/*.mkv > vidlist.txt""")
    send("ffmpeg -y -f concat -safe 0 -i vidlist.txt -c copy recording.mkv")


def download_recordings():
    hosts = get_ips()

    client = ParallelSSHClient(hosts, user=USER)

    filename = "/Users/sam/projects/synthetic-messenger-performance/saved_recordings/recording.mp4"
    cmds = client.copy_remote_file(f"/home/{USER}/recording.mp4", filename)
    joinall(cmds, raise_error=True)

    # for h in hosts:
    #     client = SSHClient(h, user=USER)
    #     output = client.run_command("hostname")
    #     hostname = "".join(output.stdout).strip()
    #     filename = f"/Users/sam/projects/synthetic-messenger-performance/saved_recordings/{hostname}.mp4"
    #
    #     print(filename)
    #     if os.path.exists(filename):
    #         continue
    #     client.copy_remote_file(f"/home/{USER}/recording.mp4", filename)


def stop_bots():
    """Stop zoom and clicking"""
    send("pm2 stop ad_clicker; killall zoom; killall node")


def deploy():
    """Pull latest from github"""
    # send("cd bot;git pull;npm install")
    send("cd bot;git pull")


def bootup(total=PERFORMERS):
    """Bootup some bots"""
    create_servers(total=total)


def vnc(ip=None):
    """VNC into the first server"""
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

    if args["record"]:
        record_bots()

    if args["stop_record"]:
        stop_record()

    if args["count_recordings"]:
        count_recordings()

    if args["combine_record"]:
        combine_recordings()

    if args["download"]:
        download_recordings()

    if args["stop"]:
        stop_bots()

    if args["vnc"]:
        vnc()

    if args["showimage"]:
        image = get_image()
        print("ID:", image.id)

    if args["send"]:
        cmd = args["<cmd>"]
        send(cmd)
