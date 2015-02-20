#!/bin/sh
apt-get install lxc aufs-tools
apt-get install linux-image-extra-$(uname -r)

cp ./lxc-wrapper.py /usr/bin/lxc-wrapper
chmod 755 /usr/bin/lxc-wrapper

mkdir -p /var/lib/lxc/images
mkdir -p /var/lib/lxc/templates
