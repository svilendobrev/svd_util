#s.dobrev 2k4-5
'various descriptors for class-level-attributes'

class Descriptor4AutoCreatedReadonlyAttr( object):
    """ switchable attribute, like classmethod but on attributes:
        class A:
            class X_klas:
                ...
            x = Descriptor4AutoCreatedReadonlyAttr( X_klas)
        a = A()
        A.x gets X_klas
        a.x gets a._props.x, which is (lazy) autosetup as X_klas()
    """

    __slots__ = ( 'factory', 'name' )
    def __init__( me, factory, name):
        me.factory = factory
        me.name = name
    def __get__( me, obj, klas ):
        #print 'getattr', me.factory, klas
        #try:
            if obj is None: return me.factory
            _props = obj._props      #=me if same for all instances
            name = me.name
            try:
                me_obj = getattr( _props, name)
            except AttributeError:
                me_obj = me.factory()
                setattr( _props, name, me_obj)
            return me_obj
        #except:
        #    traceback.print_exc()

class Descriptor4AutoCreatedAttr( Descriptor4AutoCreatedReadonlyAttr):
    def __set__( me, obj, value):
        #print 'setattr', me.factory, value
        _props = obj._props      #=me if same for all instances
        return setattr( _props, me.name, value)

#######

class Descriptor4AutoCreatedReadonlySharedAttr( object):
    """ switchable attribute, like classmethod but on attributes:
        class A:
            class X_klas:
                ...
            x = Descriptor4AutoCreatedReadonlySharedAttr( X_klas)
        a = A()
        A.x gets X_klas
        a.x gets A.x.obj, which is (lazy) autosetup as X_klas() -
                same/shared for all instances of A
    """

    __slots__ = ( 'factory', 'obj' )
    def __init__( me, factory, name):
        me.factory = factory
    def __get__( me, obj, klas ):
        #print 'getattr', me.factory.__name__, klas
        if obj is None: return me.factory
        try:
            me_obj = me.obj
        except AttributeError:
            me_obj = me.obj = me.factory()
        return me_obj

class Descriptor4AutoCreatedSharedAttr( Descriptor4AutoCreatedReadonlySharedAttr):
    def __set__( me, obj, value):
        #print 'setattr', me.factory, value
        me.obj = value

#######

class Descriptor4ClassOnlyAttr( object):
    """ instance-inaccessible attribute:
        class A:
            class X:
                ...
            X= Descriptor4ClassOnlyAttr( X)
        a = A()
        A.X gets X
        a.X gets AttributeError
    """

    __slots__ = ( 'factory', 'name' )
    def __init__( me, factory, name):
        me.factory = factory
        me.name = name
    def __get__( me, obj, klas ):
        #print 'getattr', me.factory, klas
        if obj is None: return me.factory
        raise AttributeError, 'class-only attribute %s is instance-inaccessible' % me.name

# vim:ts=4:sw=4:expandtab
