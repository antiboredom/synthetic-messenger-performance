#!/bin/bash

# install the stuff
apt update
apt -y install wmctrl  xdotool

# install node
curl -fsSL https://deb.nodesource.com/setup_14.x | bash -
apt-get install -y nodejs

# clone the repo and install deps
cd /home/pi
git clone https://github.com/antiboredom/synthetic-messenger-performance/ bot

cd /home/pi/bot
npm install

# install pm2
npm install -g pm2
