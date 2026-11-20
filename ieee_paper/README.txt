Compile on Overleaf (it supplies the official IEEEtran.cls): upload this folder as a project, set main.tex as the main file.
Locally: pdflatex main.tex (twice). Figures/tables are regenerated with: python make_figs.py ; python mk_tables.py
To add co-authors, edit the \author block in main.tex (instructions are in the comments).
