#!/usr/bin/env python
import os
import shutil
import sys
import getopt
import platform

def copytree(src, dst):
    for item in os.listdir(src):
    
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            os.mkdir(d)
            copytree(s, d)
        else:
            filename, extn = os.path.splitext(item)
            print ("file " + filename + " extn  " + extn)
            if (extn != ".py" and extn != ".png"):
                continue
                
            shutil.copy(s, d)

def make(copyToBlenderAddons = False, createArchive = False):
    blenderHome = None
    platSys = platform.system()
    if platSys == 'Windows':
        appData = os.getenv('APPDATA')
        blenderHome = os.path.join(appData, "Blender Foundation/Blender/2.91")
        
    elif platSys == 'Linux':
        home = os.getenv('HOME')
        blenderHome = os.path.join(home, ".config/blender/2.91/")

    #Create build directory
    curPath = os.getcwd()
    if os.path.exists('build'):
        shutil.rmtree('build')
    os.mkdir('build')
    os.mkdir('build/normalBrush')

    copytree("source", "build/normalBrush");

    
    #Build addon zip file
    if createArchive: 
        if os.path.exists('deploy'):
            shutil.rmtree('deploy')
        os.mkdir('deploy')

        shutil.make_archive("deploy/normalBrush", "zip", "build")


    if copyToBlenderAddons: 
        addonPath = os.path.join(blenderHome, "scripts/addons")
        destPath = os.path.join(addonPath, "normalBrush")

        print("Copying to blender addons: " + addonPath)
        if os.path.exists(destPath):
            shutil.rmtree(destPath)
        copytree("build", addonPath);


if __name__ == '__main__':
    copyToBlenderAddons = False
    createArchive = False

    for arg in sys.argv[1:]:
        if arg == "-a":
            createArchive = True
        if arg == "-b":
            copyToBlenderAddons = True

    make(copyToBlenderAddons, createArchive)
            
