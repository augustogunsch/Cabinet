#!/bin/env python3.9
from subprocess import run
from datetime import date
from os import makedirs, environ
from os.path import relpath
from re import findall
from glob import glob
from pathlib import Path
from sys import argv, stderr
from shutil import copy, copytree, rmtree
from html.parser import HTMLParser
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

base_author = 'Augusto Gunsch'

input_root = Path('input')
output_root = Path('output')
file_output_root = output_root / Path('files')
templates_root = Path('templates')
static_root = Path('static')

if len(argv) > 1 and 'clean' not in argv:
    print('usage: {} [clean]'.format(argv[0]), file=stderr)
    exit(1)

if 'clean' in argv:
    print('Cleaning output root')
    rmtree(output_root, ignore_errors=True)

templates = {}
for template in templates_root.glob('*.html'):
    templates[template.stem] = template.read_text()


def render_template(template, **kwargs):
    for var, val in kwargs.items():
        template = template.replace('${%s}' % var, str(val))

    return template


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


class TeXFile:
    def extract_tex_metadata(self):
        m = findall(r'\\usepackage\[(.*)\]\{babel\}', self.raw_content)
        self.lang = m[0] if m else 'english'

        m = findall(r'\\title\{(.*)\}', self.raw_content)
        self.title = m[0] if m else self.input_file.stem.replace('_', ' ')

        m = findall(r'\\author\{(.*)\}', self.raw_content)
        self.author = m[0] if m else base_author

        m = findall(r'\\date\{(.*)\}', self.raw_content)
        self.date = m[0] if m else date.today().strftime('%d/%m/%Y')

        m = findall(r'\\documentclass\{(.*)\}', self.raw_content)
        self.document_class = m[0] if m else 'article'

        m = findall(r'\\usepackage(\[.*\])?\{biblatex\}', self.raw_content)
        self.biblatex = bool(m)

    def expand_macros(self):
        content = self.raw_content
        breadcrumbs = str(self.pretty_breadcrumbs).replace('>',
                                                          r'\textgreater\hspace{1pt}')
        content = content.replace(r'\breadcrumbs', breadcrumbs)
        outdir = (file_output_root/self.breadcrumbs).parent
        content = content.replace(r'\outdir', str(outdir))
        self.content = content

    def __init__(self, input_file):
        self.input_file = input_file

        self.breadcrumbs = Path(*input_file.parts[len(input_root.parts):]).with_suffix('')
        self.pretty_breadcrumbs = str(self.breadcrumbs) \
                                     .replace('_', ' ') \
                                     .replace('/', ' > ')

        with open(input_file, 'r') as f:
            self.raw_content = f.read()

        self.mtime = input_file.stat().st_mtime
        self.extract_tex_metadata()

        self.expand_macros()


class FromTeX:
    def __init__(self, tex_file, ext):
        self.tex_file = tex_file

        self.output_file = file_output_root / self.tex_file.breadcrumbs.with_suffix(ext)

        self.mtime = self.output_file.stat().st_mtime \
                     if self.output_file.exists() else 0
        self.is_outdated = self.mtime < self.tex_file.mtime


