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

def olddiff( a,b, aname, bname):
    d = difflib.Differ()
    N = 2
    buff=[]
    once = False
    for line in d.compare( a,b):
        if line[0]==' ':
            buff.append( line)
            if len(buff)>N: del buff[0]
        else:
            if not once:
                yield '-', aname, '->', '+', bname
                once = True
            for l in buff:      #pre-context only
                yield l,
            buff = []
            yield line

import difflib
def diff( a, b, aname ='a', bname ='b', type ='unified', #or ndiff or context
        **ka):  #unified context ndiff /unittest
    if isinstance( a, str): a = a.splitlines()  #was keepends=True
    if isinstance( b, str): b = b.splitlines()

    if type=='ndiff':
        return difflib.ndiff( a,b)
    try:
        differ = type=='context' and difflib.context_diff or difflib.unified_diff
    except NameError:
        differ = olddiff
    return differ( a, b, aname, bname, **kargs)

def diff_pprint( a, b, **ka):
    import pprint
    if not isinstance( a, str): a = pprint.pformat( a)
    if not isinstance( b, str): b = pprint.pformat( b)
    return diff( a, b, **ka)

def difftext( a, b, use_pprint =False, **ka):
    differ = diff_pprint if use_pprint else diff
    return '\n'.join( differ( a,b, **ka))

# vim:ts=4:sw=4:expandtab

