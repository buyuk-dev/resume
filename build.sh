#!/usr/bin/env bash
set -euo pipefail

# Build dependencies (Debian/Ubuntu):
#   sudo apt-get install -y pandoc texlive-xetex texlive-latex-recommended texlive-latex-extra
# macOS: install Pandoc + MacTeX or BasicTeX and ensure XeLaTeX is available.

# Allow overriding fonts via env vars, e.g.:
#   FONT_MAIN="SF Pro Text" FONT_SANS="SF Pro Text" bash build.sh
#   FONT_MAIN="Lato" FONT_SANS="Lato" bash build.sh
FONT_MAIN_DEFAULT="SF Pro Text"
FONT_SANS_DEFAULT="SF Pro Text"
FONT_MAIN="${FONT_MAIN:-$FONT_MAIN_DEFAULT}"
FONT_SANS="${FONT_SANS:-$FONT_SANS_DEFAULT}"

pandoc \
  --pdf-engine=xelatex \
  -V mainfont="$FONT_MAIN" \
  -V sansfont="$FONT_SANS" \
  -V colorlinks=true -V linkcolor=blue \
  -V geometry:margin=1.5cm \
  -o resume.pdf resume.md --wrap=preserve

cp resume.pdf MichalskiMichal.pdf
