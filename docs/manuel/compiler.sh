#!/bin/sh
# Compile les manuels FR et EN (deux passes), supprime les fichiers temporaires, copie les PDF dans coupole/docs.
#   sh docs/manuel/compiler.sh
set -e
ICI=$(cd "$(dirname "$0")" && pwd)
cd "$ICI"
V=$(cat ../../VERSION)
python3 ../../outils/tables_cli.py >/dev/null 2>&1 || true
for L in fr en; do
  if [ "$L" = fr ]; then D="8 octobre 2026"; else D="8 October 2026"; fi
  printf '\\newcommand{\\versioncoupole}{%s}\n\\newcommand{\\datecoupole}{%s}\n' "$V" "$D" > version.tex
  pdflatex -interaction=nonstopmode -halt-on-error manuel_$L.tex >/dev/null
  pdflatex -interaction=nonstopmode -halt-on-error manuel_$L.tex >/dev/null
done
rm -f *.aux *.log *.out *.toc version.tex
mkdir -p ../../coupole/docs
cp manuel_fr.pdf manuel_en.pdf ../../coupole/docs/
echo "manuels : $(ls -la manuel_fr.pdf manuel_en.pdf | awk '{print $5, $9}' | tr '\n' ' ')"
