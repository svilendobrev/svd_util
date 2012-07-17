#sdobrev 2010
'empty context for with operator - i.e. with (somefile or wither): ...'

class wither:
    def __enter__(*a,**k): pass
    def __exit__(*a,**k): pass
wither=wither()

# vim:ts=4:sw=4:expandtab
