import zipfile
import os

def creat_zip_file_from_directory(path_src, path_dest):
    zf = zipfile.ZipFile(path_dest, 'w', zipfile.ZIP_DEFLATED)
    for root, _, files in os.walk(path_src):
        for f in files:
            zf.write(os.path.join(root, f),
                     os.path.relpath(
                         os.path.join(root, f), path_src))
    zf.close()
