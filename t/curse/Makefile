all:
	. ./check-1.sh
	$(MAKE) 1.n0 2.n0 3.n0
	$(MAKE) $(shell seq 10 | sed 's/$$/.n1/')
	. ./check-2.sh

%.n0: $(shell seq 10 | sed 's/$$/.n1/')
	: >$@

%.n1: $(shell seq 100 | sed 's/$$/.n2/')
	echo n1-$* >$@

.PRECIOUS: %.n2
%.n2:
	echo n2-$* >$@
	echo $* >>$*.count
	echo $* >>in.countall
	$(MAKE) countall

.PHONY: countall
countall:
	echo $@ >>out.countall
	echo hello >$@

clean:
	rm -f *~ .*~ *.n0 *.n1 *.n2 *.tmp *.count countall *.countall
