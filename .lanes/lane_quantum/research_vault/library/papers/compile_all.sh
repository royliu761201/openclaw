#!/bin/bash
# Helper to compile all papers with centralized templates
export TEXINPUTS=".:$(pwd)/templates/:"
for d in */; do
  if [ -d "$d" ] && [ "$d" != "templates/" ]; then
    cd "$d"
    paper_name=$(basename "$d")
    if [ -f "${paper_name}.tex" ]; then
      echo "Compiling ${paper_name}..."
      pdflatex -interaction=nonstopmode "${paper_name}.tex"
    fi
    cd ..
  fi
done
