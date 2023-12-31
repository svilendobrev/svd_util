#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function #,unicode_literals

import re
import sys
import collections

from svd_util.dicts import dictAttr

from django.core.management.base import BaseCommand

def norm_url( u):
    return u.rstrip('/') + u.endswith('/') * '/'


class Command_url_cov( BaseCommand):
    help = 'compare tested vs used urls+methods'

    URL_COV_FILE = '.test_url_cov'  #.testing.APIClient_tracking_requests_Mixin.URL_COV_FILE ??

    def add_arguments( me, parser):
        parser.add_argument( '--cov-urls-tested', default= me.URL_COV_FILE, help= 'automatic file containing tested urls')
        parser.add_argument( '--funcs_tested',  action='store_true', help= 'show urls with functional tests')
        parser.add_argument( '--perms_tested',  action='store_true', help= 'show urls with permissions tests')
        parser.add_argument( '--no-perms',      action='store_true', help= 'do not show permissions at all')
        parser.add_argument( '--testtrace',     action='store_true',
            help= 'show which tests (and their trace - file,class,testname) have covered the url')
        #parser.add_argument( '--exnomencl', action='store_true', help= 'ignore nomenclature-likes')

    def handle( me, *args, **options):
        opts = dictAttr( options)
        urls = me.urls_from_inside()
        return me.print_diff( urls, opts)

    def urls_from_inside( me, url_only =False):
        from django_extensions.management.commands import show_urls
        urlconf = __import__( show_urls.settings.ROOT_URLCONF, {}, {}, [''])
        view_functions = show_urls.Command().extract_views_from_urlpatterns( urlconf.urlpatterns)
        all_urls = {}
        for (func, regex, url_name) in view_functions:
            url = show_urls.simplify_regex( regex)
            if '.<format>' in url: continue
            url = norm_url( url)
            metadata = dict( (k, getattr( func,k))
                            for k in 'view_class cls actions'.split()   #view_initkwargs initkwargs
                            if hasattr(func,k)
                            )
            if metadata.get( 'view_class') == metadata.get( 'cls'):
                metadata.pop( 'view_class', None)
            #if any, actions is like: { get : .methodname, post: .methodname, ..}
            func_name = func.__name__
            module = func.__module__ + '.' + func_name
            cls = metadata.get( 'cls') or metadata.get( 'view_class')
            if 'actions' in metadata:
                actions = metadata.pop('actions')
                ##@drf.detail_route is here as well
            else:
                #apiview/view/...rawfunc whatever
                actions = dict( (m,m) for m in 'get head post put patch delete'.split() if hasattr( cls, m))
                if not actions:  actions.update( any=None)

            if cls:
                actions = dict( (h,f) for h,f in actions.items()
                                if h in cls.http_method_names and hasattr( cls,f) or (h,f)==('any',None) )
                if len(metadata) == 1:
                    metadata = list( metadata.values())[0]
            all_urls[ url] = dict( (act, metadata) for act in actions)
        return all_urls

    def process_tested_url( me, url): return url

    def tested_urls_from_cov( me, fname):
        turls = eval( open( fname).read())  #{ (fname,tname) : [ (method,url) ] }
        perms = dict( (k[1], turls.pop(k)) for k in list(turls) if 'permissions' in k[0] )
        def turlcov2urldict( turls):
            urls = collections.defaultdict( dict )
            for where,methurls in turls.items():
                for method,url in methurls:
                    url = norm_url( url)
                    url = me.process_tested_url( url)
                    urls[ url ].setdefault( method.lower(), [] ).append( where)
            return urls

        return turlcov2urldict( turls) , turlcov2urldict( perms)

    def print_diff( me, all_urls, opts,
                        excluded_first_level =(), excluded_last_level =(),
                        excluder =None,
                        dont_exclude_if_tested =False
                        ):

        tested_urls = me.tested_urls_from_cov( opts.cov_urls_tested)
        tfuncs, tperms = tested_urls

        all_urls = dict( (re.sub( '<\w*>', '{pk}', u),v) for u,v in all_urls.items() )
        all_urls0 = all_urls.copy()
        for u in all_urls0:   #exclude
            uf = u.split('/')[1]
            ul = u.rstrip('/').split('/')[-1]
            if (
                excluded_first_level and uf in excluded_first_level
                or
                excluded_last_level and ul in excluded_last_level
                or
                excluder and excluder( u, first=ul, last=ul)
                ) and (not dont_exclude_if_tested or u not in tfuncs and u not in tperms):
                    del all_urls[ u]

        # filter by all_urls - .cov may collect multiple subprojects
        funcs = dictAttr( tested = dict( (u,v) for u,v in tfuncs.items() if u in all_urls)) # or u in all_urls0 and dont_exclude_if_tested
        perms = dictAttr( tested = dict( (u,v) for u,v in tperms.items() if u in all_urls))
        for what in (funcs, perms):
            what.update( ok_urls = 0, ok_urlmethods =0, untested = {} )
            for url,method_where in sorted( all_urls.items()):
                cov = what.tested.get( url)

                def mwhere2mmwhere( method_where):
                    view2method = {}
                    for m,vw in method_where.items():
                        view2method.setdefault( vw, []).append( m)
                    return dict( (' '.join( sorted( mm)).upper(), vw) for vw,mm in view2method.items())

                if not cov:
                    what.untested[ url] = mwhere2mmwhere( method_where)
                else:
                    missed = set( method_where) - set( cov)
                    if missed:
                        what.untested[ url] = mwhere2mmwhere( dict( (method, method_where[ method]) for method in missed) )
                    else:
                        what.ok_urls += 1
                        what.ok_urlmethods += len( method_where)


        total = dictAttr( urls = len( all_urls), urlmethods= sum( len(m) for m in all_urls.values() ) )
        print( '\n------ total', 'urls/methods=', total.urls, total.urlmethods )
        from pprint import pprint
        whats = ['funcs'] + (not opts.no_perms) * [ 'perms']

        for nwhat in whats:
            _do = dict( funcs= opts.funcs_tested, perms= opts.perms_tested )[ nwhat ]
            if _do:
                what = locals()[nwhat]
                if not opts.testtrace:
                    what.tested= dict( (url, ' '.join( sorted( methods2testtrace)).upper())
                                        for url, methods2testtrace in what.tested.items()
                                     )
                print( '\n------ tested', nwhat,)
                pprint( what.tested)#, width= 200)# to show everything on one row

        for nwhat in whats:
            what = locals()[nwhat]
            what.update( unt_urls= len(what.untested), unt_urlmethods= sum( len(m) for m in what.untested.values() ))
            print( '\n------', nwhat,
                'ok urls/umethods=', what.ok_urls, what.ok_urlmethods,
                ';',
                'untested urls/umethods=', what.unt_urls, what.unt_urlmethods,
                )
            pprint( what.untested)

        def perc( x,total): return str(int(100*x)//total)+'%'
        def xperc( x,total): return str(x)+':'+str(int(100*x)//total)+'%'
        print( '\n=== total', 'urls/methods=', total.urls, '/', total.urlmethods)
        for nwhat in whats:
            what = locals()[nwhat]
            print( nwhat, 'ok', xperc( what.ok_urls, total.urls), '/', xperc( what.ok_urlmethods, total.urlmethods),
                          'untested=', xperc( what.unt_urls, total.urls), '/', xperc( what.unt_urlmethods, total.urlmethods),
                    )

    if 0:
     def urls_from_outside( me):
        all_urls_file = sys.stdin
        return [ norm_url( row.split()[ 0].replace( r'\.<format>', ''))
                    for row in all_urls_file]

     def tested_urls_from_manual( me, tested_urls_fname):
        URLS = None
        with open( tested_urls_fname) as tested_urls_file:
            tested_urls = {}
            for row in tested_urls_file:
                row = row.split()
                if not (row and row[0].startswith( '**')): continue
                if row[0] == '**':
                    if row[1].startswith( 'URLS'):
                        URLS = row[2:]
                    continue
                assert row.pop(0) == '***', row
                url = row.pop(0)

                covers = tuple('+-*~')
                kinds = [ dictAttr( kind= 'func')]#, cover = None, detail = None) ]
                while row:
                    i = row.pop(0)
                    if i in covers:
                        kinds[-1].cover = i
                    elif i.startswith('('):
                        kinds[-1].detail = i.strip('()')
                    elif i.startswith('P'):
                        assert i[-1] in covers, i
                        kinds.append( dictAttr( kind= 'perm', cover= i[-1], ) )

                tested_urls[ url] = kinds  #= [row[0] for row in tested_items]
                #TODO use these kinds etc

        return tested_urls

# vim:ts=4:sw=4:expandtab

