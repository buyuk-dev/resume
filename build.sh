#!/usr/bin/env bash
# sudo apt-get install pandoc texlive-latex-base texlive-fonts-recommended texlive-extra-utils texlive-latex-extra
pandoc -V colorlinks=true -V linkcolor=blue -V geometry:margin=1.5cm -o resume.pdf resume.md --wrap=preserve
cp resume.pdf MichalskiMichal.pdf
