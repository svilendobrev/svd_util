#$Id$
# -*- coding: utf8 -*-

'''
Машина за пускане на Тестове
Работи с параметри от командния ред или дадени на TestMainframe()
ползва се като се създаде обект TestMainframe()
'''
import unittest
from svd_util.mix import myTestCase4Function
# параметри от командния ред
from svd_util.config import Config

class Config( Config):
    _enable_type_conversion = False
    errors  = False
    all_cases = False
    module  = None
    case    = None
    sample  = None
    _help = '''
    errors    :: ( print traceback if error)
    all_cases ::  show all TestCases in the choosen module
    module=   :: ( име на модул, от който да се заредят тестовете )
    case= :: ( групата тестове, която да се пусне)
    sample=   :: ( 1 или няколко тест-а, които да се изпълнят от дадена група)
'''
config = Config()


class SampleBase( object):
    'Базов клас за Примери'
    ENGINE_ARGS = 'expect info name'.split()
    def __init__( me, **kargs):
        for k,v in kargs.iteritems():
            if k in me.ENGINE_ARGS:
                setattr(me, k, v)

from svd_util.struct import DictAttr

class TestBase( unittest.TestCase):
    'Базов тестови клас! Името на наследниците му, които ще бъдат пускани трябва да започват с Test_'
    case = None
    TESTOVE = []
    def test_me( me): pass
    def __call__( me, resulter):
        for test in me.TESTOVE:
            value = DictAttr( (k,v) for k,v in test.__dict__.iteritems() if k not in SampleBase.ENGINE_ARGS)
            me.case.setup( value, test.expect, test.info ).run( resulter)

############################
from svd_util.attr import issubclass

class TestMainframe( unittest.TestLoader):
    def __init__( me, module =None, testcase =None, sample =None):
        config.getopt()
        me.module_name = module or config.module
        me.testcase = testcase or config.case
        me.sample = sample or config.sample
        me.prevodach= {}
        'prevodach = { "човешко" име : име от модула } - Опростени имена на cases '

    def _importFromFile( me, name):
        assert name
        module = __import__( name)
        for k, v in vars( module).iteritems():
            if issubclass( v, TestBase):
                try:
                    n= v.__name__.split('_', 1)[1]
                    me.prevodach[ n.lower()] = v
                except IndexError:
                    pass
        return module

    def stripTestCase( me, testove):
        samples= me.sample.split(',')
        gotovi_primeri= []
        err= []
        for s in samples:
            if s == '': continue
            try:
                t= int( s)
                try:
                    if t and testove[t-1] not in gotovi_primeri: #XXX A edin test >1 pyt???
                        gotovi_primeri.append( testove[t-1])
                except IndexError:
                    err.append(t)
            except ValueError:
                for edin_test in testove:
                    if s == edin_test.name:
                        if not edin_test in gotovi_primeri:
                            gotovi_primeri.append( edin_test)
                    else:
                        if ( s not in err) and ( s not in [ m.name for m in testove]):
                            err.append(s)
        if err:
            print 40*'-'
            for e in err: print '\nНе е намерен пример: %(e)s '%locals()
        return gotovi_primeri

    def groupTests( me, module):
        if me.testcase and me.sample: # TestCase and Sample(s)
            klas= me.prevodach.get( me.testcase)
            klas.TESTOVE= me.stripTestCase( klas.TESTOVE)
            case= unittest.TestLoader().loadTestsFromTestCase( klas)
            suite= unittest.TestSuite( case)
        elif me.testcase and not me.sample: # TestCase
            tc= me.prevodach.get( me.testcase)
            suite= unittest.TestLoader().loadTestsFromName( tc.__name__, module= module)
        else: # All
            suite= unittest.TestLoader().loadTestsFromModule( module= module)
        return suite

    def runTest( me, exit_on_error =True): # see engine/testutils
        success = False
        try:
            k = me._importFromFile( me.module_name)
            if config.all_cases:
                print me.prevodach.keys()
                raise SystemExit
            suite = me.groupTests( k)
            success = unittest.TextTestRunner( verbosity= 2).run( suite).wasSuccessful()
        except Exception:
            raise
        if exit_on_error and not success:
            raise SystemExit, not success
        return success

if __name__ == '__main__':
    test = TestMainframe( module = config.module)
    test.runTest()

# vim:ts=4:sw=4:expandtab
