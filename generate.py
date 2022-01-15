#!python
import os
import shutil
from markdown2 import markdown

input_ = 'input_files'
output = 'Files'
templates = 'templates'


def render_template(template, **kwargs):
    expanded = template[:]

    for var, val in kwargs.items():
        expanded = expanded.replace('${%s}' % var, val)

    return expanded


with open(templates + '/file.html', 'r') as template:
    file_template = template.read()

with open(templates + '/dir.html', 'r') as template:
    dir_template = template.read()

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

                pretty_name = basename.replace('_', ' ')

                new_file = render_template(file_template,
                                           title=pretty_name,
                                           path=outroot.replace('_', ' ') + '/' + pretty_name,
                                           content=content)

                f.write(new_file)

    index_html = '<ul>'

    for directory in dirs:
        index_html += '<li><a href="%s">%s/</a></li>' % (directory + '/index.html', directory.replace('_', ' '))

    for file in outfiles:
        index_html += '<li><a href="%s">%s</a></li>' % (file, file.removesuffix('.html').replace('_', ' '))

    index_html += '</ul>'

    with open(outroot + '/index.html', 'w') as f:
        pretty_outroot = outroot.replace('_', ' ')

        f.write(render_template(dir_template,
                                title=pretty_outroot,
                                path=pretty_outroot,
                                content=index_html))
