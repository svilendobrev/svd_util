from rest_framework_extensions.mixins import NestedViewSetMixin as _NestedViewSetMixin

class NestedViewSetMixin( _NestedViewSetMixin):
    ''' Handle parent lookup values that can't be converted to parent model pk '''

    def filter_queryset_by_parents_lookups(self, queryset):
        try:
            return super().filter_queryset_by_parents_lookups(queryset)
        except (TypeError, ValueError):
            raise Http404


def reg2parent_as_nested( parent_router, suburl, viewset, base_name, parents_query_lookups):
    ''' this does:
    - prepend NestedViewSetMixin in the bases
    - if any permission-klas needs parent_lookups-from-url, replace it with new-made
        subclass with xxx_url_key = proper parents_query_lookups

    - WTF.. all @detail_route.. has their own permissions.. and they are empty/wrong
    '''
    #TODO: klas-names += parent_router??
    newviewset = type( viewset.__name__+'_nested', (NestedViewSetMixin, viewset), {})
    perms = []
    for perm in getattr( newviewset, 'permission_classes', ()):
        needed_parent_lookups = getattr( perm, 'needed_parent_lookups', None)
        if needed_parent_lookups:
            perm = type( perm.__name__+'_nested', (perm,), dict(
                        obtain_url_key_values= perm.obtain_parent_key_values4NestedViewSetMixin,
                        needed_parent_lookups= parents_query_lookups,
                        ))
        perms.append( perm)
    if perms:
        newviewset.permission_classes = perms
    return parent_router.register( suburl, newviewset, base_name=base_name,
            parents_query_lookups= list( parents_query_lookups.values())    #order?? XXX
            )


from rest_framework_extensions import routers
from rest_framework_extensions.utils import compose_parent_pk_kwarg_name

class NestedRegistryItem( routers.NestedRegistryItem):
    '''allow parents_query_lookups to contain empties and/or be shorter than hierarchy, i.e. with levels without url-lookups
    activate as:
    nesting.routers.NestedRegistryItem = nesting.NestedRegistryItem
    '''

    def get_parent_prefix( me, parents_query_lookups):
        levels = []
        current = me
        while current:
            pl = parents_query_lookups and parents_query_lookups.pop()
            if pl:
                levels.insert( 0, '(?P<{parent_pk_kwarg_name}>{parent_lookup_value_regex})'.format(
                        parent_pk_kwarg_name= compose_parent_pk_kwarg_name( pl),
                        parent_lookup_value_regex= getattr( current.parent_viewset, 'lookup_value_regex', '[^/.]+'),
                        ))
            levels.insert( 0, current.parent_prefix)
            current = current.parent_item
        return '/'.join( levels)

    def zget_parent_prefix( me, parents_query_lookups):
        'allow empty parents_query_lookups=[] i.e. root-level without url-lookup'
        if not parents_query_lookups: return me.parent_prefix
        return super().get_parent_prefix( parents_query_lookups)


# vim:ts=4:sw=4:expandtab
