\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{bookreport}[2022/3/12 Book Report]

\LoadClass{note}

\usepackage{iflang}

\renewcommand{\maketitle}{
	\IfLanguageName{portuguese}
	{
		\noindent\large
		Título: \hfill \@title\\
		Autor: \hfill \@author\\
		Data da Ficha: \hfill \@date\\
		\rule{\textwidth}{0.4pt}
	}
	{
		\noindent\large
		Title: \hfill \@title\\
		Author: \hfill \@author\\
		Report Date: \hfill \@date\\
		\rule{\textwidth}{0.4pt}
	}
}
