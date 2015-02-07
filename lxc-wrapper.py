#!/usr/bin/python
import argparse
import os.path
import os
import shutil
import subprocess

#/usr/share/lxc/templates/
LXC_HOME="/var/lib/lxc/"

def createImage(template, image,container):
    if(template!=None):
        createImage_from_template(template, image)
    elif(container!=None):
        createImage_from_container(container, image)

def createImage_from_template(template, image):
    if(image==None):
        image=template
    if(os.path.exists(LXC_HOME+"images/"+image)):
        raise Exception("Already image exists")
    if(os.path.exists(LXC_HOME+image)):
        raise Exception("Already container exists")
    result = ""
    try:
        result = subprocess.check_output(["lxc-create", "-t", template,"-n",image],stderr=subprocess.STDOUT)
    finally:
        print result
    try:
        os.makedirs(LXC_HOME+"images")
    except OSError:
        pass
    shutil.move(LXC_HOME+image, LXC_HOME+"images/"+image)
    #result = subprocess.check_output(["mv","-f", LXC_HOME+image, LXC_HOME+"images/"+image],stderr=subprocess.STDOUT)
    #print result

def createImage_from_container(container, image):
    if(image==None):
        image=container
    if(os.path.exists(LXC_HOME+"images/"+image)):
        raise Exception("Already image exists")
    if(not os.path.exists(LXC_HOME+container)):
        raise Exception("Container does not exist")
    try:
        os.makedirs(LXC_HOME+"images")
    except OSError:
        pass
    #shutil.copytree(LXC_HOME+container, LXC_HOME+"images/"+image)
    try:
        result = subprocess.check_output(["cp","-rpf",LXC_HOME+container, LXC_HOME+"images/"+image],stderr=subprocess.STDOUT)
    finally:
        print result
    #lxc-clone -o ubuntu01 -n ubuntu02
    if(os.path.exists(LXC_HOME+container+"/diff")):
        shutil.rmtree(LXC_HOME+"images/"+image+"/rootfs")
        os.remove(LXC_HOME+"images/"+image+"/fstab")
        for line in open(LXC_HOME+container+"/fstab","r"):
            if(line.startswith("aufs")):#"aufs  "+LXC_HOME+container+"/rootfs       aufs   defaults,br:"+LXC_HOME+container+"/diff:"+LXC_HOME+"images/"+image+"/rootfs=ro 0 0"
                lineTemp=line.split(":")[-1]#LXC_HOME+"images/"+image+"/rootfs=ro 0 0"
                originRoot=lineTemp.split("=")[0]
                shutil.copytree(originRoot, LXC_HOME+"images/"+image+"/rootfs")
                try:
                    result = subprocess.check_output(["mv","-f", LXC_HOME+"images/"+image+"/diff/*", LXC_HOME+"images/"+image+"/rootfs/"],stderr=subprocess.STDOUT)
                finally:
                    print result
                shutil.rmtree(LXC_HOME+"images/"+image+"/diff")
                break

def createContainer(template, image,container):
    if(template!=None):
        if(image==None):
            image=template
        createImage_from_template(template, image)
        createContainer_from_image(image,container)
    else:
        createContainer_from_image(image,container)

def createContainer_from_image(image,container):
    if(os.path.exists(LXC_HOME+container)):
        raise Exception("Already container exists")
    os.makedirs(LXC_HOME+container+"/rootfs")
    os.makedirs(LXC_HOME+container+"/diff/etc")
    createConfigFile(LXC_HOME+"images/"+image+"/config",LXC_HOME+container+"/config",container)
    createFstabFile(image,container)
    createHostname(image,container)

def createConfigFile(origin,newFile,container):
    f = open(newFile, 'w')
    for line in open(origin, 'r'):
        if(line.startswith("lxc.rootfs")):
            f.write("lxc.rootfs = "+LXC_HOME+container+"/rootfs\n")
        elif(line.startswith("lxc.mount")):
            f.write("lxc.mount = "+LXC_HOME+container+"/fstab\n")
        elif(line.startswith("lxc.utsname")):
            f.write("lxc.utsname = "+container+"\n")
        else:
            f.write(line)

def createFstabFile(image,container):
    f = open(LXC_HOME+container+"/fstab", 'w')
    f.write("aufs  "+LXC_HOME+container+"/rootfs       aufs   defaults,br:"+LXC_HOME+container+"/diff:"+LXC_HOME+"images/"+image+"/rootfs=ro 0 0\n")

def createHostname(image,container):
    f = open(LXC_HOME+container+"/diff/etc/hostname", 'w')
    f.write(container+"\n")
    f.close()
    f = open(LXC_HOME+container+"/diff/etc/hosts", 'w')
    f.write("127.0.0.1   localhost\n")
    f.write("127.0.1.1   "+container+"\n")
    f.close()

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', dest='command', action='store_const',const="create image",help='Create image from lxc template or container')
    parser.add_argument('-c', dest='command', action='store_const',const="create container",help='Create container from lxc template or image')
    parser.add_argument('-t', dest='template', help='Set lxc template name',default=None)
    parser.add_argument('-i', dest='image', help='Set image name',default=None)
    parser.add_argument('-n', dest='container', help='Set container name',default=None)
    args = parser.parse_args()
    if(args.command=="create image"):
        createImage(args.template,args.image,args.container)
    if(args.command=="create container"):
        createContainer(args.template,args.image,args.container)
