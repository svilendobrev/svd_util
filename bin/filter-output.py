#$Id$
#filtering=count-generalizing instance/run-specific things, e.g. addresses
#wat?!

replaces = {
    '^Ran \d+ tests? in (?P<time>[\d.]+)s\s*$' : [],
#    'instance at (?P<address>0x[0-9a-f]+)>' : {},
    'at (?P<address>0x[0-9a-f]+)>' : {},
    '[".!; ](?P<fid>f(_m)?\d+)[".]' : {},
    '@-(?P<address>0x[0-9a-f]+)' : {},
    '(?P<address>-?0x[0-9a-f]+)' : {},
}

import re,sys
for v in sys.argv[1:]:
    replaces[ v] = {}
rc = {}
for r,counter in replaces.iteritems():
    rc[ re.compile( r)] = counter

for l in sys.stdin:
    for r in rc:
        def repl( m):
            founds = rc[r]
            count = len(founds)+1
            #count = rc[r]+1
            d = m.groupdict()
            assert len(d) ==1, 'one group only per regexp !'
            for k,v in d.iteritems():
                name = '<%(k)s%(count)d>' % locals()
                if isinstance( founds, dict):
                    name = founds.setdefault( v, name)
                else:
                    founds.append( v)
                return m.string[ m.start(0): m.start( k)] + name + l[m.end( k):m.end(0)]

        l = r.sub( repl, l)
    sys.stdout.write( l)

# vim:ts=4:sw=4:expandtab
