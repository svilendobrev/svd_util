#sdobrev 2010

''' interface/protocol/API declaration language. Methods, arguments, results -
types, cardinality, optionality; inheritance, specialization, cloning. Use
visitors to do/generate all else.

    svilen.dobrev 2010

    methoddecl: name, argdecls, returns, features
    argdecl:    name, type/converter, optional/defaultvalue

abstract faces cannot be instantiated - only faces with all methods implemented
WARNING/TODO: implementation methods are NOT checked for compliance with the declaration

example:
class ChannelFace( FaceDeclaration):     #pure declaration - abstract face
    class Types( Types):
        channel = Types.intplus
        rate    = int, Types.minmax(-2,+2)

    new_channel = Method(   name = optional( Types.text)
                            ).returns( Types.channel)
    del_channel = Method( channel = Types.channel ).returns( bool)

class MoreChannelFace( ChannelFace):  #implementing one method, declaring one more - still abstract
    class Types( ChannelFace.Types):
        program = str
    like_program= Method(   program = Types.program,
                            dislike = optional( bool, False)
                        )
    def del_channel( me, channel):
        return me.doer.channel_delete( channel)

class TheChannelFace( MoreChannelFace):  #implementing all methods
    def new_channel( me, program, name =None, **kargs): ...
    def like_program( me, program, dislike =False): ...
'''

#from util
from struct import DictAttr, Struct
from dictOrder import dictOrder
import attr
import warnings

