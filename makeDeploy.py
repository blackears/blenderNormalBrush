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
            #destDir = os.path.join(dst, item)
            os.mkdir(d)
            copytree(s, d)
        else:
            filename, extn = os.path.splitext(item)
            print ("file " + filename + " extn  " + extn)
            if (extn != ".py" and extn != ".png"):
                continue
                
            shutil.copy(s, d)
        
        
#        s = os.path.join("source", item)
#        d = os.path.join("build", item)
 #       if os.path.isdir(s):
  #          shutil.copytree(

if __name__ == '__main__':
    curPath = os.getcwd()
    if os.path.exists('build'):
        shutil.rmtree('build')
    os.mkdir('build')
    
    if os.path.exists('deploy'):
        shutil.rmtree('deploy')
    os.mkdir('deploy')

    copytree("source", "build");

    shutil.make_archive("deploy/normalTool", "zip", "build")

    
#    zipf = zipfile.ZipFile('deploy/normalTool.zip', 'w', zipfile.ZIP_DEFLATED)

#    zipdir('source/', zipf)

#    zipf.write('__init__.py')
#    zipdir('ops/', zipf)
    #zipdir('icons/', zipf)
    
    zipf.close()
    
    