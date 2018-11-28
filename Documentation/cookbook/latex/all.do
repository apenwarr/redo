for d in latex dvips dvipdf Rscript; do
    if ! type "$d" >/dev/null 2>/dev/null; then
        echo "$0: skipping: $d not installed." >&2
        exit 0
    fi
done

redo-ifchange paper.pdf paper.ps
