#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import pip
import sys
'''
pipmerge many-requirements-or-constraints-files..
 where constraints-files are those having "constr" in name

overloads constraints OVER requirements into single requirements result:
    if item is in reqs , and once in constraints -> constraint installed
    if item is in reqs , and multiple non-empty in constraints -> duplication error
    if item is multiple in reqs , and not in constraints -> duplication error
    if item is only in reqs -> installed
    if item is only in constrains - ignore

the resulting single file can be given to pip install -r

beware that behavior of pip is somewhat different:
  pip install -r reqs1 -r reqs2 -c constraints1 -c constraints2
is as follows:
    if item is in reqs , and in constraints -> first constraint installed, rest ignored
    if item is multiple in reqs , and not in constraints -> duplication error
    if item is only in reqs -> installed
    if item is only in constrains - ignored

'''

if 'resurrect the comments':
    class ctx:
        _filename = None
        cmts_by_filename_lineno = {}
        @classmethod
        def ignore_comments( ctx, lines_enum):
            for line_number, line in lines_enum:
                m = pip.req.req_file.COMMENT_RE.search( line)
                if m:
                    cmt = m.group(0)
                    ctx.cmts_by_filename_lineno[ (ctx._filename, line_number) ] = cmt
                    line = line[ :m.start()] + line[ m.end(): ]
                line = line.strip()
                if line:
                    yield line_number, line

        #these instead of parsing .comes_from: -r ... (line ..)
        @classmethod
        def parse_requirements( ctx, filename, *a,**ka):
            ctx._filename = filename
            return pip.req.parse_requirements( filename, *a,**ka)

    _process_line = pip.req.req_file.process_line
    def process_line( line, filename, line_number, *a,**ka):
        for r in _process_line( line, filename, line_number, *a,**ka):
            r.comment = ctx.cmts_by_filename_lineno.get( (filename, line_number))
            yield r
    pip.req.req_file.process_line = process_line
    pip.req.req_file.ignore_comments = ctx.ignore_comments


files   = sys.argv[1:] # [ 'requirements.txt', 'constraints.txt' ]
parsed  = [ list( ctx.parse_requirements( fn, session=True, constraint= 'constr' in fn))
            for fn in files
            ]

#import pprint
#pprint.pprint( parsed)

base = parsed[0]

r_byname = dict( (r.name, r) for r in base )
for p in parsed[1:]:
    for r in p:
        existing = r_byname.get( r.name)
        if not existing:
            if not r.constraint:
                r_byname[ r.name ] = r
            continue
        if not r.constraint:
            raise RuntimeError( 'conflicting reqs: {r}, {existing}'.format( **locals()) )
        #print( existing.req.__dict__)
        #print( r.req.__dict__)
        es = existing.req.specifier
        rs = r.req.specifier
        if not rs: continue
        if es == rs: continue
        print( '..override:', r.name, es, 'with:', rs, file=sys.stderr)
        if existing.constraint and es and rs:
            raise RuntimeError( 'conflicting constraints: {r}, {existing}'.format( **locals()) )
        r_byname[ r.name ] = r
        if 0: #merge .extras? TODO XXX   from pip.req.req_set.py RequirementSet.add_requirement
           existing_req.constraint = False
           existing_req.extras = tuple(
                        sorted(set(existing_req.extras).union(
                               set(install_req.extras))))

#print('======')
for n,r in sorted( r_byname.items()):
    #see piptools/utils.py format_requirement()
    if r.editable: line = '-e {r.link}'.format( **locals())
    else: line = str( r.req).lower()
    if r.comes_from: line = line.ljust( 30) + '  # from {r.comes_from}'
    if getattr( r, 'comment', ''):  line = line.ljust( 30) + '  #' + r.comment.strip()
    print( line.format( **locals()))

# vim:ts=4:sw=4:expandtab
