#$Id: makefile,v 1.1 2004-06-03 14:54:59 sdobrev Exp $

test: test/html.py test/layout.py test/test_http_medusa.py #controller.py 

test/%: %
	PYTHONPATH=..; $(PY) $*
