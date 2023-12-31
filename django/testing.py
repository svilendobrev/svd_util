
def get_verbosity_of_unittest( testcase):   #unittest hides this ; nothing to do with django
    '''usage:
    verbosity = common.get_verbosity_of_unittest( me)
    verbose = verbosity if isinstance( verbosity, bool) else verbosity>2
    '''
    result = testcase._outcome.result
    verbosity = getattr( result, 'verbosity', None)
    if verbosity is None:
        verbosity = 1 if result.dots else result.showAll  #base TestResult has only this: showAll=verbosity>1
    #else: verbose = verbosity >2    #0: nothing 1=dots 2:names 3:all
    return verbosity

def hack_verbosity4TestResult():
    ''' save the verbosity (it exists in runner but gets lost in result - although passed in.
        call this once, somewhere at module level in tests
        '''
    from unittest.result import TestResult
    TestResult.__init__org = TestResult.__init__
    def __init__(self, stream, descriptions, verbosity):
        self.verbosity = verbosity
        self.__init__org( stream, descriptions, verbosity)
    TestResult.__init__ = __init__


#from rest_framework.test import APIClient as _APIClient
import inspect
import traceback, os
from unittest import suite

class APIClient_tracking_requests_Mixin:
    '''usage:
    class APIClient( APIClient_tracking_requests_Mixin, _APIClient):
        IGNORED_FUNCNAMES = ..
        #URL_COV_FILE = ..
        pass
    APIClient.activate_hookEndTests()

    see also show_coverage which uses resulting URL_COV_FILE
    '''

    URL_COV_FILE  = '.test_url_cov'
    IGNORED_FUNCNAMES = 'setUp'.split()
    _test2reqs = {}

    def request(self, **request):
        req = tuple( request.get( k) for k in 'REQUEST_METHOD PATH_INFO'.split())
        stack = traceback.extract_stack()
        funcs = set( x[2] for x in stack)
        if not funcs.intersection( self.IGNORED_FUNCNAMES ):
            if 0:
                print( 111, '\n'.join( '+ '+str( (filename,functionname))
                    for filename, linenumber, functionname, srctext in stack ))
            try:
                p_funcname = p_filename = ''
                for f in inspect.stack():
                    funcname, filename = f.function, f.filename   #f[3],f[0]
                    if funcname == 'run' and 'unittest/case.py' in filename:
                        break
                    p_funcname, p_filename = funcname, filename
                thetest = ( p_filename, f.frame.f_locals['self'].__class__.__name__, p_funcname )
            finally:
                del f
            self._test2reqs.setdefault( tuple(thetest), set()).add( req)
        return super().request( **request)

    @classmethod
    def hookEndTests( klas):
        cwd = os.getcwd()
        try:
            t2r = eval( open( klas.URL_COV_FILE, 'r').read() )
        except OSError:
            t2r = {}
        t2r.update( ((os.path.relpath( k[0], cwd),) + k[1:],v) for k,v in klas._test2reqs.items())
        with open( klas.URL_COV_FILE, 'w') as fo:
            print('{', file=fo)
            for k,v in sorted( t2r.items()):
                print( k,':', list(sorted(v)), ',', file=fo)
            print('}', file=fo)
        klas._test2reqs.clear()

    @classmethod
    def activate_hookEndTests( klas):
        _run4hookEndTests = suite.TestSuite.run
        def run4hookEndTests( self, *a,**ka):
            r = _run4hookEndTests( self, *a,**ka)
            klas.hookEndTests()
            return r
        suite.TestSuite.run = run4hookEndTests

##############

# vim:ts=4:sw=4:expandtab
