#!/usr/bin/env bash
set -euo pipefail

# Build dependencies (Debian/Ubuntu):
#   sudo apt-get install -y pandoc texlive-xetex texlive-latex-recommended texlive-latex-extra
# macOS: install Pandoc + MacTeX or BasicTeX and ensure XeLaTeX is available.

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
  -o resume.pdf source.md --wrap=preserve 2>/dev/null

cp resume.pdf MichalskiMichal.pdf

# Generate clean markdown for GitHub display
{
  # Extract header info from YAML frontmatter
  title=$(grep '^title:' source.md | sed 's/title: *"//' | sed 's/"$//')
  subtitle=$(grep '^subtitle:' source.md | sed 's/subtitle: *"//' | sed 's/"$//')
  author=$(sed -n '/^author:/,/^[a-z]/p' source.md | grep -v '^author:' | grep -v '^header' | sed 's/^  //' | head -1)

  echo "# $title"
  echo "**$subtitle**"
  echo ""
  echo "$author"
  echo ""
  echo "---"
  echo ""

  # Extract skills from pill macros (line starting with \pill, not definitions)
  skills_line=$(grep '^\\pill' source.md | head -1)
  if [ -n "$skills_line" ]; then
    skills=$(echo "$skills_line" | sed -E 's/\\pill[a-z]+\{([^}]*)\}/\1 /g' | tr -s ' ' | sed 's/^ //' | sed 's/ $//' | sed 's/C\\#/C#/g')
    echo "**Skills:** $skills"
    echo ""
  fi

  # Process the rest of the file
  sed -E '
    # Remove everything up to and including the closing ---
    1,/^---$/d

    # Skip LaTeX-only lines
    /^\\vspace/d
    /^\\begin\{/d
    /^\\end\{/d
    /^\\pill/d
    /^\\noindent/d
    /^\\centering/d

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

  ' source.md

} > resume.md

echo "Generated: MichalskiMichal.pdf, resume.md"
