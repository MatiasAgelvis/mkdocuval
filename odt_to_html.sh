#!/usr/bin/env bash 

cd "$(dirname "$0")"

python3 docusaurus_nb.py

python3 setup_blog.py

ipython -c "%run to_pdf.ipynb"

# ipython -c "%run separate.ipynb"

# ipython -c "%run pdf_to_html.ipynb"

# ipython -c "%run html_renamer.ipynb"