class Types( object):

    @classmethod
    def as_dict( me):
        'all declarations, uniq as of mro'  #unused??
        all = {}
        for klas in me.mro():   #leaf to root
            for k,m in vars(klas).items():
                if k in all or k.startswith('__'): continue
                all[k] = m
        return all

    class typedef( object):
        def __init__( me, type, *validators, **kw):
            me.type = type
            assert not isinstance( type, me.__class__)
            prevalidators = kw.pop( 'pretype_validators', None) or ()
            me.validators = [
                v.__get__(123) if isinstance( v, staticmethod) else v    #staticmethod still inside classdecl
                for v in validators ]
            me.prevalidators = [
                v.__get__(123) if isinstance( v, staticmethod) else v    #staticmethod still inside classdecl
                for v in prevalidators]

        def validate( me, v):
            for valider in me.prevalidators + [ me.type ] + me.validators + [ me._validate ]:
                if not valider: continue
                try: v = valider(v)
                except:
                    print 343333333333, valider, `v`
                    raise
            #print 4444444, `v`
            return v
        def _validate( me, v): return v
        __call__ = validate

        def choices( me):
            'if any finite choices'
            for v in me.prevalidators + me.validators:
                ch = getattr( v, 'choices', None)
                if callable( ch): ch=ch()
                if ch is not None: return ch
            return me._choices()
        def _choices( me):
            return None

        def __str__( me):
            r = me.type and str( me.type ).strip('<>') or ''
            if r.startswith( 'type '): r = r[5:].strip("'")
            r = '<typedef '+r
            for v in me.validators:
                r+= ':' + (getattr( v, '__name__', None) or str(v))
            return r+'>'
        @classmethod
        def convert( klas, arg):
            if isinstance( arg, klas): return arg
            if isinstance( arg, tuple): return klas( *arg)
            return klas( arg)

    class valuedef( object):
        is_optional = False
        default_value = None

        def __init__( me, type, typename =None):
            me.type = Types.typedef.convert( type)
            me.typename = typename

        def optional( me, default_value =None, is_optional =True ):
            me.is_optional = is_optional
            me.default_value = default_value
            return me

        def str( me, withname =False):
            r = str( me.type).rstrip('>')
            r = r.replace( '<typedef ', '<')
            if withname and me.typename:
                r = '<valuedef '+me.typename+': ' + r.lstrip('<')
            if me.is_optional:
                r+= '; optional'
                if me.default_value is not None:
                    r+= ' ='+str(me.default_value)
            return r+'>'
        __str__ = str

        @classmethod
        def convert( klas, arg):
            if isinstance( arg, klas): return arg
            return klas( arg)

        def _clone( me, type_or_valuedef):
            o = type_or_valuedef
            if not isinstance( o, me.__class__):
                return me.__class__( o, typename= me.typename)
            #change optionality etc
            return me.__class__( o.type, typename= me.typename
                                ).optional( default_value= o.default_value, is_optional= o.is_optional)

        def clone_new_types( me, types):
            if not me.typename:
                #warnings.warn( 'cant change unnamed type: '+str(me) )
                return me
            repl = types.get( me.typename)
            if not repl:
                #warnings.warn( 'not re-defined: '+str(me) )
                return me
            return me._clone( repl)

    ####################
    #various typedefs and validators:

    class enum( typedef):
        'this is also a mapper - if items is dict'
        def __init__( me, items, *validators, **kw):
            me.items_order = items
            assert items
            me._setup( items)
            Types.typedef.__init__( me, kw.pop( 'type', None), *validators)
        def _setup( me, items):
            if not isinstance( items, dict):
                items = ((k,k) for k in items)
            me.items = DictAttr( items)

        def _validate( me, v): return me.items[ v ]
        def _choices( me): return me.items.keys()
        def __str__( me):
            return '<'+me.__class__.__name__+' '+ ','.join( str(i) for i in me.items_order ) +' >'
    mapper = enum

    @staticmethod
    def min( vm):
        def min(v): assert v>=vm
        return min
    @staticmethod
    def max( vm):
        def max(v): assert v<=vm
        return max
    @staticmethod
    def minmax( vmin,vmax):
        def minmax(v):
            assert v>=vmin
            assert v<=vmax
        return minmax
    @staticmethod
    def positive( v):
        assert v>0
        return v
    @staticmethod
    def positive0( v):
        assert v>=0
        return v

    intplus = typedef( int, positive)
    intplus0= typedef( int, positive0)
    text    = typedef( str)
    text_stream = text

    class datestamp( typedef):
        def __init__( me, *validators):
            typedef.__init__( me, str, *validators)
        def _validate( me, v):
            assert len(v) == 4+2+2
            y,m,d = v[:4],v[4:6],v[6:]
            assert 2000 <= y <= 3000
            assert 1    <= m <= 12
            assert 1    <= d <= 31
            return y,m,d
        def __str__( me):
            return me.__class__.__name__

    class aliaser( object):
        '''aliases of x: a,b ; of y: c,d
        i.e. translating a,b into x; c,d into y ;
        unmatched goes trough'''
        def __init__( me, valkeys, ignorecase =True,
                hidden =False    #dont show up choices - in forms etc
            ):
            me.ignorecase = ignorecase
            me.hidden = hidden
            me._map = _map = {}
            for v,kk in valkeys.items():
                if isinstance( kk, basestring): kk = kk.split()
                _map.update( (me.lower(k), v) for k in kk )
        def lower( me, v):
            if me.ignorecase and isinstance( v, basestring): v = v.lower()
            return v
        def choices( me):
            if me.hidden: return None
            return me._map.keys()
        def get( me, v):
            return me._map.get( me.lower(v), v)
        __call__ = get
        def __str__( me):
            r = 'aliaser( '+','.join( (k or "''") for k in sorted( me._map.keys() ))
            if me.ignorecase: r += '; ignorecase'
            return r+')'

    @staticmethod
    def lowercase( v):
        if isinstance( v, basestring): v = v.lower()
        return v


import types as _types
class _Meta4Types_auto( type):
    def __new__( meta, name, bases, dict_):
        dict_ = dict( (k, Types.typedef.convert( v))
                for k,v in dict_.iteritems()
                if not k.startswith( '__') and not isinstance( v, (
                        _types.NoneType,
                        _types.FunctionType, _types.LambdaType, _types.GeneratorType, _types.MethodType, ))
                )
        return type.__new__( meta, name, bases, dict_)

class Types_auto( Types):
    '''all things declared inside become typedefs automagicaly, e.g.
    class T( Types_auto):
        size = int, positive0
    print T.size
     >>> <typedef 'int':positive0>
    '''
    __metaclass__ = _Meta4Types_auto



class MTypes:
    'wraps all (Types)attrs into valuedefs'
    def __init__( me, types): me.__types = types
    def __getattr__( me, k):
        t = getattr( me.__types, k)
        return Types.valuedef( t, typename= k)


if 0:
    #XXX this gymnastics if _types is not a module but a func
    #def _types():
    #    ...
    #    return locals().copy()
    class Types: pass
    _functype = type( _types)
    _types = _types()
    Types.__dict__.update( (k, isinstance(v,_functype) and staticmethod(v) or v) for k,v in _types.iteritems() )
    del _types

