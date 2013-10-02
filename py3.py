# sdobrev 2011
'using same code for python2 and python3'

import sys
v3 = sys.version_info[0]>=3
if v3:
    from collections import OrderedDict as dictOrder
    import collections
    #import __builtins__    #always there
    if not hasattr( __builtins__, 'callable'):  #again in 3.3
        def callable(x): return isinstance( x, collections.Callable)

    #if not hasattr( __builtins__, 'unicode'):
    unicode=str
    basestring=str
    file=open

    #obsolete modules
    #dictOrder = collections.OrderedDict
    #setOrder = ?
    #assignment_order: use metaclass.__prepare__
    #diff = difflib
    #module.import_fullname ~= import_lib.import_module
else:
    import __builtin__
    basestring= __builtin__.basestring
    unicode   = __builtin__.unicode
    file      = __builtin__.file
    try:
        from collections import OrderedDict as dictOrder
    except:
        from dictOrder import dictOrder

    #from __future__ import print_function, unicode_literals
def prn( *a, **kargs):
    stderr = use_stderr or 'use_stderr' in kargs or 'stderr' in kargs
    o = stderr and sys.stderr or sys.stdout
    o.write( ' '.join( unicode(x) for x in a) + '\n')

# vim:ts=4:sw=4:expandtab
