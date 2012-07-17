#sdobrev 2006
'''forward-declared module.attr resolver.
common between static_type and plainwrap resolvers.

a klas has declarations of references (reftypes), and each of those
has a klas to refer to - or name of it when forward decl.

resolve() walks a namespace, for each klas under control,
for each of its reftypes, resolve it if forward declared,
looking in namespace or in klas.__module__ or extra namespaces.

resolve1() resolves a forward declared reftypes,
looking in namespace or in klas.__module__ or extra namespaces.
'''
from attr import issubclass
import sys
class Resolver( object):
    def finisher( me, typ, resolved_klas):
        pass
    def is_forward_decl( me, typ):
        raise NotImplementedError
        return name-to-be-resolved or None
    def klas_reftype_iterator( me, klas):
        raise NotImplementedError
        yield only-reference-types
    dbgpfx = ''
    def resolve( me, namespace,
            base_klas,
            exclude =(),
            debug =False,
            *namespaces
            ):
        for klas in namespace.itervalues():
            if not issubclass( klas, base_klas): continue
            if klas in exclude: continue
            modnamespace = sys.modules[ klas.__module__].__dict__
            for typ in me.klas_reftype_iterator( klas):
                name = me.is_forward_decl( typ)
                if name:
                    who = me._resolve1( name, typ,
                                        namespace, modnamespace, *namespaces,
                                        **dict( debug=debug))
                    if debug: print me.dbgpfx+'resolve', klas, typ
                    assert issubclass( who, base_klas)

    def resolve1( me, typ, *namespaces, **kargs):
        name = me.is_forward_decl( typ)
        return me._resolve1( name, typ, *namespaces, **kargs)
    def _resolve1( me, name, typ, *namespaces, **kargs):
        debug =kargs.get( 'debug', False)
        assert name
        if '.' in name:
            if debug: print me.dbgpfx, 'resolve: ignoring module in', name
            mod,name = name.rsplit('.',1)
        for namespace in namespaces:
            if name in namespace:
                who = namespace[ name]
                break
        else:
            raise KeyError, '%(typ)s: cant resolve %(name)s' % locals()
        me.finisher( typ, who)
        return who

# vim:ts=4:sw=4:expandtab
