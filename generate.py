#!python
import os
import shutil
from markdown2 import markdown

input_ = 'files'
output = 'out'
templates = 'templates'


def render_template(**kwargs):
    expanded = template[:]

    for var, val in kwargs.items():
        expanded = expanded.replace('${%s}' % var, val)

    return expanded


with open(templates + '/base.html', 'r') as template:
    template = template.read()

for root, dirs, files in os.walk(input_, topdown=True):
    outroot = output + root[len(input_):]

    os.makedirs(outroot, exist_ok=True)

    shutil.copy(templates + '/stylesheet.css', outroot + '/stylesheet.css')

    outfiles = []

    for file in files:
        if file.endswith('.md'):
            basename = file[:-3]
            outfile = outroot + '/' + basename + '.html'
            outfiles.append(basename + '.html')
            infile = root + '/' + file

            with open(infile, 'r') as f:
                content = f.read()

            with open(outfile, 'w') as f:
                content = markdown(content)

                new_file = render_template(title=basename,
                                           content=content)

                f.write(new_file)

    index_html = '<ul>'

    for directory in dirs:
        index_html += '<li><a href="%s">%s</a></li>' % (directory + '/index.html', directory.replace('_', ' '))

    for file in outfiles:
        index_html += '<li><a href="%s">%s</a></li>' % (file, file.removesuffix('.html').replace('_', ' '))

    index_html += '</ul>'

    with open(outroot + '/index.html', 'w') as f:
        f.write(render_template(title=outroot,
                                content=index_html))
