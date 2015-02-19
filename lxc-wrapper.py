#!/usr/bin/python
import argparse
import os.path
import os
import shutil
import subprocess
import urllib2
import time
import json

LXC_HOME="/var/lib/lxc/"
LXC_TEMPLATE_FOLDER="/usr/share/lxc/templates/"
LXC_TEMPLATE_LIBRARY="http://library.lxc-wrapper.whiteblack-cat.info/"
LXC_WRAPPER_IMAGE=LXC_HOME+"images/"
LXC_WRAPPER_TEMPLATE=LXC_HOME+"templates/"

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
    if(result == "lxc-started"):
        try:
            result = subprocess.check_output(["lxc-attach", "-n",image,"--","shutdown","-h","now"],stderr=subprocess.STDOUT)
        except:
            pass
        print result
    #try:
    #    os.makedirs(LXC_WRAPPER_IMAGE)
    #except OSError:
    #    pass
    shutil.move(LXC_HOME+image, LXC_WRAPPER_IMAGE+image)
    #result = subprocess.check_output(["mv","-f", LXC_HOME+image, LXC_HOME+"images/"+image],stderr=subprocess.STDOUT)
    #print result

def create_template(template,image):
    lxcStartFlag=False
    if(os.path.exists(LXC_TEMPLATE_FOLDER+"lxc-"+template)):
        result=""
        try:
            result = subprocess.check_output(["lxc-create", "-t", template,"-n",image],stderr=subprocess.STDOUT)
        finally:
            print result
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
                    result = subprocess.check_output(["lxc-start", "-d" ,"-n",image],stderr=subprocess.STDOUT)
                    print result
                    time.sleep(10)
                    lxcStartFlag=True
                elif(result == "lxc-started"):
                    lxcStartFlag=True
            commands=vals["template"]
            for item in commands.split("\n"):
                print item
                itemList = item.split(" ")
                tempCommand = ["lxc-attach", "-n",image,"--"]
                tempCommand.extend(itemList)
                result = subprocess.check_output(tempCommand,stderr=subprocess.STDOUT)
                print result
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
            return create_template(template,image)

def createImage_from_container(container, image):
    if(image==None):
        image=container
    if(os.path.exists(LXC_WRAPPER_IMAGE+image)):
        raise Exception("Already image exists")
    if(not os.path.exists(LXC_HOME+container)):
        raise Exception("Container does not exist")
    #try:
    #    os.makedirs(LXC_WRAPPER_IMAGE)
    #except OSError:
    #    pass
    #shutil.copytree(LXC_HOME+container, LXC_HOME+"images/"+image)
    try:
        result = subprocess.check_output(["cp","-rpf",LXC_HOME+container, LXC_WRAPPER_IMAGE+image],stderr=subprocess.STDOUT)
    finally:
        print result
    #lxc-clone -o ubuntu01 -n ubuntu02
    if(os.path.exists(LXC_HOME+container+"/diff")):
        shutil.rmtree(LXC_WRAPPER_IMAGE+image+"/rootfs")
        os.remove(LXC_WRAPPER_IMAGE+image+"/fstab")
        for line in open(LXC_HOME+container+"/fstab","r"):
            if(line.startswith("aufs")):#"aufs  "+LXC_HOME+container+"/rootfs       aufs   defaults,br:"+LXC_HOME+container+"/diff:"+LXC_HOME+"images/"+image+"/rootfs=ro 0 0"
                lineTemp=line.split(":")[-1]#LXC_HOME+"images/"+image+"/rootfs=ro 0 0"
                originRoot=lineTemp.split("=")[0]
                #shutil.copytree(originRoot, LXC_WRAPPER_IMAGE+image+"/rootfs")
                result = subprocess.check_output(["cp","-rpf",originRoot, LXC_WRAPPER_IMAGE+image+"/rootfs"],stderr=subprocess.STDOUT)
                print result
                try:
                    result = subprocess.check_output(["cp","-rpf", LXC_HOME+"images/"+image+"/diff/.", LXC_WRAPPER_IMAGE+image+"/rootfs/"],stderr=subprocess.STDOUT)
                finally:
                    print result
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
    os.makedirs(LXC_HOME+container+"/diff/etc")
    createConfigFile(LXC_WRAPPER_IMAGE+image+"/config",LXC_HOME+container+"/config",container)
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
    f.write("aufs  "+LXC_HOME+container+"/rootfs       aufs   defaults,br:"+LXC_HOME+container+"/diff:"+LXC_WRAPPER_IMAGE+image+"/rootfs=ro 0 0\n")

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
