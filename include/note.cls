\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{note}[2022/3/14 Note]

\LoadClass{article}

\usepackage[margin=1in]{geometry}

\newcommand{\noteheader}[1]{
	\noindent\large
	\begin{center}
	#1
	\end{center}
}
