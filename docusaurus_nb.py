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
    return os.path.basename(path.rsplit('.', 1)[0])


# **Convert all odt to docx with pandoc**

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
    # all patterns must match an entire expression and the number, in that order
    name = re.search(r'([a-zA-Z0-9\-]+)', string)[0]
    # matches the infix anotated titles
    pattern_A = r'([\*_]{0,5}%s.*?\((?:[\*_]){0,5}\d{4}(?:\\?-[0-9]{4})?\D*?(?:[\*_]){0,5}\D*?:\D*?(?:[\*_]){0,4}\D*?([0-9]+(?:\s{0,2}\\?(?:-|y|,)\s{0,2}[0-9]+){0,3})\D*?\))' % name
    # matches the postfix anotated titles
    pattern_B = r'([\*_]{0,5}%s(?:.*?\n{0,3}){0,3}[pP]\\?\s{0,3}\.\s{0,3}([0-9]+(?:\\?-[0-9]+){0,3}))' % name
    # matches simple page notation
    pattern_C = r'([\*_]*[pP]\\?\s*\.\s*[\*_]*(\d+).*?)'

    # Special case for WARNOCK file: The text formatting in this file
    # causes false positives with pattern_A and pattern_B due to its unique citation style.
    # When 'WARNOCK' is in the filename, force using pattern_C (simple page number matching)
    # to avoid regex matching issues with the more complex patterns.
    # TODO: Consider updating the name extraction regex to better handle these cases,
    # or create a specific pattern for this citation style.
    if 'WARNOCK'.lower() in name.lower():
        return pattern_C

    if re.search(pattern_A, string):
        return pattern_A
    else:
        return pattern_B


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

    # remove mammoth given headers
    content = re.sub(r'<a.*?><\/a>## (.*)', r'### \1', content)

    # mitigate improperly bolded words
    # starting late
    content = re.sub(r' ([a-zA-Z])__([a-zA-Z]+)', r' __\1\2', content)
    # ending early
    content = re.sub(r'([a-zA-Z]+)__([a-zA-Z]) ', r'\1\2__', content)
    # the colons seem to be annoying the parser
    content = re.sub(r'__:', r':__', content)
    # removes double minus
    content = re.sub(r'(\d)\\-\\-(\d)', r'\1-\2', content)

    # add page titles
    flags = re.IGNORECASE
    pattern = get_regex_pattern(content)
    content = re.sub(pattern, r'\n## \2\n\1', content, flags=flags)

    if 'Warnock' in parent_folder:
        print('\n', parent_folder, ':', re.findall(r'([\*_]*[pP]\\?\s*\.\s*[\*_]*(\d+).*?)', content))
        print('\n', pattern)

    # remove heading white spaces
    # content = content.lstrip()

    # write to a new
    output_path = os.path.dirname(file).replace('_', ' ') + '.md'
    title = os.path.basename(os.path.dirname(file)).replace('_', ' ')
    with open(output_path, 'w+') as output_file:
        output_file.write('# ' + title + '\n\n')
        output_file.write(content)
