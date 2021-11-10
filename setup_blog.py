#!/usr/bin/env python
# coding: utf-8

import glob
import os
import shutil
import docusaurus_config as config
import re
join = os.path.join

IN_path = config.BLOG_IN_path
OUT_path = config.BLOG_OUT_path

os.makedirs(IN_path, exist_ok=True)
os.makedirs(OUT_path, exist_ok=True)


def filename(path):
    return os.path.basename(path.rsplit('.')[0])


for file in glob.glob(join(IN_path, '*', '*.md')):
    with open(file, 'r') as input_file:
        content = input_file.read()

    # change the image paths
    # get parent folder name
    parent_folder = file.split('/')[-2]
    # inline declared images
    content = re.sub(r'(!\[.*?\]\()(.*?)(\))', r'\1{}/\2\3'.format(parent_folder), content)
    # referenced images
    content = re.sub(r'(\[.*\]\s*:\s*)((?:.*?)\.(?:jpg|png))', r'\1{}/\2'.format(parent_folder), content)

    # copy the whole directory to the outpath
    shutil.copytree(IN_path, OUT_path, dirs_exist_ok=True)
    # write to a new file
    output_path = join(OUT_path, os.path.basename(file))
    with open(output_path, 'w+') as output_file:
        output_file.write(content)


# remove duplicates from the image folders
for file in glob.glob(join(OUT_path, '*', '*.md')):
    os.remove(file)