def optional( type, default_value =None):
    v = Types.valuedef.convert( type)
    return v.optional( default_value)


class Method( object):
    _returns = None
    #_inputs  = None
    name = None
    _doc = ''
    def __init__( me, **ka):
        me._inputs = me._convert_dict( ka) or {} #None
        me._features = []
    def features( me, *ff):
        me._features += ff
        return me
    def inputs( me, **ka):
        me._inputs.update( me._convert_dict( ka) )
        return me
    def returns( me, *a,**ka):
        'single or tuple or dict'
        assert not a or not ka
        if a:
            a = [ Types.valuedef.convert( x)
                    for x in a
                    if x is not None]
            if len(a)==1: a=a[0]
        me._returns = a or me._convert_dict( ka) or None
        return me
    def doc( me, text):
        me._doc = text
        return me

    def _convert_dict( me, ka):
        for k,v in ka.items(): ka[k] = Types.valuedef.convert( v)
        return ka

    def sorted_inputs( me, mandatory_first =False):
        key = None
        if mandatory_first:
            def key( (k,v) ): return v.is_optional, k
        return me._inputs and sorted( me._inputs.items(), key= key ) or ()

    def str( me, sep= ' ; ', sep4inputs =', ', inputs =True, returns =None, **kargs):
        r = [
            inputs and me._inputs and 'inputs: ' +sep4inputs.join( '%s=%s' % kv for kv in me.sorted_inputs( **kargs) ) ,
            (me._returns or returns) and 'returns: '+str( me._returns) ,
            me._features and ':'.join( me._features) ,
            me._doc      and '"'+ me._doc +'"' ,
            ]
        return sep.join( [x for x in r if x] ) or 'Method()'
    __str__ = __repr__ = str

    def strface( me, face, name =None, sepname =': ', **kargs):
        return face.__name__ +'.'+ (me.name or name) + sepname + me.str( **kargs)

    def validate( me, params, face, name =None):
        #if me.impl is None:
        #    raise RuntimeError( 'not implemented method: ' + me.strface( face,name))
        name = name or me.name

        extra = dict(params)
        missing = []

        #print 22222222, params
        r = {}
        if me._inputs:
            for k,vdecl in me._inputs.items():
                if k in params:
                    v = params[k]
                    #if isinstance(v,list): v = v[0]
                    try:
                        v = vdecl.type.validate( v)
                        #XXX ???
                        #if v is vdecl.default_value and not vdecl.is_optional:
                        #    raise KeyError( v)
                    except Exception, e:
                        facename = face.__name__
                        type = vdecl.type
                        #raise
                        raise RuntimeError(
                            '''cannot validate argument %(k)r of method %(facename)s.%(name)s: %(e)s
                            expected type: %(type)s''' % locals() )
                    del extra[k]
                elif vdecl.is_optional:
                    v = vdecl.default_value
                else:
                    missing.append( (k,vdecl))
                    continue
                r[k] = v

        if missing: raise RuntimeError( 'missing mandatory arguments: '
                        +','.join( k for k,d in missing)
                        +'\n in method ' + me.strface( face,name)
                    )
        if extra: raise RuntimeError( 'unknown extraneous arguments: '
                        +','.join( repr(k) for k in extra)
                        +'\n in method ' + me.strface( face,name)
                    )
        return r

    NONE = 'dont'
    def clone_new_args( me, inputs =(), returns =NONE, dont_inherit =False):
        'reinterpret using other set of args'

        if dont_inherit: xinputs = {}
        else: xinputs = me._inputs.copy()
        xinputs.update( inputs)

        xreturns = returns  #overwrite
        if not dont_inherit:
            if returns is me.NONE or returns is not None and not returns: xreturns = me._returns
            elif isinstance( returns, dict) and isinstance( me._returns, dict):
                #mix
                xreturns = me._returns.copy()
                xreturns.update( returns)
        if xreturns is me.NONE: xreturns = None

        x = me.__class__( **xinputs ).returns( xreturns ).features( *me._features ).doc( me._doc)
        x.name = me.name
        return x

    def clone_new_types( me, types ):
        'reinterpret using other set of arg-types/valuedefs'

        inputs = dict( (k,v.clone_new_types( types)) for k,v in me._inputs.items() )
        returns = me._returns
        if returns:
            if isinstance( returns, dict):
                returns= dict( (k,v.clone_new_types( types)) for k,v in returns.items() )
            elif isinstance( returns, (list,tuple)):
                returns= [ v.clone_new_types( types) for v in returns]
            else:
                returns= returns.clone_new_types( types)

        x = me.__class__( **inputs ).returns( returns ).features( *me._features ).doc( me._doc)
        x.name = me.name
        return x


