# niki/sdobrev 2008/1997
'wave-like dependency-tree expression/rule re-calculation'

from dis import opname, HAVE_ARGUMENT
from types import *

def ToplevelNames( co ):
    """ToplevelNames( co ) -> list
    Detect all toplevel names used in a byte code.
    Return the list of names.

    """
    code = co.co_code
    names = co.co_names
    top = {}
    n = len(code)
    i = 0
    while i < n:
        c = code[i]
        op = ord(c)
        i = i+1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i+1])*256
            i = i+2
            if opname[op] == 'LOAD_NAME':
                top[ names[oparg] ] = None
    return top.keys()

class XCalcStorage:

    def __init__(self, xcalc=None, global_cx=globals()):
        self.__dirty = {}
        self._xcalc = xcalc
        self._globals = global_cx

    def AttachXCalc( self, xcalc, global_cx=None ):
        self._xcalc = xcalc
        if global_cx:
            self._globals = global_cx

    def PrepareCalc( self ):
        affect = {}
        wave = self.__dirty.keys()
        while wave:
            diff = {}
            for src in wave:
                diff.update( self._xcalc.GetDamage( src ) )
            # diff = diff - affect
            for k in diff.keys():
                if affect.has_key(k):
                    del diff[k]
            affect.update( diff )
            wave = diff.keys()
        # undef affected values
        for a in affect.keys():
            setattr( self, a, 0 )
            delattr( self, a )
        self.__dirty = {}

    def GetOrCalc( self, a ):
        if not self.__dict__.has_key( a ):
            self._xcalc.CalcOne( self, [a] )
        return self.__dict__[ a ]

    def Set( self, dst, v ):
        setattr( self, dst, v )
        self.__dirty[dst] = 1
        self.PrepareCalc()
        #if dst in ['MIN_SAL','DBEGIN']:
        #    print dst, '!'

    # required by XCalc
    def FireRule( self, dst ):
        try:
            v = eval( self._xcalc.rules[dst], self._globals, self.__dict__ )
        except KeyboardInterrupt:
            raise
        except StandardError, e:
            print dst, e.__class__.__name__, e,
            raise RuntimeError( '%s\nError in "%s": %s' % (self.__class__.__name__, dst, e ) )
        #print 'calc', dst, v
        self.Set( dst, v )

#/class XCalcStorage

class XCalcStorageI(XCalcStorage):
    """base suitable for Iterative Rulesets"""

    def Set( self, dst, v ):
        if v != self.__dict__.get( dst, None ):
            XCalcStorage.Set( self, dst, v )

#/class XCalcStorageI

class XCalc:

    def __init__(self):
        self.__rdeps = {}
        self._damage = {}

    def GetDamage( self, dst ):
        return self._damage.get(dst,{})

    def AddRule( self, dst, args ):
        self.__rdeps[dst] = args
        for var in args:
            try:
                dmg_var = self._damage[var]
            except KeyError:
                dmg_var = self._damage[var] = {}
            dmg_var[dst] = 1

    def CalcOne( self, obj, undef ):
        """calc all undef attributes
           obj - target object
           undef - set of attributes that need recalc (updated by obj_FireRule)
        """
        while undef:
            #print 'CalcOne', undef
            dst = undef[-1]
            try:
                dep = self.__rdeps[dst]
            except KeyError:
                raise AttributeError(dst)
            #print 'Rule', dst, dep
            for arg in dep:
                if not self.__rdeps.has_key(arg):
                    # arg might be "builtin"
                    continue
                if arg in undef:
                    raise RuntimeError( "%s: %s ?=%s" % (dst, dep, undef) )
                if not obj.__dict__.has_key( arg ):
                    # can't use rule if it has undefined argument
                    undef.append(arg)
                    break
            else:
                obj.FireRule( dst )
                undef.pop()

#/class XCalc

class XCalcR(XCalc):
    """XCalc with ruleset container
    rules - name:code mapping
    """

    def __init__(self):
        XCalc.__init__(self)
        self.rules = {}

    def AddRule( self, dst, src ):
        """
        dst - attribute name
        src - python code as string or code object
        """
        if type(src) == TupleType:
            args = src
        else:
            if type(src) == CodeType:
                co = src
            else:
                co = compile( src, "(%s) %s" % (dst,src), 'eval' )
            self.rules[dst] = co
            args = ToplevelNames(co)
            #print 'AddRule', dst, args
        XCalc.AddRule( self, dst, args )

if __name__ == '__main__':

    class RS1(XCalcR):

        def __init__( self ):
            XCalcR.__init__( self )

            self.AddRule( 'SubTotalVAT', 'total+vat' )
            self.AddRule( 'TotalVAT',    'SubTotalVAT-discountVAT' )
            self.AddRule( 'discountVAT', 'SubTotalVAT*DiscPercent/100' )

    class RS2(XCalcR):

        def __init__( self ):
            XCalcR.__init__( self )

            #self.AddRule('b', '(b+a/b)/2')
            self.AddRule('b', '1/a')

    class test1(XCalcStorage):

        def __init__( self, m ):
            XCalcStorage.__init__( self, m )

            self.total = 100
            self.vat = 20
            self.DiscPercent = 5

        def _getattr__( self, a ):
            return self.GetOrCalc(a)

    class test2(XCalcStorageI):

        def __init__( self, m ):
            XCalcStorageI.__init__( self, m )

            self.a = 0.0

        def _getattr__( self, a ):
            return self.GetOrCalc(a)

    xc1 = RS1()
    t = test1(xc1)
    try:
        t.boza
    except StandardError, e:
        print e
    #t.Recalc()
    t.GetOrCalc('TotalVAT')
    print t.total, t.SubTotalVAT, t.TotalVAT, t.discountVAT

    t.Set('total',200)
    t.Set('vat',40)
    #t.Recalc()
    #t.GetOrCalc('SubTotalVAT')
    t.GetOrCalc('TotalVAT')
    print t.total,
    try:        print t.SubTotalVAT,
    except:     print "t.SubTotalVAT",
    try:        print t.TotalVAT,
    except:     print "t.TotalVAT",
    try:        print t.discountVAT
    except:     print "t.discountVAT"

    t = test2(RS2())
    t.GetOrCalc('b')
    print t.b

# vim:ts=4:sw=4:expandtab
