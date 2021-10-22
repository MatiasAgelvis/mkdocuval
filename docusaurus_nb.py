#!/usr/bin/env python
# coding: utf-8

import glob
import os
import pypandoc
import docusaurus_config as config
import re
import subprocess
join = os.path.join

ODT_path = config.ODT_path
DOCX_path = config.DOCX_path
PDF_path = config.PDF_path
MD_path = config.MD_path

os.makedirs(ODT_path, exist_ok=True)
os.makedirs(DOCX_path, exist_ok=True)
os.makedirs(PDF_path, exist_ok=True)
os.makedirs(MD_path, exist_ok=True)


def filename(path):
    return os.path.basename(path.rsplit('.')[0])


# **Convert all odt to docxwith pandoc**

for file in glob.glob(join(ODT_path, '*')):
    outfile = join(DOCX_path, filename(file) + '.docx')
    pypandoc.convert_file(file, 'docx', outputfile=outfile)


# **Convert all docx to md with mammoth**

def exclamation(command):
    return subprocess.run(command, check=True, text=True, shell=True)


for file in glob.glob(join(DOCX_path, '*')):
    out_dir = join(MD_path, filename(file).replace(' ', '_'))
    os.makedirs(out_dir, exist_ok=True)

    exclamation("mammoth --output-format=markdown '{file}' \
                 --output-dir='{out_dir}'".format(file=file, out_dir=out_dir))
    print(out_dir)


# * **copy the html file from each folder**
# * **change the image paths**
# * **add page titles**
# * **write to a new file at parent folder**

def get_regex_pattern(string):
    name = re.search(r'([\w\-]+)', string)[0]
    pattern_A = r'([\*_]{0,5}%s.*?\(\d{4}(?:\\?-[0-9]{4})?\D*?(?:[\*_]){0,2}\D*?:\D*?(?:[\*_]){0,2}\D*?([0-9]+(?:\s{0,2}(?:\\-|y|,)\s{0,2}[0-9]+){0,3})\D*?\))' % name
    pattern_B = r'([\*_]{0,5}%s(?:.*?\n{0,3}){0,3}[pP]\\?\s{0,3}\.\s{0,3}([0-9]+(?:\\-[0-9]+){0,3}))' % name
    
    return pattern_A if re.search(pattern_A, string) else pattern_B


# for some reason when mammoth exports md to a directory
# it writes it to a html
# copy the html file from each folder
for file in glob.glob(join(MD_path, '*', '*.html')):
    with open(file, 'r') as input_file:
        content = input_file.read()

    # change the image paths
    # get parent folder name
    parent_folder = file.split('/')[-2]
    content = re.sub(r'(!\[.*?\]\()(.*?)(\))', r'\1{}/\2\3'.format(parent_folder), content)
    
    # add page titles
    flags = re.IGNORECASE
    pattern = get_regex_pattern(content)
    content = re.sub(pattern, r'\n## \2\n\1', content, flags=flags)
    # remove heading white spaces
    # content = content.lstrip()
    
    # write to a new 
    output_path = os.path.dirname(file).replace('_', ' ') + '.md'
    title = os.path.basename(os.path.dirname(file)).replace('_', ' ')
    with open(output_path, 'w+') as output_file:
        output_file.write('# ' + title + '\n\n')
        output_file.write(content)