class HtmlFile(FromTeX):
    def __init__(self, tex_file):
        super().__init__(tex_file, '.html')

    def write_output(self):
        args = [
            'pandoc',
            '--mathjax=static/mathjax/es5/tex-mml-chtml.js',
            '-f', 'latex',
            '-t', 'html',
            '-'
        ]
        proc = run(args,
                   input=self.tex_file.content,
                   encoding='utf-8',
                   capture_output=True)

        if proc.returncode != 0:
            print(proc.stderr, file=stderr)
            exit(proc.returncode)

        body = proc.stdout

        try:
            template = templates[self.tex_file.document_class]
        except:
            print('No template named "{}.html"'.format(self.tex_file.document_class),
                  file=stderr)
            exit(2)

        root = Path(relpath(output_root, start=self.output_file)).parent

        if self.tex_file.lang == 'portuguese':
            lang_title = 'Título'
            lang_author = 'Autor'
            lang_date = 'Data da Ficha'
        else:
            lang_title = 'Title'
            lang_author = 'Author'
            lang_date = 'Report Date'

        content = render_template(template,
                                  lang_title=lang_title,
                                  lang_author=lang_author,
                                  lang_date=lang_date,
                                  title=self.tex_file.title,
                                  date=self.tex_file.date,
                                  author=self.tex_file.author,
                                  breadcrumbs=self.tex_file.pretty_breadcrumbs,
                                  pdf=self.output_file.with_suffix('.pdf').name,
                                  root=root,
                                  body=body)

        highlighter.feed(content)
        content = highlighter.output()

        makedirs(self.output_file.parent, exist_ok=True)
        with open(self.output_file, 'w') as f:
            f.write(content)


class PdfFile(FromTeX):
    def __init__(self, tex_file):
        super().__init__(tex_file, '.pdf')

    def run_pdflatex(self):
        args = [
            'pdflatex',
            '-jobname', self.output_file.stem,
            '-output-directory', self.output_file.parent,
            '-shell-escape'
        ]

        env = {
            **environ,
            'TEXINPUTS': './include:'
        }

        proc = run(args,
                   env=env,
                   input=bytes(self.tex_file.content, 'utf-8'),
                   capture_output=True)

        if proc.returncode != 0:
            print(proc.stdout, file=stderr)
            print(proc.stderr, file=stderr)
            exit(proc.returncode)

    def run_biber(self):
        args = [
            'biber',
            self.output_file.with_suffix('')
        ]

        proc = run(args,
                   capture_output=True)

        if proc.returncode != 0:
            print(proc.stdout, file=stderr)
            print(proc.stderr, file=stderr)
            exit(proc.returncode)

    def write_output(self):
        makedirs(self.output_file.parent, exist_ok=True)

        self.run_pdflatex()

        if self.tex_file.biblatex:
            self.run_biber()
            self.run_pdflatex()


def write_files():
    changed = False

    for input_file in input_root.glob('**/*.tex'):
        tex_file = TeXFile(input_file)

        html_file = HtmlFile(tex_file)
        pdf_file = PdfFile(tex_file)

        if html_file.is_outdated:
            print('Generating "{}"'.format(html_file.output_file))
            html_file.write_output()
            changed = True

        if pdf_file.is_outdated:
            print('Generating "{}"'.format(pdf_file.output_file))
            pdf_file.write_output()
            changed = True

    return changed

def copy_static_files():
    if not output_root.exists():
        makedirs(output_root)

    for entity in static_root.iterdir():
        dest = output_root/Path(*entity.parts[len(static_root.parts):])
        if not dest.exists():
            print('Copying "{}" to "{}"'.format(entity, dest))
            if entity.is_dir():
                copytree(entity, dest)
            else:
                copy(entity, dest)

def make_details(directory):
    html = ''

    if directory != input_root:
        html += '<details open>'
        html += '<summary>{}</summary>'.format(directory.name.replace('_', ' '))

    html += '<ul>'
    for file in directory.iterdir():
        if file.is_file():
            if file.suffix == '.tex':
                outfile = Path(*file.resolve().parts[len(input_root.resolve().parts):])
                outfile = ('files'/outfile).with_suffix('.html')

                html += '<li><a href="{}">{}</a></li>'.format(outfile,
                                                              file.stem.replace('_', ' '))
        else:
            html += make_details(file)
    html += '</ul>'

    if directory != input_root:
        html += '</details>'

    return html

def make_index():
    html = '<ul id="toc">'
    html += make_details(input_root)
    html += '</ul>'

    index = render_template(templates['index'],
                            toc=html)

    with open(output_root / 'index.html', 'w') as f:
        f.write(index)

copy_static_files()
outdated_index = write_files()

if outdated_index:
    print('Generating index')
    make_index()
