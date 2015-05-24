#!/usr/bin/python
import argparse
import os.path
import os
import shutil
import subprocess
import urllib2
import time
import json
import random

LXC_HOME="/var/lib/lxc/"
LXC_TEMPLATE_FOLDER="/usr/share/lxc/templates/"
LXC_TEMPLATE_LIBRARY="http://library.lxc-wrapper.whiteblack-cat.info/"
LXC_WRAPPER_IMAGE=LXC_HOME+"images/"
LXC_WRAPPER_TEMPLATE=LXC_HOME+"templates/"

def showImage():
    subprocess.call(["ls", LXC_WRAPPER_IMAGE])

def createImage(template, image,container):
    if(template!=None):
        createImage_from_template(template, image)
    elif(container!=None):
        createImage_from_container(container, image)

def createImage_from_template(template, image):
    if(image==None):
        image=template
    if(os.path.exists(LXC_WRAPPER_IMAGE+image)):
        raise Exception("Already image exists")
    if(os.path.exists(LXC_HOME+image)):
        raise Exception("Already container exists")

    result = create_template(template,image)
    print "Template container configured"
    if(result == "lxc-started"):
        result = subprocess.call(["lxc-attach", "-n",image,"--","shutdown","-h","now"])
        if(result!=0):
            raise Exception("Failed to shutdown image container: "+image+", returncode:"+str(result))
    #try:
    #    os.makedirs(LXC_WRAPPER_IMAGE)
    #except OSError:
    #    pass
    shutil.move(LXC_HOME+image, LXC_WRAPPER_IMAGE+image)
    print "Template container converted to image"
    #result = subprocess.check_output(["mv","-f", LXC_HOME+image, LXC_HOME+"images/"+image],stderr=subprocess.STDOUT)
    #print result

def create_template(template,image):
    lxcStartFlag=False
    if(os.path.exists(LXC_TEMPLATE_FOLDER+"lxc-"+template)):
        result = subprocess.call(["lxc-create", "-t", template,"-n",image])
        if(result!=0):
            raise Exception("Failed to create container: "+image+", returncode:"+str(result))
        print "Template lxc container created"
        return "lxc-template"
    else:
        if(os.path.exists(LXC_WRAPPER_TEMPLATE+template)):
            f = open(LXC_WRAPPER_TEMPLATE+template,"r")
            dat = f.read()
            f.close()
            vals = json.loads(dat)
            if(vals["depend"]):
                result = create_template(vals["depend"],image)
                if(result == "lxc-template"):
                    result = subprocess.call(["lxc-start", "-d" ,"-n",image])
                    if(result!=0):
                        raise Exception("Failed to start container: "+image+", returncode:"+str(result))
                    time.sleep(10)
                    print "Template lxc container started"
                    lxcStartFlag=True
                elif(result == "lxc-started"):
                    lxcStartFlag=True
            commands=vals["template"]
            for item in commands.split("\n"):
                if(item==""):
                    continue
                #itemList = item.split(" ")
                #tempCommand = ["lxc-attach", "-n",image,"--"]
                #tempCommand.extend(itemList)
                tempCommand = "lxc-attach -n "+image+" -- "+item
                result = subprocess.call(tempCommand,shell=True)
                if(result!=0):
                    raise Exception("Failed to execute: '"+item+"' on: "+image+", returncode:"+str(result))
            if(lxcStartFlag):
                return "lxc-started"
        else:
            response = urllib2.urlopen(LXC_TEMPLATE_LIBRARY+template)
            html = response.read()
            tempVal = json.loads(html)
            if(tempVal["type"]=="lxc-attach"):
                f = open(LXC_WRAPPER_TEMPLATE+template,"w")
                f.write(html)
                f.close()
            elif(tempVal["type"]=="lxc-template"):
                f = open(LXC_TEMPLATE_FOLDER+"lxc-"+template,"w")
                f.write(tempVal["template"])
                f.close()
            print "Template file downloaded"
            return create_template(template,image)

