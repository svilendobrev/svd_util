# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext as _
from ..dicts import dictAttr

null_and_blank = dict( null=True, blank=True)

def nullable( field_type, *args, **kargs):
    kargs.update(null=True, blank=True)
    return field_type(*args, **kargs)


def optional_text( field_type, *args, **kargs):
    #if not factory: factory = models.CharField
    kargs.update(blank=True)
    kargs.setdefault('default', '')
    return field_type( *args, **kargs)


def Link(to, **kwargs):
    kwargs.setdefault('on_delete', models.CASCADE)
    return kwargs.pop( 'Field', models.ForeignKey )(to, **kwargs)


def LinkOneToOne(to, **kwargs):
    kwargs.setdefault('on_delete', models.CASCADE)
    return kwargs.pop( 'Field', models.OneToOneField )(to, **kwargs)


def enum( items, *, max_length =20, upper =True, lower =False, **ka):
    if isinstance( items, str): items = items.split()
    assert not (upper and lower)
    if upper: items = [ i.upper() for i in items ]
    if lower: items = [ i.lower() for i in items ]
    all2 = list( zip( items,items))
    f = models.CharField( max_length= max( max_length, *(len(i) for i in items)), choices= all2, **ka )
    f.all = dictAttr( all2)
    return f

try:
    from django.db.models import JSONField as _JSONField    #dj3+
except:
    from django.contrib.postgres.fields import JSONField as _JSONField  #old
from django.core.serializers.json import DjangoJSONEncoder
def JSONField( *a, **ka):
    ka.setdefault( 'encoder', DjangoJSONEncoder)
    return _JSONField( *a, **ka)


class PreciousModelMixin(models.Model):
    class Meta:
        abstract = True

    deleted = models.BooleanField(_('deleted'), default=False, db_index=True)


def can_bulk( somedj_inst_or_klas):
    from django.db import connections
    if not isinstance( somedj_inst_or_klas, type): somedj_inst_or_klas = somedj_inst_or_klas.__class__
    connection = connections[ somedj_inst_or_klas.objects.db]
    return connection.features.can_return_ids_from_bulk_insert


def DUMP( x, *, pfx =0, unsorted =0, **ka):
    print( str(pfx or '')+'>>>>>', x)
    for field in x._meta.concrete_fields:
        v = getattr( x, field.name, None)
        if not unsorted and isinstance( v, dict): v = dict( sorted( v.items()))
        print( ' ', field.name, repr(v), **ka)

def DUMPALL( q, **ka):
    for x in q: DUMP( x, **ka)

#comparing model-instances

def is_equal( o1, o2, **ka):
    assert o1.__class__ is o2.__class__, (o1, o2)
    return as_dict( o1, **ka) == as_dict( o2, **ka)

def as_names( mklas, use_attname =False, with_primary_key =False, ignoring =()): #ignoring= list or func( field)
    'autoignoring pk/id by default, see with_primary_key=True'
    fname = use_attname and 'attname' or 'name'
    if not callable( ignoring):
        ignored_items = ignoring
        ignoring = lambda f: getattr(f,fname) in ignored_items
    return [ getattr(f,fname)
                for f in mklas._meta.concrete_fields
                if (not f.primary_key or with_primary_key) and not ignoring( f)
            ]

def as_dict( obj, as_names= as_names, dict =dict, **ka):
    'autoignoring pk/id by default, see with_primary_key=True'
    return dict( (k,getattr(obj,k)) for k in as_names( obj.__class__, **ka))

########

def get_field_multilevel( model, field_name):
    'get field-model of a.b.c - across relations'
    mnames = field_name.split('.')
    for mname in mnames[:-1]:
        #rel = getattr( model, mname ).field.remote_field #rel
        rel = model._meta.get_field( mname ).remote_field #rel
        model = rel.model
    lastfield_name = mnames[-1]
    return model, lastfield_name

########

#from django.db.models import Count, Case, When, IntegerField
def count_filtered( **filter):
    return models.Count( bool_by_filter( _then=1, _default= None, **filter))
            #Case(
            #    When( then=1, **filter),  #else null - ignored by Count
            #    output_field= models.IntegerField(),
            #    ))

def bool_by_filter( _then =True, _default =False, **filter):
    return models.Case(
                models.When( then= _then, **filter),
                default= _default,
                output_field= models.IntegerField(),
                )

class block_signal:
    ''' a context manager that blocks a signal '''
    def __init__(self, signal, receiver, sender, dispatch_uid=None):
        self.signal = signal
        self.receiver = receiver
        self.sender = sender
        self.dispatch_uid = dispatch_uid

    def __enter__(self):
        self.signal.disconnect(
            receiver = self.receiver,
            sender = self.sender,
            dispatch_uid = self.dispatch_uid,
        )

    def __exit__(self, type, value, traceback):
        self.signal.connect(
            receiver = self.receiver,
            sender = self.sender,
            dispatch_uid = self.dispatch_uid,
        )


#### virtual fields

class VirtualField:
    '''
    A field that is declared on the base abstract model but is
    customized depending on concrete model class namespace
    '''
    def __init__(self, factory):
        self.factory = factory

    def __call__(self, attrs):
        return self.factory(**attrs)



def virtual_fields_meta(base_meta):
    class VirtualFieldsMeta(base_meta):
        def __new__(cls, name, bases, attrs):
            attr_meta = attrs.get('Meta')

            fields = {
                k: v
                for base in reversed(bases)
                for k, v in vars(base).items()
                if isinstance(v, VirtualField)
            }
            fields.update(attrs)
            attrs = fields

            is_abstract = getattr(attr_meta, 'abstract', False)
            is_proxy = getattr(attr_meta, 'proxy', False)
            if not is_abstract and not is_proxy:
                for field_name, field_factory in attrs.items():
                    if not isinstance(field_factory, VirtualField):
                        continue
                    attrs[field_name] = field_factory(attrs)
            return super().__new__(cls, name, bases, attrs)
    return VirtualFieldsMeta


# vim:ts=4:sw=4:expandtab
