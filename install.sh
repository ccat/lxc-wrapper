#!/bin/sh
apt-get install lxc aufs-tools
apt-get install linux-image-extra-$(uname -r)

cp ./lxc-wrapper.py /usr/bin/lxc-warpper
chmod 755 /usr/bin/lxc-warpper
