#!/usr/bin/python

####
# 02/2006 Will Holcomb <wholcomb@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# 7/26/07 Slightly modified by Brian Schneider
# in order to support unicode files ( multipart_encode function / cStringIO)
"""
Usage:
  Enables the use of multipart/form-data for posting forms

Inspirations:
  Upload files in python:
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306
  urllib2_file:
    Fabien Seisen: <fabien@seisen.org>

Example:
  import MultipartPostHandler, urllib2, cookielib

  cookies = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                MultipartPostHandler.MultipartPostHandler)
  params = { "username" : "bob", "password" : "riviera",
             "file" : open("filename", "rb") }
  opener.open("http://wwww.bobsite.com/upload/", params)
"""

import urllib
import urllib2
import mimetools, mimetypes
#import os, stat
from cStringIO import StringIO


class MultipartPostHandler( urllib2.BaseHandler):
    DOSEQ = 1 # Controls how sequences are uncoded. If true, elements may be sequences (has multiple values)

    handler_order = urllib2.HTTPHandler.handler_order - 10 # needs to run first

    def http_request(self, request):
        data = request.get_data()
        if isinstance( data, dict): #data is not None and not isinstance( data, basestring):
            v_files = [ (k,v) for k,v in data.items() if isinstance(v,file) ]
            if not v_files:
                data = urllib.urlencode( data, self.DOSEQ)
            else:
                v_vars  = [ (k,v) for k,v in data.items() if not isinstance(v,file) ]
                boundary, data = self.multipart_encode( v_vars, v_files)

                contenttype = 'multipart/form-data; boundary=%s' % boundary
                if (request.has_header('Content-Type')
                   and request.get_header('Content-Type').find('multipart/form-data') != 0):
                    print "Replacing %s with %s" % (request.get_header('content-type'), 'multipart/form-data')
                request.add_unredirected_header('Content-Type', contenttype)

            request.add_data(data)
        return request

    @staticmethod
    def multipart_encode( vars, files, boundary = None, buf = None):
        NL='\r\n'
        if boundary is None: boundary = mimetools.choose_boundary()
        bound = '--'+str(boundary)
        r = []
        line = r.append
        for key, value in vars:
            line( bound)
            line( 'Content-Disposition: form-data; name="%s"' % key)
            line('')
            line( str(value))
        for key, fd in files:
            filename = fd.name.split('/')[-1]
            contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            line( bound)
            line( 'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename) )
            line( 'Content-Type: %s' % contenttype )
            #file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
            # line( 'Content-Length: %s' % file_size )
            line('')
            fd.seek(0)
            line( fd.read() )
        line( bound+ '--')
        line('')

        if buf is None: buf = StringIO()
        for l in r: buf.write( l+NL)
        buf = buf.getvalue()
        return boundary, buf

    https_request = http_request

if __name__=="__main__":
    import sys
    url = sys.argv[1]
    opener = urllib2.build_opener( MultipartPostHandler)
    print opener.open( url, dict( version= 7, data= file(sys.argv[2]) )).read()

