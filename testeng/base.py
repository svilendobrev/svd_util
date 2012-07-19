#$Id$
# -*- coding: utf8 -*-

class BaseState: pass
class BaseTestSample:
    '''one test sample with
        - test (input) values,
        - expected result
        - name of the test
        - ??? times the test the sample ?to repeat ?or what? NOT IMPLEMENTED YET
        - testData method to pretty print the actual data of the test sample
        - testResult method in case some specific printing/formatting of test result is needed
    ALL samples are expected to work over some initialState which is ELSEwhere.
    see: examples in engine/timed/test.py and model/simpleDB.py
    '''
    name = ''
    expected = None
    def testData( me): raise NotImplementedError
    def testResult( me, result):
        '''обикновено се използва при показване, когато резултатът и очакваното не се
        събират на един ред - за украсяване на debug изходите.'''
        raise NotImplementedError
#    def __str__( me): pass
    pass

SUBSEP = 4*'-'

class BaseTestCase( object):
    '''used as base class for app tests
       needs:
        me.setupEach( initialState's)
        me.testEach( testSample's)
        me.assertEquals
    '''
    verbosity = 0
    initialState = ()
    testSamples  = ()   # [ BaseTestSample's ]
    def __init__( me, initialState =None, testSamples =None):
        if initialState:
            me.initialState = initialState      # [ BaseState's ]
        if testSamples:
            me.testSamples = testSamples        # [ BaseTestSample ]
        me.currentSample = None

    initial_sortkey = None
    def setup( me):
        if me.verbosity>2: print
        initialState = me.initialState
        if me.initial_sortkey:
            initialState = sorted( initialState, key=me.initial_sortkey)
        for f in initialState:
            me.setupEach( f)
            if me.verbosity>2: print f

    def test( me):
        first = True
        for t in me.testSamples:
            import copy
            me.currentSample = copy.copy( t)
            if me.verbosity:
                if first:
                    print
                    first = False
                print SUBSEP, 'TEST', t.name,
            #expected = t.expected
#            mustNotTest = issubclass( expected.__class__, Exception)
#            if mustNotTest:
#                me.currentRes = result = me.assertRaises( expected.__class__, me.testEach, t)
#            else:
            me.currentRes = result = me.testEach( me.currentSample)
            expected = me.currentSample.expected    #see test_timed many objids case - why this is moved here
            if me.verbosity:    print result == expected and 'OK' or 'FAILED'
            if me.verbosity>1:
                a = getattr( t, 'testResult', None)
                if a: x = a( result) # result printing implemented in the sample
                else: x = 'Result: %(result)s ; Expected: %(expected)s'% vars()
                print t.testData(), x
                print me
#            if not mustNotTest:
            me.assertEquals( result, expected)

    currentRes = None   #always existing
    systemState = None
    def __str__( me):
        ''' Използва се за показване на резултата при грешен/неминал тест. '''
        if not me.currentSample: return ''

        res = '\n'.join( str(f) for f in me.initialState )
        result = me.currentRes
        sample = me.currentSample
        expect = sample.expected
        sample_name = sample.name

        title = getattr( me, 'title', '')
        systemState = me.systemState
        if callable( systemState): systemState = systemState()
        if systemState: res += '''
systemState: %(systemState)s'''
        res += '''
result: %(result)s
expect: %(expect)s
sample: %(sample)s
%(title)s
%(sample_name)r FROM'''     #след FROM се показва името на тест case-а
        return res % locals()

from .utils import AppTestCase
class Case( BaseTestCase, AppTestCase):
    ''' Това трябва да се наследява от конкретните тестове, където трябва да има методите:
    setupEach или setup (НИКОГА и двата едновременно)
    testEach или test (НИКОГА и двата едновременно)
    xxxEach вариантите се ползват ако съответните начално състояние/ test примери (samples)
    са колекция от еднотипни елементи отговарящи на протокола съответно на BaseState и
    BaseTestCase. В този случай този клас се грижи и за правилното изпечатване на начални
    състояния и тестови примери при различни нива на описателност (verbosity).
    Ако се ползват setup/test варианта, потребителят на класа сам се грижи за
    оправяне на изхода. Допустими са варианти setupEach с test или setup с testEach.
    виж за пример engine/timed/test.py, model/simpleDB.py
    '''
    def __init__( me, doc, inputDatabase, testingSamples):
        AppTestCase.__init__( me)
        BaseTestCase.__init__( me, inputDatabase, testingSamples)
        # following _must_ be set - in order AppTestCase to work
        me.docString = doc
        me.setupMethod = me.setup
        me.testMethod = me.test

# vim:ts=4:sw=4:expandtab
