#$Id$

PYRUN = PYTHONPATH=.. python

%.test: %.py
	@echo =============== "$(ARGS)"
	$(PYRUN) $< -v $(ARGS)
#  wx

now: menu.test panel4statics.difft

######################

#panel4statics.difft: ARGS += all
panel4statics.difft: tests/panel4statics.diff	#override default rule above

never:
tests/%.result: %.py never
	$(PYRUN) $< -v $(ARGS) > $@

.PRECIOUS: %.org tests/%.result 	#patterns same as in a rule!
.PHONY: tests/%.diff    #patterns same as in a rule!
%.org: %.result
	@[ -f $@ ] || ( read -p '$@ original inexisting. create?' -n 1 && [ "$$REPLY" = "y" ] && cp $< $@ && echo '' )
%.diff: %.result %.org
#		may use bash's pipefail-option
	diff -btw $+ > $@ || ( cat $@ && false )
#	rm -f $*.result $@
cleantest: clean-test-result
clean-test-%:
	rm -f tests/*.$*


################# not needed for now
%.tmp: %
	@$(PY) ../bin/filter-output.py < $< >$@
#	echo -e '\n-------- test $*'
%.ok: %.result.tmp %.org
	diff -btw $+
	@touch $@
	@echo

# vim:ts=4:sw=4:noexpandtab