class MetaFaceDeclaration( type):
    def __init__( klas, name, bases, dict_):
        for mdcl in klas.methods_walk():
            mdcl.decl.name = mdcl.name
        if dict_.get('DONT_CHECK_METHODS_AND_TYPES'): return

        if len(bases)==1: return
        fbases = [ b for b in bases if issubclass( b, FaceDeclaration) ]
        if len(fbases)<=1: return

        #check type name clashes between bases
        types = getattr( klas, 'Types', None) # kl
        dtypes = types and types.__dict__ or {}
        rtypes = dict( dtypes)
        for b in fbases:
            btypes = getattr( b, 'Types', None)
            if not btypes: continue
            for k in dir( btypes):
                if k.startswith('__'): continue
                bt = getattr( btypes, k)
                if k in dtypes:
                    t = dtypes[k]
                    if t is not bt:
                        bname = b.__name__
                        warnings.warn( 'duplicate typename %(k)r: %(bname)s:%(bt)s, %(name)s:%(t)s' % locals(), stacklevel=2)
                else:
                    rtypes[ k] = bt
        #flatten
        if not types or types is not klas.__dict__.get( 'Types'):
            klas.Types = Types()
            klas.Types.__dict__.update( rtypes)
        else:
            for k,m in rtypes.items():
                if k not in dtypes: setattr( klas.Types, k, m)
        klas.MTypes = MTypes( klas.Types)


        #check method name clashes between bases
        mets = klas.methods_dict()
        for b in fbases:
            bname = b.__name__
            for k,bm in b.methods_dict().iteritems():
                m = mets.get(k)
                mdecl = m.decl
                bmdecl = bm.decl
                if mdecl is not bmdecl:
                    warnings.warn( 'duplicate method %(k)r: %(bname)s:%(bmdecl)s, %(name)s:%(mdecl)s' % locals(), stacklevel=2)


