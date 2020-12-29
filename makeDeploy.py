#!/usr/bin/env python
import os
import zipfile

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

if __name__ == '__main__':
    curPath = os.getcwd()
    if not os.path.exists('deploy'):
        os.mkdir('deploy')

    zipf = zipfile.ZipFile('deploy/normalTool.zip', 'w', zipfile.ZIP_DEFLATED)

    zipf.write('__init__.py')
    zipdir('gizmos/', zipf)
    
    zipf.close()
    
    