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

# Generate PDF from source
pandoc \
  --pdf-engine=xelatex \
  -V mainfont="$FONT_MAIN" \
  -V sansfont="$FONT_SANS" \
  -V colorlinks=true -V linkcolor=blue \
  -V geometry:margin=1.5cm \
  -o resume.pdf resume.tex --wrap=preserve

cp resume.pdf MichalskiMichal.pdf

# Generate clean markdown for GitHub display
sed -E '
  # Remove YAML frontmatter
  1,/^---$/d
  /^---$/,/^---$/d

  # Skip LaTeX-only lines
  /^\\vspace/d
  /^\\begin\{/d
  /^\\end\{/d
  /^\\pill/d
  /^\\noindent/d

  # Convert \role{Company}{Title}{Dates} to markdown
  s/^\\role\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}/**\1**, \2 (\3)/

  # Convert \edu{Uni}{Dept}{Dates} to markdown
  s/^\\edu\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}/**\1**, \2 (\3)/

  # Convert \tech{...} to italic
  s/^\\tech\{([^}]*)\}/_\1_/

  # Convert \item to bullet
  s/^\\item /- /

  # Convert \mbox{\href{url}{text}} to [text](url)
  s/\\mbox\{\\href\{([^}]*)\}\{([^}]*)\}\}/[\2](\1)/g
  s/\\href\{([^}]*)\}\{([^}]*)\}/[\2](\1)/g

  # Clean up \mbox{} wrapper
  s/\\mbox\{([^}]*)\}/\1/g

  # Clean up LaTeX escapes
  s/\\&/\&/g
  s/C\\#/C#/g
  s/R\\&D/R\&D/g

' resume.tex > resume.md

echo "Generated: MichalskiMichal.pdf, resume.md"