class FaceDeclaration( object):
    __metaclass__ = MetaFaceDeclaration
    #DONT_CHECK_METHODS_AND_TYPES = 1
    @classmethod
    def implementation( me):
        return me

    @classmethod
    def belongs( klas, func):
        'use as do-nothing-decorator declaring face-belonginess'
        assert func.__name__ in klas.methods_dict(), func.__name__ + ' does no belong to face '+klas.__name__
        return func

    @classmethod
    def check_face_match( face, base):
        mface = face.methods_dict()
        mbase = base.methods_dict()
        missing_from_base = [ what.name
            for what in base.methods_walk()
            if mface.get( what.name) in (None, what.decl) ]
        extra_over_base = [ what.name
            for what in mface.values()
            if what.name not in base.methods_dict() ]
        face = face.__name__
        base = base.__name__
        if missing_from_base:
            warnings.warn( '%(face)s misses methods of %(base)s: %(missing_from_base)s' % locals(), stacklevel=2 )
        if extra_over_base:
            warnings.warn( '%(face)s has extra methods to %(base)s: %(extra_over_base)s' % locals(), stacklevel=2 )

    #typedeclaration = callable_type_or_converter_or_validator[,extra_validators]

    @classmethod
    def methods_walk( me):
        return me.methods_dict().values()

    @classmethod
    def methods_walk_instance( klas, inst =None):
        if inst is None or inst is klas:
            return klas.methods_walk()      #dont just copy/reinterpret
        _methods_walk = getattr( inst, '_methods_walk', klas._methods_walk)     #allow inst to be anything
        return _methods_walk( klas, inst= inst, raw= False)

    def methods_walk_self_instance( me):
        return me.methods_walk_instance( me)
    def methods_unimplemented( me):
        return [ what for what in me.methods_walk_self_instance() if what.impl is None]

    @classmethod
    def method_by_name( me, name):
        return me.methods_dict()[name]

    _methods_dict = None
    @classmethod
    def methods_dict( me, clear =False):
        r = not clear and me.__dict__.get( '_methods_dict') or None   #local klas attribute
        if r is None:
            me._methods_dict = r = dictOrder( (w.name, w)
                        for w in me._methods_walk( me, raw= True) )
        return r

    @staticmethod   #inheritable
    def _methods_walk( klas, inst =None, raw =False):
        if inst is None: inst = klas
        if raw:
            name_method_iterator = klas._methods_decl()
        else:
            name_method_iterator= ((w.name,w.decl) for w in klas.methods_walk() )
            #in theory, name_method_iterator may walk klas, or inst, or even else
        for k,m in name_method_iterator:
            impl = getattr( inst, k, None)
            #if inst is a klas, it would be unbound impl or Method or None (if not subklas at all)
            #if impl is m: impl = None   #??same as isinstance (impl, Method)
            if isinstance( impl, Method): impl= None
            yield Struct( face= klas, name= k, decl= m, impl= impl)
            #cases:
            # inst is the klas:     inst.k is klas.k (Method or unbound impl)
            # inst is a subklas:    inst.k may be new (Method or unbound impl), or klas.k (Method or unbound impl)
            # inst is instance of (sub)klas: inst.k may be bound impl, or a Method (new or klas.k) if unimplemented
            # inst is anything else:    inst.k may be bound impl, or (Method or None) if unimplemented


    @classmethod
    def _methods_decl( me):
        'all Method declarations, uniq as of mro'
        all = {}
        for klas in me.mro():   #leaf to root
            for k,m in vars(klas).items():
                if k in all or not isinstance( m, Method): continue
                all[k] = m
        return sorted( all.items() )


    @classmethod
    def replace_types( me, **newtypes):
        '''uses newtypes (as valuedefs) instead.
        warn: to make optional( bool) into explicit 3-state textual,
            do not use optional( bool, aliaser( True:t1,False:t2,else:t3))..
            needs optional( enum( t1:True,t2:False,t3:else))
        '''
        #assert not me.__dict__.get( '_methods_dict'), 'dont replace already used type, first inherit it'
        r = dictOrder()
        for w in me.methods_walk():
            w = Struct( w.__dict__)
            w.decl = w.decl.clone_new_types( types= newtypes)
            r[ w.name] = w
        me._methods_dict = r

    @classmethod
    def clone_new_args( me, method_names, **kargs4clone):
        for k in method_names:
            setattr( me, k, getattr( me, k).clone_new_args( **kargs4clone) )
        me.methods_dict( clear=True)

    ERROR_IF_UNDEFS = True
    def __init__( me):
        undefs = me.methods_unimplemented()
        if undefs and me.ERROR_IF_UNDEFS:
            raise RuntimeError, '\n'.join(
                ['missing implementations of these methods:' ] + [
                    '  ' + w.face.__name__+'.'+w.name +': '+ str(w.decl)
                        for w in undefs
                ] )

    @classmethod
    def _type_of_arg_in_method( me, methodname, argname):
        return me.method_by_name( methodname).decl._inputs[ argname].type


def validate_decor( func):
    name = func.__name__
    def valider( me, **kargs):
        meta = me.method_by_name( name)
        kargs = meta.decl.validate( kargs, meta.face, name)
        try:
            return func( me, **kargs)
        except:
            print 5555555555555, func
            raise
    valider.__name__ = name+'_validated'
    return valider


def validate( what, params):
    return what.decl.validate( params, what.face, what.name)
def prn( what): #name,decl,face,impl):
    return '%-30s %s' % (what.face.__name__+'.'+what.name, what.decl)
def doc( what): #name,decl,face,impl):
    return what.decl.strface( what.face, what.name, mandatory_first= True, sep= '\n    ', sepname= '\n    ' )

def url4webpy( face, pfx4url =None):
    if callable( pfx4url): pfx4url = pfx4url( face)
    pfx = pfx4url or ''
    if pfx: pfx+= '/'
    return [ ('^'+pfx +what.name, what.impl )
                for what in face.methods_walk() ]

