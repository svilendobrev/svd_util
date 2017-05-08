#sdobrev 2005
'sort/reorder sqlite .dump, for comparable outputs'

all ={}
class Tabl:
    def __init__( me, name):
        all[ name] = me
        me.name =name
        me.decl = []
        me.ins  = []
        me.created = False

table = None
import sys
for line in sys.stdin:
    line = line.rstrip()
    if line.startswith( 'CREATE'):
        table = Tabl( line)
    elif not (table and table.created):
        if line.startswith( ');'):
            table.decl.append( line)
            table.created = True
        elif line.startswith( '\t'):
            table.decl.append( line)
    elif line.startswith( 'INSERT'):
        table.ins.append( line)
    else:
        print('unknown:', line)

for t in sorted( list(all.values()), key=lambda x:x.name):
    t.decl.sort()
    t.decl = [ l.endswith(',') and l or l+','
            for l in t.decl ]
    print('\n'.join( [ t.name ] + t.decl + t.ins ))

# vim:ts=4:sw=4:expandtab
