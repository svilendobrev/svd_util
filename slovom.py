# -*- coding: cp1251 -*-
'numbers in words in Bulgarian  2008? friends | числа словом'

_DIGITS = [
    '',
    'един',
    'два',
    'три',
    'четири',
    'пет',
    'шест',
    'седем',
    'осем',
    'девет',
]
_DIGITS_ALT = {
    'един' : 'една',
    'два'  : 'две',
}

_BIG_DIGITS_NAMES = [
    '',
    'хиляда',
    'милион',
    'милиард',
    'трилион',
    'квадрилион',
    'квинтилион',
    'секстилион',
    'септилион',
    'октилион',
    'нонилион',
    'децилион',
    'индецилион',
    'дуодецилон',
    'тридецилион',
    'куадродецилион',
    'басицилион',
]

def slovom(write_number, curr= 'лева и', after_point='00', curr_sents='ст.'):
    length = len(write_number)
    if length == 1:
        result = onedigit(write_number)
    elif length == 2:
        result = decimal(write_number)
    elif length == 3:
        result = hundred(write_number)
    else:
        result = thousand_and_bigger(write_number)
    return '%s %s %s %s' % (result, curr, after_point, curr_sents)

def onedigit(s, alternative=False):
    d = _DIGITS[ int(s)]
    if alternative:
        d = _DIGITS_ALT.get(d, d)
    return d

def decimal(s, **kargs):
    if s == '10':
        result = 'десет'
    elif s[0] == '1':
        result = (s[1] == '1' and 'еди' or onedigit(s[1])) + 'надесет'
    elif s[1] == '0':
        result = onedigit(s[0], **kargs) + 'десет'
    else:
        result = onedigit(s[0], **kargs) + 'десет и ' + onedigit(s[1], **kargs)
    return result

def hundred_round(s):
    if s == '000':
        result = ''
    elif s == '100':
        result = 'сто';
    elif s[1] == '0' and s[2] == '0': # && s != '100':
        d = s[0]
        if d == '2':
            result = 'двеста'
        elif d == '3':
            result = 'триста'
        else:
            result = onedigit(d) + 'стотин'
    return result

def hundred(s, **kargs):
    s1 = int(s[1])
    s2 = int(s[2])
    if s1 == 0 and s2 == 0:
        result = hundred_round(s)
    elif s1 == 0 and s2 != 0:
        s_round = s[:2] + '0'
        result = '%s и %s' % (hundred_round(s_round), onedigit(s2, **kargs))
    elif s1 != 0 and s2 == 0:
        s_round = s[0] + '00'
        s_decimal = s[1:3]
        result = '%s и %s' % (hundred_round(s_round), decimal(s_decimal, **kargs))
    elif s1 != 1 and s2 != 0:
        s_round = s[0] + '00'
        s_decimal = s[1:3]
        result = hundred_round(s_round) + ' ' + decimal(s_decimal, **kargs)
    elif s1 == 1 and s2 != 0:
        s_round = s[0] + '00'
        s_decimal = s[1:3]
        hundreds = hundred_round(s_round)
        if hundreds:
            result = '%s и %s' % (hundreds, decimal(s_decimal, **kargs))
        else:
            result = decimal(s_decimal, **kargs)
    return result

def thousand_and_bigger(s):
    res = ''
    end = length = len(s)
    start = length-3
    first = True
    while start != end:
        chunk = s[start:end]
        l = len(chunk)
        plural = True
        if l == 1:
            if chunk == '1':
                plural = False
            f = onedigit
        elif l == 2:
            f = decimal
        else:
            f = hundred
        wchunk = f( chunk)
        if wchunk:
            big_name = _BIG_DIGITS_NAMES[ (length-start-1)/3]
            if plural:
                if big_name:
                    if big_name == 'хиляда':
                        big_name = 'хиляди'
                        wchunk = f( chunk, alternative=True)
                    else:
                        big_name += 'а'
            else:
                if big_name == 'хиляда':
                    wchunk = '' #avoid edin hilqda
            wchunk += (' ' + big_name  + '')
            if first:
                if ' и ' not in wchunk:
                    wchunk = 'и ' + wchunk
                first = False
            res = wchunk + ' ' + res
        end = start
        start -= 3
        if start < 0:
            start = 0
    #needs rework
    res = res.strip()
    if res.startswith('и'):
        res = res[1:]
    res = res.strip().replace('  ', ' ')
    return res

if __name__ == '__main__':
    for i in [  1,
               11, 18, 20, 21, 22, 29, 30, 31, 39,
               100, 101, 110, 111, 132, 190, 200, 201, 300, 401, 800,
               1000, 1002, 1111, 1221, 1392, 1220, 1222,
               10000, 11000, 11200, 50001, 52002, 50300, 50303,
               51000, 502000, 5003000,
               120000, 125125,
               1002000, 1120000, 1125125,
               11120000, 11125125,
               100000000000000011120111,
               11112512555555555000000001,
        ]: print i, slovom(str(i))

# vim:ts=4:sw=4:expandtab
