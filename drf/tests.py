from unittest import TestCase
from svd_util.dicts import dictAttr, dict_pop


from .srlzing import ModelSrlz_renames_Mixin

def f( name =None, source =None): return dictAttr( name= name, source= source )

class Test_ModelSrlz_renames( TestCase):
    ff = dict( (k,f(k,None)) for k in 'abc')

    class base:
        def get_fields( me): return dict( me.ff)
        def __new__( klas, serlz2model ={}, serlz2model_ignore_missing =False, serlz2model_include_only =False):
            klas.serlz2model = serlz2model
            klas.serlz2model_ignore_missing = serlz2model_ignore_missing
            klas.serlz2model_include_only = serlz2model_include_only
            return super().__new__( klas )
    base.ff = ff

    class S( ModelSrlz_renames_Mixin, base): pass

    def check( me, srlz, **expect):
        result = srlz.get_fields()
        me.assertEqual( result, expect)
    def checkRaises( me, srlz ):
        with me.assertRaisesRegex( AssertionError, "'y'"):
            result = srlz.get_fields()

    def test_empty__untouched( me):
        me.check( me.S(),
            **me.ff)
    def test_empty_incl__empty( me):
        me.check( me.S(
            serlz2model_include_only = True
            ), )
    def test_rename1__renamed1_with_rest_untouched( me):
        me.check( me.S(
            serlz2model = dict( d='b')
            ), **dict( dict_pop( me.ff, 'b'), d= f( 'b', source='b') ))
    def test_rename1_incl__renamed_only( me):
        me.check( me.S(
            serlz2model = dict( d='b'),
            serlz2model_include_only = True ,
            ), d= f( 'b', source='b') )
    def test_rename1missing_incl__raises( me):
        me.checkRaises( me.S(
            serlz2model = dict( x='y'),
            serlz2model_include_only = True ,
            ))
    def test_rename1missing_incl_ign__empty( me):
        me.check( me.S(
            serlz2model = dict( x='y'),
            serlz2model_include_only = True ,
            serlz2model_ignore_missing=True ,
            ), )
    def test_rename1ok1missing_incl_ign___renamed1ok_only( me):
        me.check( me.S(
            serlz2model = dict( d='b', x='y'),
            serlz2model_include_only = True ,
            serlz2model_ignore_missing=True ,
            ), d= f( 'b', source='b') )

# vim:ts=4:sw=4:expandtab
