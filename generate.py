#!python
import os
import re
import shutil
import pdfkit
from markdown2 import markdown

input_ = 'input'
outroot = 'out'
output = 'Files'
templates = 'templates'

shutil.rmtree(outroot, ignore_errors=True)
os.mkdir(outroot)
shutil.copy(templates + '/stylesheet.css', outroot + '/stylesheet.css')


with open(templates + '/file.html', 'r') as template:
    file_template = template.read()

with open(templates + '/index.html', 'r') as template:
    index_template = template.read()


def render_template(template, **kwargs):
    for var, val in kwargs.items():
        template = template.replace('${%s}' % var, val)

    return template


class File:
    def __init__(self, root, outdir, name):
        self.outdir = outdir
        self.basename = name[:-3]
        self.pdf = self.basename + '.pdf'
        self.html = self.basename + '.html'
        self.path = self.outdir.removeprefix(outroot + '/') + '/' + self.html
        self.pretty_path = self.path.replace('_', ' ').removesuffix('.html')

        self.root_reference = re.sub(r'.+?/', '../', outdir)
        self.root_reference = re.sub(r'/[^\.]+$', '/', self.root_reference)

        with open(root + '/' + name, 'r') as f:
            self.content = markdown(f.read())

    def expand_html(self):
        title = self.basename.replace('_', ' ')

        return render_template(file_template,
                               title=title,
                               path=self.pretty_path,
                               root=self.root_reference,
                               pdf=self.pdf,
                               content=self.content)

    def write_html(self):
        html_content = self.expand_html()

        with open(self.outdir + '/' + self.html, 'w') as f:
            f.write(html_content)

    def write_pdf(self):
        content = self.content

        # Extra style for PDF
        content += """
        <style>
            body {
                text-align: justify;
            }
        </style>
        """

        pdfkit.from_string(content, self.outdir + '/' + self.pdf)

    def write(self):
        self.write_html()
        self.write_pdf()


toc = '<ul>'

for root, dirs, files in os.walk(input_, topdown=True):
    outdir = outroot + '/' + output + root[len(input_):]

    os.makedirs(outdir, exist_ok=True)

    outfiles = []

    if len(files) or len(dirs):
        for file in files:
            if file.endswith('.md'):
                f = File(root, outdir, file)

                f.write()

                toc += '<li><a href="%s">%s</a></li>' % (f.path, f.pretty_path)

toc += '</ul>'


with open(outroot + '/index.html', 'w') as f:
    f.write(render_template(index_template,
                            toc=toc))
