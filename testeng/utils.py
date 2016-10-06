#$Id$
import unittest

class AppTestResult( unittest._TextTestResult):
    "our test result respecting verbosity level to not show traceback always"
    def getDescription( me, test):
        return '\n\n' + unittest._TextTestResult.getDescription( me, test)
    def printErrors(me):
        if me.dots or me.showAll:
            me.stream.writeln()
        me.printErrorList( me.errors,  False)
        me.printErrorList( me.failures, True)
    def printErrorList( me, errors, isfailure):
        flavour = isfailure and 'FAIL' or 'ERROR'
        for test, err in errors:
            me.stream.writeln( me.separator1)
            me.stream.writeln( "%s: %s" % (flavour,me.getDescription(test)))
            if me.showAll or not isfailure:
                me.stream.writeln( me.separator2)
                me.stream.writeln( str( err) )


class AppTestRunner( unittest.TextTestRunner):
    def _makeResult( me):
        return AppTestResult( me.stream, me.descriptions, me.verbosity)

class AppTestCase( unittest.TestCase):
    destroyMethod = docString = setupMethod = testMethod = None
    def __init__( me):
        unittest.TestCase.__init__( me, methodName ='testRun') #lius 10m vdesno
    def setUp( me): me.setupMethod()
    def tearDown( me): me.destroyMethod and me.destroyMethod()
    def testRun( me): me.testMethod()
    def shortDescription( me):
        doc = "%s %s/%s" % ( me, me.docString, me.__class__.__name__)
        return doc.strip()

    def diff( me, result, expected, result_name ='result', expected_name ='expect', ):
        if result == expected: return False
        if isinstance( result, (tuple,list)) and isinstance( expected, (tuple,list)):
            keys = list(range( len(expected)))
        elif isinstance( result, dict) and isinstance( expected, dict):
            keys = iter(expected.keys())
        else: return True
        err=0
        print('diffing by items...')
        for k in keys:
            v = expected[k]
            try:
                rv = result[k]
            except (KeyError,IndexError):
                rv = '<NOT-SET>'
                ok = False
            else:
                ok = me.diff( rv, v)
            if not ok:
                print('key', k,':\n', result_name,':',rv, '\n', expected_name,':', v)
                err +=1
        if not err:
            print(' WARNING: diff as whole, no diff piece-by-piece ??!!')
        return True

    def assertEquals( me, a,b, **kargs):
        try:
            unittest.TestCase.assertEqual( me, a,b)
        except me.failureException:
            if not me.diff( a,b, **kargs):
                print(' WARNING: second diff gives no diff ??!!')
            raise

def testMain( testcases, verbosity =0, exit_on_error =True, no_stderr =False):
    import sys
    verbosity = max( verbosity, sys.argv.count('-v') )
    suite = unittest.TestSuite()
    for case in testcases:
        case.verbosity = verbosity
        suite.addTest( case)
    r = AppTestRunner( descriptions= True, verbosity= verbosity,
                        stream =no_stderr and sys.stdout or sys.stderr
                ).run( suite).wasSuccessful()
    if exit_on_error and not r:
        sys.exit( not r)
    return r

# vim:ts=4:sw=4:expandtab
