#!python
import os
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


class CodeHighlighter(HTMLParser):
    data = ''
    reading_code = False
    code = ''
    lang = ''

    def output(self):
        data = self.data
        self.data = ''
        return data

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.reading_code = True

        if tag == 'code':
            for attr in attrs:
                if attr[0] == 'class':
                    self.lang = attr[1].split(' ')[1]

        if not self.reading_code:
            self.attrs = attrs
            self.data += '<' + tag

            for attr in attrs:
                self.data += ' %s="%s"' % (attr[0], attr[1])

            self.data += '>'

    def handle_data(self, data):
        if self.reading_code:
            self.code += data
        else:
            self.data += data

    def handle_endtag(self, tag):
        if not self.reading_code:
            self.data += '</%s>' % tag

        if tag == 'pre':
            self.reading_code = False
            self.data += highlight(self.code,
                                   get_lexer_by_name(self.lang),
                                   HtmlFormatter(linenos=True))
            self.code = ''
            self.lang = ''


highlighter = CodeHighlighter()

input_ = 'input'
outroot = 'out'
output = 'Files'
templates = 'templates'

shutil.rmtree(outroot, ignore_errors=True)
os.mkdir(outroot)
shutil.copy(templates + '/stylesheet.css', outroot + '/stylesheet.css')
shutil.copy(templates + '/highlight.css', outroot + '/highlight.css')
shutil.copytree(templates + '/mathjax', outroot + '/mathjax')


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
        self.basename = name[:-4]
        self.pdf = self.basename + '.pdf'
        self.html = self.basename + '.html'
        self.path = self.outdir.removeprefix(outroot + '/') + '/' + self.html
        self.pretty_path = self.path.replace('_', ' ').removesuffix('.html')
        self.input_path = root + '/' + name

        self.root_reference = re.sub(r'.+?/', '../', outdir)
        self.root_reference = re.sub(r'/[^\.]+$', '/', self.root_reference)

        # with open(root + '/' + name, 'r') as f:
            # markdowner = markdown2.Markdown(extras=['metadata',
                                                    # 'fenced-code-blocks',
                                                    # 'tables',
                                                    # 'code-friendly'])

            # self.content = markdowner.convert(f.read())

        self.content = subprocess.check_output(['pandoc', '-f', 'latex', '-t', 'html',
                                                '%s/%s' % (root, name)]).decode()

    def expand_html(self):
        title = self.basename.replace('_', ' ')

        expanded = render_template(file_template,
                                   title=title,
                                   path=self.pretty_path,
                                   root=self.root_reference,
                                   pdf=self.pdf,
                                   content=self.content)

        highlighter.feed(expanded)

        return highlighter.output()

    def write_html(self):
        html_content = self.expand_html()

        with open(self.outdir + '/' + self.html, 'w') as f:
            f.write(html_content)

    def write_pdf(self):
        subprocess.run(['latexmk', '-pdf', '-outdir=%s' % self.outdir, self.input_path])

        subprocess.run(['latexmk', '-c', '-outdir=%s' % self.outdir, self.input_path])

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
            if file.endswith('.tex'):
                f = File(root, outdir, file)

                f.write()

                toc += '<li><a href="%s">%s</a></li>' % (f.path, f.pretty_path)

toc += '</ul>'


with open(outroot + '/index.html', 'w') as f:
    f.write(render_template(index_template,
                            toc=toc))