def url_doco( face, only_undefs =False, pfx4url =None, separgs =' &', sepattrs= '\n    ', ):
    if callable( pfx4url): pfx4url = pfx4url( face)
    pfx = pfx4url or ''
    for what in face.methods_walk():
        if only_undefs and what.impl is not None: continue
        url = pfx
        if url: url += '/'
        url += '%-12s' % what.name
        method = what.decl
        args = [ '%s= %s' % ka for ka in method.sorted_inputs( mandatory_first=True) ]

        r = url
        if args:
            r += separgs.strip()=='&' and separgs.replace( '&','?') or separgs
            r += separgs.join( args )
        r = sepattrs.join( x for x in [ r,
            method._returns  and 'returns '+ str( method._returns),
            method._features and ':'.join( method._features),
            method._doc      and '"'+ method._doc + '"'
            ] if x )
        yield r

def test( url4webpy =url4webpy, url_doco =url_doco, **kargs):
    for fc in attr.subclasses( FaceDeclaration):
        print '=================', fc
        print '---dump'
        for what in fc.methods_walk(): print ' ', prn( what)
        for what in fc.methods_walk(): print ' ', doc( what)
        print '---url_patterns'
        for x in url4webpy( fc): print ' ', x
        print '---url_doco'
        for x in url_doco( fc, **kargs): print ' ', x

if __name__ == '__main__':

    class ChannelFace( FaceDeclaration):     #pure declaration - abstract face
        class Types( Types):
            channel= Types.intplus
            program = int
            rate    = int, Types.minmax(-2,+2)
        MTypes = MTypes( Types)

        new_channel = Method(
                        program = MTypes.program,
                        name    = optional( Types.text),
                        size    = Types.intplus
                        ).returns( bool )
        del_channel = Method(
                        channel = MTypes.channel
                        ).returns( bool )

    class MoreChannelFace( ChannelFace):  #implementing one method, declaring one more - still abstract
        Types = ChannelFace.Types
        MTypes = MTypes( Types)
        def del_channel( me, channel):
            print 'do del_channel', channel
            return True
        like_program= Method(
                        program = MTypes.program,
                        dislike = optional( bool, False)
                        )

    class TheChannel_impl( MoreChannelFace.implementation()):  #implementing all methods
        def new_channel( me, program, name =None, **kargs):
            print 'do new_channel', program, name
            return True
        @validate_decor
        def like_program( me, program, dislike =False):
            print 'do like_program', program, dislike


    test()
    print '----'*5
    def errtest( func, *args, **kargs):
        try:
            func( *args, **kargs)
        except RuntimeError, e: print e
        else: assert 0*'didnt raise error'

    errtest( MoreChannelFace )   #missing impl

    c = TheChannel_impl()
    c.like_program( program=1 )      #ok
    errtest( c.like_program, dislike=True )   #missing arg
    errtest( c.like_program, program=2, alabala=1 )      #extra arg
    errtest( c.like_program, program='ewqe' ) #err
    print '----'*5

    class T( Types_auto):
        size = int, Types.positive0
    print T.size
    print '----'*5

    class EhtChannel_impl( TheChannel_impl):
        pass

    #for x in url_doco( EhtChannel_impl): print x
    for x in EhtChannel_impl.methods_walk(): print prn( x)
    EhtChannel_impl.replace_types( program=str, channel= optional( EhtChannel_impl.Types.channel) )
    #for x in url_doco( EhtChannel_impl): print x
    for x in EhtChannel_impl.methods_walk(): print prn( x)

    class Empty_impl( MoreChannelFace):
        pass
    Empty_impl.replace_types( program=str, channel= optional( Empty_impl.Types.channel) )
    errtest( Empty_impl)   #missing impl


    ## combining Types in multiple inheritance
    class XFace( FaceDeclaration):
        class Types( Types):
            opa= float

    class X( XFace, MoreChannelFace):
        pass
    class Y( XFace, MoreChannelFace):
        class Types( Types):
            uha= str
    assert X.Types.opa is XFace.Types.opa
    assert X.Types.channel is MoreChannelFace.Types.channel
    assert Y.Types.opa is XFace.Types.opa
    assert Y.Types.channel is MoreChannelFace.Types.channel

    class Z( X, Y):
        class Types( Types):
            are= str
    assert Z.Types.opa is XFace.Types.opa
    assert Z.Types.channel is MoreChannelFace.Types.channel
    assert Z.Types.uha is Y.Types.uha
    print Z.MTypes.uha
    print Z.MTypes.channel

# vim:ts=4:sw=4:expandtab
