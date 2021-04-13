#!/bin/bash

# create the user
adduser --disabled-password --gecos "Synthetic" syn

# set the start up script
mkdir -p /home/syn/.config/openbox/
echo "ffmpeg -f x11grab -r 24 -s 1280x720 -i :1.0+0,0 -pix_fmt yuv420p -threads 0 -f v4l2 /dev/video1 &" > /home/syn/.config/openbox/autostart
chown syn:syn /home/syn/.config/
chown -R syn:syn /home/syn/.config/

# copty ssh keys
rsync --archive --chown=syn:syn ~/.ssh /home/syn

# make it sudo
usermod -aG sudo syn

cat <<EOT >> /etc/sudoers
syn ALL=(ALL) NOPASSWD:ALL
EOT

# change ssh settings
cat <<EOT >> /etc/ssh/sshd_config
ChallengeResponseAuthentication no
PasswordAuthentication no
EOT

systemctl restart ssh

# install the stuff
apt update
apt -y install openbox obconf ffmpeg tigervnc-standalone-server tigervnc-common xdg-utils wmctrl xterm git libnss3 xdotool x11-xserver-utils feh
apt -y install linux-headers-$(uname -r)
apt -y install linux-modules-extra-$(uname -r)
apt -y install dkms


# zoom
wget "https://zoom.us/client/latest/zoom_amd64.deb" -O zoom.deb
apt -y install ./zoom.deb

# virtual video
wget "http://deb.debian.org/debian/pool/main/v/v4l2loopback/v4l2loopback-dkms_0.12.5-1_all.deb" -O v4l2loopback-dkms_0.12.5-1_all.deb
dpkg -i v4l2loopback-dkms_0.12.5-1_all.deb

modprobe v4l2loopback exclusive_caps=1 video_nr=1

# start virtual video at boot
echo "v4l2loopback" > /etc/modules-load.d/v4l2loopback.conf

cat > /etc/modprobe.d/v4l2loopback.conf <<EOL
options v4l2loopback exclusive_caps=1
options v4l2loopback video_nr=1
EOL

# install node
curl -fsSL https://deb.nodesource.com/setup_14.x | bash -
apt-get install -y nodejs

# add user to video group
usermod -a -G video syn

# create service for vnc
cat > /etc/systemd/system/vncserver.service <<EOL
[Unit]
Description=Start TigerVNC Server at startup
After=syslog.target network.target

[Service]
Type=forking
User=syn
PAMName=login
PIDFile=/home/syn/.vnc/%H:%i.pid
ExecStartPre=-/usr/bin/vncserver -kill :1 > /dev/null 2>&1
ExecStart=/usr/bin/vncserver :1 -geometry 1280x720
ExecStop=/usr/bin/vncserver -kill :1

[Install]
WantedBy=multi-user.target
EOL

# set a default garbpage password
sudo -H -u syn bash -c 'printf "password\npassword\n\n" | vncpasswd'

# start the vnc service
systemctl enable vncserver.service
systemctl start vncserver.service


# clone the repo and install deps
sudo -H -u syn bash -c 'cd /home/syn/; git clone https://github.com/antiboredom/synthetic-messenger-performance/ bot'
sudo -H -u syn bash -c 'cd /home/syn/bot; npm install'

# ONE MORE THING! you must accept zoom's terms and conditions lol
