#sdobrev 2007
'python module tools'

def file_relative_to_module( name, module):
    '''make full pathname of a file that is relative to some module's path'''
    from os.path import dirname, join
    if isinstance( module, str): module = __import__( module)
    return join( dirname( module.__file__ ), name)

def import_fullname( name, **kargs):
    'replacement of __import__ returning the leaf module'
    m = __import__( name, **kargs)
    subnames = name.split('.')[1:]
    for k in subnames: m = getattr(m,k)
    return m

# vim:ts=4:sw=4:expandtab
