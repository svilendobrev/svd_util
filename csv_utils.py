#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function #,unicode_literals

from common_helpers.dicts import dictAttr
from collections import OrderedDict as dictOrder


def read_table( table,
            pretrigger = lambda row: None,
            trigger = lambda row: True,
            ignorer = lambda row: False,
            stopper = lambda row: not row[0].strip(),   #empty first column
            stopper2= lambda row: False,
            key_translator  ={},
            only_translated_keys    =False,
            fname   =None,
            DBG     =False,
    ):
    '''
    keys is the first row that trigger(row)
    always strips keys and cells
    always ignores empty keys
    if key_translator, applies it
        if only_translated_keys, take only those with translations
    pretrigger(row)     #listen on all rows before trigger
    first yield is the (keys-as-is=dictOrder(n,key), row_org_keys)
    stop if stopper(row)    #stopper before ignorer
    if not ignorer(row)
        yield item= dictAttr( keys+row_values )
    stop if stopper2(row)   #stopper after ignorer
    '''
    if DBG: print( '<<: filename:', fname)
    on = 0
    keys = None
    for i,row in enumerate( table):
        if not on:
            if not trigger or trigger( row):
                on = 1
                keys_org = row
                keys = dictOrder( (n, key_translator.get(k,k))
                            for n,k in enumerate( (i.strip() for i in row)) #always strip keys
                            if k and #always ignore empty keys
                                not only_translated_keys or k in key_translator
                            )
                if DBG>1: print( '..keys', keys)
                yield keys, keys_org
            else:
                if pretrigger: pretrigger( row)
            continue
        if stopper and stopper( row): break
        if ignorer and ignorer( row): continue
        if stopper2 and stopper2( row): break

        #item = #zip( keys, row))
        item = dictAttr( (k, row[n].strip() if n<len(row) else None) for n,k in keys.items()) #have all keys
        #item = dictAttr( (keys[n],v) for n,v in enumerate(row) if n in keys)   #intersection of  keys/row
        if DBG>1: print( '..', item)
        yield item

import csv
def read_csv( file_or_name, **ka):
    csv_kargs = ka.pop( 'csv_kargs', {})
    infile = open(file_or_name) if isinstance( file_or_name, str) else file_or_name
    return read_table( fname= file_or_name, table= csv.reader( infile, **csv_kargs), **ka)

# vim:ts=4:sw=4:expandtab
