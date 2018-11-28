library(ggplot2)

qplot(mpg, wt, data = mtcars) + facet_wrap(~cyl) + theme_bw()
ggsave("mpg.new.eps", width=4, height=2, units='in')
