# lxc-wrapper

lxc-wrapper is a aufs wrapper for lxc on Ubuntu.

# Install

```
git clone https://github.com/ccat/lxc-wrapper.git
cd lxc-wrapper
./install.sh
```

# Usage

## Create image

```
lxc-wrapper -m -i <IMAGE NAME> -t <LXC TEMPLATE NAME>
```

## Create container

```
lxc-wrapper -c -i <IMAGE NAME> -n <CONTAINER NAME>
```
