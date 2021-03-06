#sdobrev 2011
'extra os-level funcs - execresult, touch, ..'

def execresult( args, encoding =None):
    import subprocess, locale
    #return subprocess.Popen( args, stdout= subprocess.PIPE ).communicate()[0].strip()  #<py2.7
    r = subprocess.check_output( args )
    if not encoding: encoding= locale.getpreferredencoding()
    if encoding: r = r.decode( encoding)
    return r.strip()

def touch( f):
    import os
    return os.utime( f, None)

    total = f
    import time
    s = time.localtime()
    tm_year = s.tm_year
    tm_mon = tm_mday = 1
    tm_hour= int(total/3600)
    tm_min = int((total+29)/60)
    tm_sec = 0#int(total-tm_min*60)
    tm_wday= tm_yday= tm_isdst= -1

    s = tm_year, tm_mon, tm_mday,  tm_hour, tm_min, tm_sec,  tm_wday,tm_yday,tm_isdst
    tm = time.mktime(s)
    os.utime( f, (tm,tm) )

def save_if_different( filename, txt, makedirs =True,
        reader =lambda filename: open( filename).read(),
        writer =lambda filename,txt: open( filename, 'w').write( txt ),
        writer2=None,   #func( filename,...)
        ):
    if makedirs:
        import os.path
        fpath = os.path.dirname( filename)
        if fpath and not os.path.exists( fpath):
            os.makedirs( fpath )
    try:
        old = reader( filename)
    except IOError:
        old = None
    if txt != old:
        if writer: writer( filename,txt)
        if writer2: writer2( filename,txt)
        return True

def globescape( f):
    'as of fnmatch doc: no way to escape meta-chars.. hence replace with ?'
    for c in '[]*':
        f = f.replace( c,'?')
    return f

def makedirs( x, exist_ok =True):
    'exist_ok=True doesnt work.. being toooo smart. below py-2.7; py-3.5 is fixed'
    import os,errno
    try:
        os.makedirs( x)#, exist_ok =True)
    except OSError as e:
        if e.errno != errno.EEXIST or not exist_ok: raise

def withoutext( fname, *exts, **kargs):
    once = kargs.get('once', True)
    ignorecase = kargs.get('ignorecase', False)
    for e in exts:
        if ignorecase: e = e.lower()
        if (fname.lower() if ignorecase else fname).endswith( e):
            fname = fname[:-len(e)]
            if once: break
    return fname

#from distutils.dep_util import newer

# vim:ts=4:sw=4:expandtab
