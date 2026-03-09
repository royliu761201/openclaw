# .latexmkrc for path-less template resolution
$latex = 'pdflatex -interaction=nonstopmode %O %S';
$pdflatex = 'pdflatex -interaction=nonstopmode %O %S';

# Add templates directory to TEXINPUTS
# The trailing // means search subdirectories
$ENV{'TEXINPUTS'} = ".:../templates//:" . $ENV{'TEXINPUTS'};
