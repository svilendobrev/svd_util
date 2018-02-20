#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function #,unicode_literals
#$Id: test_http_medusa.py,v 1.9 2006-07-11 16:14:09 sdobrev Exp $

from server.medusa_handler import Base_Handler#, HTTP_codes, htmlcodec, query2dict, dict2query
#from svd_util.module import file_relative_to_module

class Config_Handler( Base_Handler):
    uri_base = 'config'
    #uri_base_after = DataSave_Handler.uri_base_after + '/'
    valid_commands = 'GET',

    _handler = None
    _httpreq4medusa = None

    def setup( me, HTTPRequestHandler_factory ):    #=None, files_prefix_module=None):
        if not me._handler:
#            if not HTTPRequestHandler_factory:
#                from sim import httpreq_console
#                HTTPRequestHandler_factory= httpreq_console.HTTPRequestHandler
            me._handler = HTTPRequestHandler_factory
            from ui.httpRequest import httpRequest4medusa
            me._httpreq4medusa = httpRequest4medusa
#            if not files_prefix_module: files_prefix_module = HTTPRequestHandler_class.__module__
#            h.files_prefix = file_relative_to_module( h.files_prefix, files_prefix_module )

    def continue_request_processor( me, request, std_in, std_out):
        split_uri = path, params, query, fragment = request.split_uri()
        if query and query[0]=='?': query = query[1:]
        path = me.uri_regex_match( path).group(1)
        split_uri = path, params, query, fragment
        hrequest = me._httpreq4medusa( request, split_uri)
        me._handler( hrequest, me.uri_base).do_GET()
        request.done()

#######################

from server import medusa_http

def run(
        ip ='',
        file_root =None,
        http_port =8000,
        https_port =None, https_keys_path ='<default>',
        Config_Handler_Factory =Config_Handler,

        help =False,
    ):
    print('use:', medusa_http.help_kargs( locals(), ignore=[ 'help', 'Config_Handler_Factory'] ))
    if help: return
    ##for all booleans:
    #if isinstance( do_something, str): do_something= (do_something== 'True')
    # or
    #do_something = svd_util.runner.boolean( do_something)

    handlers= []
    c = Config_Handler_Factory or Config_Handler
    cfgh = Config_Handler_Factory()
    cfgh.setup()
    handlers.append( cfgh)

    dh = medusa_http.DefaultFileSys_Handler( file_root)
    if dh: handlers.append( dh)

    medusa_http.start_medusa(
        ip_address=ip,
        http_kargs= http_port and { 'port':int(http_port),
                        #...**http_server_kargs
                    } or {},
        http_handlers= handlers,
        https_kargs= https_port and { 'port':int(https_port),
                        'ssl_keys_path': https_keys_path,
                        #...**https_server_kargs
                    } or {},
        https_handlers= handlers,
     )

if __name__ == '__main__':
    medusa_http.runner( run)

# vim:ts=4:sw=4:expandtab
