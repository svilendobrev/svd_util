#sdobrev ~2004

'mix-in for test - single and multiple cases per instance'

class myTestCase4Function:#( unittest.TestCase):
    'use: klas.setup( value=, expect=, name=).run( resultcollector )'
    @classmethod
    def setup( klas, value, expect, name):
        me = klas( '_runTest' )
        me.value = value
        me.expect = expect
        me.name = name
        return me

    def do( me, value, expect):
        'overload this!'
        return None

    str_value = repr
    str_expect= repr
    str_result = repr
    def _do( me, value, expect):
        result = me.do( value, expect)
        if result != expect:
            value = me.str_value( value)
            expect= me.str_expect( expect)
            result= me.str_result( result)
            me.assertEqual( result, expect,
               '''func( %(value)s ):
 result: %(result)s;
 expect: %(expect)s''' % locals() )

    def _runTest( me):                      #single: .value, .expect
        me._do( me.value, me.expect)
    def shortDescription(me): return str(me.name)

class myTestCase4Function4many( myTestCase4Function):#( unittest.TestCase):
    'use: klas.setup( cases=, name=).run( resultcollector )'
    @staticmethod
    def setup( me, cases, name):
        me = myTestCase4Function( '_runTest' )
        me.cases = cases
        me.name = asserttext
        return me
    def _runTest( me):                      #multiple: cases { value: expect }
        for value,expect in me.cases.items():
            me._do( value, expect)

# vim:ts=4:sw=4:expandtab
