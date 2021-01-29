#!/usr/bin/env python
import os
import glob
import shutil
import zipfile

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

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

if __name__ == '__main__':
    curPath = os.getcwd()
    if os.path.exists('build'):
        shutil.rmtree('build')
    os.mkdir('build')
    os.mkdir('build/normalTools')
    
    if os.path.exists('deploy'):
        shutil.rmtree('deploy')
    os.mkdir('deploy')

    copytree("source", "build/normalTools");

    shutil.make_archive("deploy/normalTools", "zip", "build")

    
