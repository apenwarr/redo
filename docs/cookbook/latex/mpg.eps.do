redo-ifchange mpg.R
Rscript mpg.R >&2
mv mpg.new.eps $3

# Some buggy ggplot2 versions produce this
# junk file; throw it away.
rm -f Rplots.pdf