def createImage_from_container(container, image):
    if(image==None):
        image=container
    if(os.path.exists(LXC_WRAPPER_IMAGE+image)):
        raise Exception("Already image exists: "+image)
    if(not os.path.exists(LXC_HOME+container)):
        raise Exception("Container does not exist: "+container)
    #try:
    #    os.makedirs(LXC_WRAPPER_IMAGE)
    #except OSError:
    #    pass
    #shutil.copytree(LXC_HOME+container, LXC_HOME+"images/"+image)
    print "Copying container to image"
    result = subprocess.call(["cp","-rpf",LXC_HOME+container, LXC_WRAPPER_IMAGE+image])
    if(result!=0):
        raise Exception("Failed to copy container: "+container+" to image: "+image+", returncode:"+str(result))
    #lxc-clone -o ubuntu01 -n ubuntu02
    if(os.path.exists(LXC_HOME+container+"/diff")):
        shutil.rmtree(LXC_WRAPPER_IMAGE+image+"/rootfs")
        os.remove(LXC_WRAPPER_IMAGE+image+"/fstab")
        for line in open(LXC_HOME+container+"/fstab","r"):
            if(line.startswith("aufs")):#"aufs  "+LXC_HOME+container+"/rootfs       aufs   defaults,br:"+LXC_HOME+container+"/diff:"+LXC_HOME+"images/"+image+"/rootfs=ro 0 0"
                lineTemp=line.split(":")[-1]#LXC_HOME+"images/"+image+"/rootfs=ro 0 0"
                originRoot=lineTemp.split("=")[0]
                #shutil.copytree(originRoot, LXC_WRAPPER_IMAGE+image+"/rootfs")
                print "Copying container rootfs to image"
                result = subprocess.call(["cp","-rpf",originRoot, LXC_WRAPPER_IMAGE+image+"/rootfs"])
                if(result!=0):
                    raise Exception("Failed to copy rootfs: "+originRoot+" to image: "+LXC_WRAPPER_IMAGE+image+"/rootfs, returncode:"+str(result))
                print "Copying container diff to image"
                result = subprocess.call(["cp","-rpf", LXC_HOME+"images/"+image+"/diff/.", LXC_WRAPPER_IMAGE+image+"/rootfs/"])
                if(result!=0):
                    raise Exception("Failed to copy diff: "+LXC_HOME+"images/"+image+"/diff/."+" to rootfs: "+LXC_WRAPPER_IMAGE+image+"/rootfs, returncode:"+str(result))
                shutil.rmtree(LXC_WRAPPER_IMAGE+image+"/diff")
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
    print "rootfs dir created"
    os.makedirs(LXC_HOME+container+"/diff/etc")
    print "diff dir created"
    createConfigFile(LXC_WRAPPER_IMAGE+image+"/config",LXC_HOME+container+"/config",container)
    print "config file created"
    createFstabFile(image,container)
    print "fstab created"
    createHostname(image,container)
    print "hostname changed"

def createConfigFile(origin,newFile,container):
    f = open(newFile, 'w')
    for line in open(origin, 'r'):
        if(line.startswith("lxc.rootfs")):
            f.write("lxc.rootfs = "+LXC_HOME+container+"/rootfs\n")
        elif(line.startswith("lxc.mount")):
            f.write("lxc.mount = "+LXC_HOME+container+"/fstab\n")
        elif(line.startswith("lxc.utsname")):
            f.write("lxc.utsname = "+container+"\n")
        elif(line.startswith("lxc.network.hwaddr")):
            macAddr = generateNewMACaddress()
            f.write("lxc.network.hwaddr = "+macAddr+"\n")
            #f.flush()
        else:
            f.write(line)
    f.close()

def createFstabFile(image,container):
    f = open(LXC_HOME+container+"/fstab", 'w')
    f.write("aufs  "+LXC_HOME+container+"/rootfs       aufs   defaults,br:"+LXC_HOME+container+"/diff:"+LXC_WRAPPER_IMAGE+image+"/rootfs=ro 0 0\n")

def createHostname(image,container):
    f = open(LXC_HOME+container+"/diff/etc/hostname", 'w')
    f.write(container+"\n")
    f.close()
    f = open(LXC_HOME+container+"/diff/etc/hosts", 'w')
    f.write("127.0.0.1   localhost\n")
    f.write("127.0.1.1   "+container+"\n")
    f.close()

def generateNewMACaddress():
    macAddrList = ["00:16:3e:00:00:00","00:16:3e:ff:ff:ff"]
    result = subprocess.check_output("grep hwaddr "+LXC_HOME+"*/config",shell=True)
    tempList = result.split("\n")
    for item in tempList:
        if("=" in item):
            tempMACaddr = item.split("=")[1].strip()
            macAddrList.append(tempMACaddr)
    newMACaddr = "00:16:3e:00:00:00"
    randomSource = "0123456789abcdef"
    while newMACaddr in macAddrList:
        newMACaddr = "00:16:3e"
        for i in range(1,4):
            newMACaddr += ":"
            newMACaddr += random.choice(randomSource)
            newMACaddr += random.choice(randomSource)
    return newMACaddr



if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', dest='command', action='store_const',const="create image",help='Create image from lxc template or container')
    parser.add_argument('-c', dest='command', action='store_const',const="create container",help='Create container from lxc template or image')
    parser.add_argument('-l', dest='command', action='store_const',const="show image",help='Show image list')
    parser.add_argument('-t', dest='template', help='Set lxc template name',default=None)
    parser.add_argument('-i', dest='image', help='Set image name',default=None)
    parser.add_argument('-n', dest='container', help='Set container name',default=None)
    args = parser.parse_args()
    try:
        if(args.command=="create image"):
            createImage(args.template,args.image,args.container)
        if(args.command=="create container"):
            createContainer(args.template,args.image,args.container)
        if(args.command=="show image"):
            showImage()
    except Exception as e:
        print e.messages
