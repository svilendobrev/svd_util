# $Id: httpRequest.py,v 1.10 2006-07-12 11:20:43 sdobrev Exp $
#s.dobrev 2k3-4

from ui.html import uri2fieldMethod, htmlize
from util.fileCache import FileCache
import socket, traceback, sys

fileCacher = FileCache()

class UI_HTTPRequestHandler:
    """ expected request.attributes:
       .req_send_error( http_errno, message )
       .req_send_header( response =200, headers ={} )
       .req_write( *items)      #item is text or iter of texts
       .req_get_uri_maybesplit()    return split uri or uri-as-str
       .req_get_info()              return uri, client_address, time, etc
    """

    def __init__( me, request, uri_base =None ):
        me.request = request
        me.uri_base = uri_base

    def _print( me, *args):
        print 'request', id( me), me.request.req_get_info(), ':',
        for a in args: print a,
        print
    def _error( me, http_errno, *messages):
        me._print( *messages )
        me.request.req_send_error( http_errno, ' '.join( messages) )
    def _send_head( me, ctype ='text/html'):
        """sends the response code and MIME headers."""
        me.request.req_send_header( response=200, headers=(
            ('Content-type', ctype),
        #see cgi:irc for these
            ('Pragma', 'no-cache'),
            ('Cache-control', 'must-revalidate, no-cache'),
            ('Expires', '-1'),
        ) )

    def copyfile( me, f_name):
        try:
            content = fileCacher.read( f_name)
        except IOError, e:     #can't open / read error
            me._error( 404, 'File error: %r' % f_name, e.strerror )
            return -1
        #except: traceback.print_exc()
        else:
            me.request.req_write( content )
    htm  = '.htm'
    html = '.html'

    handle_uri_invalid_but_method_or_address = None

    class Handle_file:
        files_prefix = ''   #'html/'
        def __init__( me, files_prefix =''):
            me.files_prefix = files_prefix
        def __call__( me, context, path, *a,**k ):
            context.copyfile( me.files_prefix + path )
    handle_file = Handle_file()

    path_handlers = {}

    #files = [ 'ui.css', ]   #'ui.js', ]
    #for l in files: path_handlers[ l] = handle_file

    # XXX requesting main works like:
    #   http://..               ->  /mainf.htm, then /console.htm, ...
    #   http://../              ->  same
    #   http://../main.htm      ->  same, as well as all in .main_aliases
    #   http://../somepath/     ->  /config/mainf.htm, then /config/console.htm, ...
    #   http://../somepath/main ->  same
    # but
    #   http://.../somepath     ->  /config/mainf.html, then /console.htm, ...
    # which does not work - returns 404 for those not /config/ prefixed
    # is it possible to do it ???

    def do_GET( me):
        try:
            uri = me.request.req_get_uri_maybesplit()

            #parse to extract obj/method
            #if not uri: uri= '/'
            path, address, method, qargs = parsed = uri2fieldMethod( uri)
            #print uri, parsed

            handler = me.path_handlers.get( path, None)
            if handler or (method or address) and me.handle_uri_invalid_but_method_or_address:
                me._send_head()
                try:
                    if handler:
                        #unbound
                        handler( me, *parsed)
                    else:
                        # XXX   is this dangerous?
                        #bound
                        me.handle_uri_invalid_but_method_or_address( *parsed)
                except (socket.error, IOError): raise
                except:
                    exc = ''.join( traceback.format_exception( *sys.exc_info() ) )
                    exc = '<body> <b> Handling Error: </b><br>\n<pre>' + htmlize( exc) + '\n</body>'
                    me.request.req_write( exc )
            else:
                me._error( 404, 'File not found: %r' % path)

        except socket.error: me._print( 'connection closed by client')
        except IOError, e: me._error( 500, 'File error:', e.strerror)
        except:
            exc = ''.join( traceback.format_exception( *sys.exc_info() ) )
            me._error( 500, exc )

    def do_HEAD( me):
        try:
            me._send_head()
        except ( IOError, socket.error): me._print( 'connection closed by client')
        except: traceback.print_exc()

    def _handle_UIController4HTML( me, controller, path, address, method, qargs ):
        #path ignored
        r = None
        if method == 'push':
            r = controller.action( me, address)
        elif method == 'setvalue':
            r = controller.set_value( me, address, **qargs)
        elif method:
            me._print( '! unknown method:', method )
            return
        if r is None:
            r = controller.redraw( context=me)
        if r:
           me.request.req_write( r)

def make_path_handlers( handler, path_handlers =None,
        exts_root =('','/'),
        exts_name =( '', '/', UI_HTTPRequestHandler.htm, UI_HTTPRequestHandler.html, '.redraw' ),
        handler_name ='controller',
        files = (),
        handler_file =UI_HTTPRequestHandler.handle_file,
    ):
    if path_handlers is None:
        path_handlers = UI_HTTPRequestHandler.path_handlers.copy()
    for e in exts_root: path_handlers[ e ] = handler
    if handler_name:
        for e in exts_name: path_handlers[ handler_name +e ] = handler
    for e in files: path_handlers[ e ] = handler_file
    return path_handlers

class httpRequest4medusa:
    """use as:
        hrequest = httpRequest4medusa( request, split_uri)
        some.UI_HTTPRequestHandler( hrequest).do_GET()
    """
    def __init__( me, request, split_uri):
        me.request = request
        me.split_uri = split_uri
    #httpreq_console expected attrs:
    def req_send_error( me, http_errno, message ):
        me.request.error( http_errno)
    def req_send_header( me, response, headers =() ):
        request = me.request
        request.reply_code = response
        for k,v in headers:
           request[ k] = v
    def req_write( me, *items):
        push = me.request.push
        for item in items:
            if not isinstance( item, str):
                #item = iter_producer( iter(item) )
                continue    #ignore logfile_stub plz
            push( item)
    def req_get_info( me):
        return me.request.uri, me.request.channel.addr
    def req_get_uri_maybesplit( me):
        return me.split_uri

# vim:ts=4:sw=4:expandtab
