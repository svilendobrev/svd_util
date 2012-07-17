#s.dobrev 2k4-2011
'wrapper and ignore_space for difflib'

import difflib
import re
re_spaces = re.compile( ' +')

def unified_diff_ignore_space( a, b, fromfile='', tofile='', fromfiledate='',
                 tofiledate='', n=3, lineterm='\n'):
    'reduce all consecutive spaces into single, compare, and print using original lines. all else - same'
    from difflib import SequenceMatcher, _format_range_unified
    aa = [ re_spaces.sub(' ', x) for x in a]
    bb = [ re_spaces.sub(' ', x) for x in b]

    started = False
    for group in SequenceMatcher(None,aa,bb).get_grouped_opcodes(n):
        if not started:
            started = True
            fromdate = '\t{}'.format(fromfiledate) if fromfiledate else ''
            todate = '\t{}'.format(tofiledate) if tofiledate else ''
            yield '--- {}{}{}'.format(fromfile, fromdate, lineterm)
            yield '+++ {}{}{}'.format(tofile, todate, lineterm)

        first, last = group[0], group[-1]
        file1_range = _format_range_unified(first[1], last[2])
        file2_range = _format_range_unified(first[3], last[4])
        yield '@@ -{} +{} @@{}'.format(file1_range, file2_range, lineterm)

        for tag, i1, i2, j1, j2 in group:
            if tag == 'equal':
                for line in a[i1:i2]:
                    yield ' ' + line
                continue
            if tag in {'replace', 'delete'}:
                for line in a[i1:i2]:
                    yield '-' + line
            if tag in {'replace', 'insert'}:
                for line in b[j1:j2]:
                    yield '+' + line

def diff( h1, h2, h1name ='', h2name ='', type='unified', **kargs):
    if isinstance( h1, str): h1 = h1.splitlines(1)
    if isinstance( h2, str): h2 = h2.splitlines(1)

    try:
        differ = type=='context' and difflib.context_diff or difflib.unified_diff
    except NameError:
        d = difflib.Differ()
        N = 2
        buff=[]
        a = False
        for line in d.compare( h1,h2):
            if line[0]==' ':
                buff.append( line)
                if len(buff)>N: del buff[0]
            else:
                if not a:
                    yield '-', h1name, '->', '+', h2name
                    a=True
                for l in buff:      #pre-context only
                    yield l,
                buff = []
                yield line
    else:
        for l in differ( h1, h2, h1name, h2name, **kargs):
            yield l

# vim:ts=4:sw=4:expandtab

