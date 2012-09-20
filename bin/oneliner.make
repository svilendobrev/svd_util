LIST = list.md
REPO = svd_util
PFX  = https://github.com/svilendobrev/$(REPO)/blob/master/
PREPO= .#/$(REPO)
ONER = $(PREPO)/bin/oneliner.py
FILES = *.py bin/*.py py/[pu]*.py */__init__.py
README = $(PREPO)/README.md

a: j
.PHONY: $(LIST).tmp

$(LIST).tmp: $(MAKEFILES) $(ONER)
	$(ONER) --base=$(PFX) --para --mdlink --unprefix=$(PREPO)/ $(FILES:%=$(PREPO)/%) >$@

j: $(README) $(LIST).tmp
	perl -ne 'print if !$$a; $$a+=/----/;' $(README) > $(LIST)
	cat $(LIST).tmp >> $(LIST)

# vim:ts=4:sw=4:noexpandtab
