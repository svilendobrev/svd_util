#$Id: itercleanup.py,v 1.2 2004-03-08 15:44:20 sdobrev Exp $
# s.dobrev 2k4
# auto-cleaning iterator - workaround try-yield-finally conflict. see PEP 325, python.org/peps

_empty_method = lambda *a:None

class IterWithCleanup:
    def __init__( me, work_method, cleanup_method =_empty_method ):
        me.work_method = work_method
        me.cleanup_method = cleanup_method
    def close( me):
#        print 'del ', me
        try: me.cleanup_method()
        except: pass
        me.cleanup_method = _empty_method       #once only
    __del__ = close
    def __iter__( me):  return me
    def next( me):
#        print 'next', me
        return me.work_method()

if __name__ == '__main__':
    class Resource:
        def __init__( me): print 'obtain', me
        def close( me): print 'release', me
    import traceback

#use as:
    def somefunc( n, err =100):
        fptr = Resource()
        try:
            #...
            match_iter = iter( range(n) )   #another iterator

            ### it would be as easy as this...
            #for record in match_iter:
            #    ...do something else
            #    yield record
        #finally:
        #    try: fptr.close()
        #    except: pass
        ### instead:
            def work_method():
                r = match_iter.next()
                #do something else( fptr, record, ...)
                #example: raise error
                if r > err: raise TypeError, r
                return r
            #work_method = match_iter.next   if nothing else to do
            return IterWithCleanup( work_method,
                        cleanup_method= fptr.close )
        except:
            try: fptr.close()
            except: pass
            raise

    i=1
    print '\n sequence',i,': obtain, got,got,got, release, end'
    for a in somefunc(3): print 'got', a
    print 'end'

    i+=1
    print '\n sequence',i,': obtain, got,got,..., exception, handled, release'
    try:
        it = somefunc(5, err=3)
        for a in it: print 'got', a
        print 'end'
    except:
        traceback.print_exc()
        print 'handled'
        it.close()
        print

    i+=1
    print '\n sequence',i,': obtain, got,got,..., exception, handled, release, after'
    def x():
        for a in somefunc(5, err=2): print 'got', a
        print 'end'
    def y():
        try:
            x()
        except:
            traceback.print_exc()
            print 'handled'
    y()
    print 'after'

    i+=1
    print '\n sequence',i,': obtain, got,got,..., exception, release'
    for a in somefunc(5, err=2): print 'got', a
    print 'end'
    print

# vim:ts=4:sw=4:expandtab

