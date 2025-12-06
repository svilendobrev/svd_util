#sdobrev 2009
'model-description "language" + dialects + generator of equivalent model in java + SAX + sqlite'

#from util
from ..attr import issubclass, subclasses #, subclasses_in
from ..dicts import DictAttr
from .. import gencxx
from .. import xml2obj

class Type( DictAttr):
    type        = None
    noninput    = False     #completely ignored from walking
    is_user_key = False
    as_getKey   = as_getId = False
    no_save    = False     # ignored at save only
    no_save_but_value = None   # if not None, this value is saved
    no_dump    = False
    #default_value
    def convert( me, v, context):
        if me.type:
            v = unicode(v)  # XXX? if direct e3obj..
            v = me.type( v)
        return v

class Int( Type):
    type = int
class Long( Type):
    type = long
class Float( Type):
    type = float
class Bool( Type):
    type = bool
    def convert( me, v, context):
        'true,false, 0,1..'
        if isinstance( v, basestring):
            v = v.strip().lower()
            q = xml2obj.truefalse.get( v)
            if q is not None: return q
            v = int(v)
        return bool( v)

class Text( Type):
    type = str
class TextUni( Text):
    type = unicode
URL = Text

class TimeStamp( Text):
    pass

class BLOB( Text): pass


class TextLang( Text):
    type = unicode
    def convert( me, v, context):
        if not isinstance( v, basestring):
            v = xml2obj.get_from_langdict_any( v, context.lang)
        return v
        #return me.type( v)

########################
class Only: pass

class Dialect:
    name = 'default'
    def __init__( me, namemap =None, prefix ='', types =None, notapplicable =False, only =()):
        me.prefix = prefix
        me.map = namemap and namemap.copy() or {}
        me.types = types    #also from metaModel
        me.notapplicable = notapplicable
        me.only = only or []

    def ignore( me, iter):
        me.map.update( (k,None) for k in iter)

    def iter_name_type_extname( me):
        #XXX unspecified means same name
        for name,typ in sorted( me.types.iteritems()):
            extname = me.map.get( name, name)
            if extname is None or typ.noninput:
                continue    #ignore
            yield name, typ, extname

    def get_name_type_extname( me, name):
        typ = me.types[ name]
        extname = me.map.get( name, name)
        return name, typ, extname

    def __str__( me): return me.name

class Dialects: #( DictAttr):
    def __init__( me, all, types, klasname):
        me.all = DictAttr( all) #DictAttr.__init__( me, all)
        me.klasname = klasname
        me.default = Dialect( types=types)
        for k,a in all.items():
            a.name = klasname+'/'+k
        me.setuponly( all.values() )
    def setuponly( me, all):
        for a in all:
            for b in all:
                if a is b: continue
                b.ignore( a.only)
    def __getattr__( me, k):
        if k in me.all: return me.all[k]
        return me.default

    def notapplicable( me):
        me.default.notapplicable = True
        for d in me.all.values():
            d.notapplicable = True


class metaModel( type):
    def __new__( meta, name, bases, adict):
        types = {}
        dialects = {}
        for k,v in adict.iteritems():
            if issubclass( v, Type): types[k] = v = v()
            elif isinstance( v, Type): types[k] = v
            elif isinstance( v, Dialect):
                dialects[k] = v
                v.name = k
                v.types = types

        for k in types: del adict[k]
        adict[ 'types'] = types
        adict[ '_dialects'] = Dialects( dialects, types, name)

        if 'NO_MAPPING' in adict:
            adict[ '_dialects'].notapplicable()

        for b in bases:
            try:
                s = b.types
            except AttributeError: pass
            else:
                #only if not already there
                for k,v in s.iteritems():
                    types.setdefault( k,v)

        return type.__new__( meta, name, bases, adict)

class Model( object):
    __metaclass__ = metaModel

#########################

def dict_merge( org, new):
    r = org.copy()
    r.update( new)
    return r

class java:

    types = {
        Int:        'int', #'long',
        Long:       'long',
        TimeStamp:  'Date',
        Bool:       'boolean',
        Float:      'float',
        Text:       'String',
        TextUni:    'String',
        BLOB:       'byte[]',
        #Bitmap:     'Bitmap',
    }
    defaults = {
        'String'    : '""',
    }

    models_klas = 'Models'

    convertors = {
        Int:        'parseInt',
        Long:       'parseLong',
        TimeStamp:  'parseTimeStamp',
        Bool:       'parseBool',
        Float:      'parseFloat',
        'String':   'parseString',
    }

    default_sax_dialect = '?'   #PUT THIS in genmodel, and fix below _dialects.getattr to return if not found
    def gen_sax_parser( me, klas, dialect =''):
        namespace = None
        item_name = klas.__name__
        klas_name = item_name + (dialect and '_'+dialect)
        item_name = me.models_klas+'.'+item_name
        dialect = dialect or me.default_sax_dialect
        all = '''\
public class %(klas_name)s extends BaseSAXHandler {

    public %(item_name)s item = null;   //the last
    public void set_item( %(item_name)s i ) {
        item = i;
        _set_item( item);
    }
    @Override
    protected void _new_item() {    //override if inheriting
        set_item( new %(item_name)s() );
    }
'''
        dialect = getattr( klas._dialects, dialect)
        if dialect.notapplicable: return
        prefix = dialect.prefix

        start_paths = {}
        end_paths = {}

        #print prefix, dialect, dialect.map
        for prefix in isinstance( prefix, (tuple,list)) and prefix or [ prefix ]:
            for k,typ,extname in dialect.iter_name_type_extname():
                if not isinstance( extname, str):
                    print '!!!!!!!!', k, extname
                    continue

                #print dialect,item_name,k,typ,extname
                ######################
                #a.  b   : attr b of a
                #a/ .b   : attr b of a
                #a/ b    : subitem b of a
                #a.  c.d : attr d of c
                #a/  c.d : attr d of c

                assert extname.count('.')<=1
                extname = prefix + extname
                extname = extname.replace( '/.', '.')
                path = extname
                attr = None
                if 'a/b/c.d match just c.d': #else full
                    path = path.rsplit('/',1)[-1]
                    srcname = 'name'
                else:
                    srcname = 'path'
                if '.' in path:
                    path,attr = path.rsplit('.',1)

                (start_paths if attr else end_paths
                        ).setdefault( path, set()
                            ).add( (k, attr) )

                if not attr and isinstance( typ, TextLang):
                    start_paths.setdefault( path, set()
                            ).add( (None,'lang') )


            if prefix:
                start_paths.setdefault( prefix.strip('./'), set()
                        ).add( None)


        startElement = me.paths2ifs( srcname, klas, start_paths, True)
        endElement   = me.paths2ifs( srcname, klas, end_paths, False)

        if namespace: ifnamespace = '''\
            if (!"%(namespace)s".equals( namespace)) return;
        ''' % locals()
        else: ifnamespace = ''

        if startElement:
            all += '''
    void _startElement( String namespace, String name, String qualName, Attributes attrs) throws SAXException {
%(ifnamespace)s
%(startElement)s
    } //_startElement
'''
        if endElement:
            all += '''
    void _endElement( String namespace, String name, String qualName) throws SAXException {
%(ifnamespace)s
%(endElement)s
    } //_endElement
'''

        all += '''
} //%(klas_name)s'''
        return all % locals()

    def paths2ifs( me, srcname, klas, paths, with_attr ):
        r = ''
        for path,items in sorted( paths.items()):
            align = max(10-len(path),0)*' '
            if r: r+= '''\
        } else
'''
            r += '''\
        if ("%(path)s"%(align)s.equals( %(srcname)s)) {
''' % locals()
            arg = with_attr and 'attrs.getValue( "%(attr)s")' or 'buffer()'
            for item in sorted(items):
                if item is None:
                    r += '''\
            new_item();
'''
                    continue
                k,attr = item
                if not k:   #lang
                    r += '''\
            store_lang( attrs);
'''
                    continue
                typ = klas.types[k]
                r += me.assign_item( k, typ, arg=arg, indent='''\
            ''') % locals()

        if r: r += '''\
        }'''
        return r

    @staticmethod
    def namesize( klas):
        if not klas.types: return None
        return max( len(k) for k in klas.types)

    type_of_id = Int

    annotations = dict(
            #someattr = 'some_annotation'
        )

    as_getKey =True
    as_getId  =True

    def gen_model( me, klas):
        if klas._dialects.default.notapplicable: return
        item_name = klas.__name__
        all = '''\
public class %(item_name)s extends Model {
'''
    #public %(item_name)s() { super(); }

        as_getKey = as_getId = None
        for k,typ in sorted( klas.types.iteritems()):
            type = me.types[ typ.__class__]
            default = me.get_by_type( typ, me.defaults)
            if not default: default = ''
            else: default = ' = '+default
            anno = me.annotations.get( k)
            if anno: all += '''\
    %(anno)s
''' % locals()
            all += '''\
    public %(type)-10s %(k)s%(default)s;
''' % locals()
            if typ.as_getKey: as_getKey = k
            if typ.as_getId:  as_getId  = k
            if 'key' == k:  #Model i-face
                if type == 'String':
                    if not as_getKey: as_getKey = k
                else:
                    if not as_getId: as_getId = k
            continue

        if as_getId or as_getKey:
            if me.as_getKey and not as_getKey: as_getKey = '""+'+as_getId
            if me.as_getId:
                if not as_getId:  as_getId  = 'funk.fail( "dont call this"); return -1'
                else: as_getId = 'return '+as_getId
            idtype = me.types.get( me.type_of_id, me.type_of_id )
            if me.as_getKey: all += '''\
    @Override public String getKey()    { return %(as_getKey)s; }
'''
            if me.as_getId: all += '''\
    @Override public %(idtype)s getId()     { %(as_getId)s; }
'''
        if klas.types:
            namesize = me.namesize( klas)
            all += '''
    public String dump() { String s = super.dump();''' + ''.join( ('''
        s += "\\n '''+k.ljust( namesize) + ''' = " + %(k)s;''') % locals()
            for k,typ in sorted( klas.types.iteritems())
            if not typ.no_dump
            ) + '''
        return s;
    }
'''
        all += '''\
}
'''
        return all % locals()



    def save( me, filename, text):
        r = ''.join( [gencxx.CVShead, gencxx.AUTOGEN_STAMP % locals(), text, gencxx.VIMtail ])
        gencxx.save_if_different( filename, r)

    def save_klasi( me, mainklas, klasi, head ='', head0 ='', tail=''):
        me.save( mainklas+'.java', (head+ head0 + '''
public class %(mainklas)s {
''') % locals() + ''.join( ('''

static
'''+x.strip() ) for x in klasi if x) + ('''
} //%(mainklas)s
'''+ tail) % locals() )


    def save_models( me, mainklas, klasi =[], **k):
        klasi = klasi + [ me.gen_model( klas)
                    for klas in subclasses( Model) ]
        me.save_klasi( mainklas, klasi, **k)

    #saxes_args= {}
    def save_saxes( me, mainklas, dialect= '', klasi =[], **ka):
        klasi = [ me.gen_sax_parser( klas, dialect=dialect)
                    for klas in subclasses( Model) ] + klasi
        ka.setdefault( 'head0', '''
import org.xml.sax.Attributes;
import org.xml.sax.helpers.DefaultHandler;
import org.xml.sax.SAXException;
import java.util.ArrayList;
''')
        #import com.actual.app.model.%(models_klas)s;

        me.save_klasi( mainklas, klasi, **ka)

    ##########

    def get_by_type( me, typ, convertors):
        type = me.types[ typ.__class__]
        return convertors.get( typ.__class__,
                        convertors.get( type, '' ))

    def assign_item( me, name, typ, arg =None, indent ='', convertors =None, ljustify =15):
        current_value = 'item.'+name
        convertor = me.get_by_type( typ, convertors or me.convertors)
        if ';' not in convertor:
            if convertor and '%(arg)s' not in convertor:
                convertor += '( %(arg)s )'
            if ljustify: current_value = current_value.ljust( ljustify + len(current_value) - len(name) )
            convertor = ('''\
%(indent)s%(current_value)s = '''+convertor +''';
''')
        return convertor % locals()

    ############
    D=DictAttr
    sqlites = {
        'String': D( load= 'sqlite.sql2string(  %(arg)s, c)', create= 'TEXT', clause= lambda arg: 'sqlite.str1( '+arg+')' ),
        Int     : D( load= 'sqlite.sql2int(     %(arg)s, c)', create= 'INTEGER' ),
        #Long    : D( load= 'sqlite.sql2long(    %(arg)s, c)', create= 'LONG' ),
        Float   : D( load= 'sqlite.sql2float(   %(arg)s, c)', create= 'REAL' ),
        Bool    : D( load= 'sqlite.sql2bool(    %(arg)s, c)', create= 'INTEGER',  set ='sqlite.bool2sql' ),
        TimeStamp:D( load= 'sqlite.sql2TimeStamp( sqlite.sql2int( %(arg)s, c))', create= 'INTEGER', set= 'sqlite.TimeStamp2sqlI' ),
        BLOB    : D( load= 'sqlite.sql2blob( %(arg)s, c)', create= 'BLOB', ),
    }


    def sqlite( me, klas):
        dialect = klas._dialects.sqlite
        if dialect.notapplicable: return
        item_name = klas.__name__
        model_name = me.models_klas + '.' + item_name
        tablename = getattr( klas, '_tablename__', item_name)
        all = '''public
class %(item_name)s extends sqlite.Base {
    static String _tablename = "T4%(tablename)s";
    public Class modelClass() { return %(model_name)s.class; }
    public String tablename()  { return _tablename; }
    public String creation()   { return _makestmt; }
    public String[] colnames() { return _colnames; }
    public String[] coltypes() { return _coltypes; }

''' % locals()
        load = ''
        save = ''
        colnames = []
        coltypes = []
        pkey = []

        sqlites_get = dict( (k,d.load) for k,d in me.sqlites.iteritems() if d)

        for name,typ,extname in dialect.iter_name_type_extname():
            sqdef = me.get_by_type( typ, me.sqlites)
            if sqdef is None: continue
            if typ.is_user_key: pkey.append( (name,typ,extname) )
            current_value = 'item.'+name

            set = sqdef.get('set')
            arg = current_value
            if set: arg = set+'( '+current_value+ ')'
            name4save = '"%(extname)s"' % locals()
            save += '''\
        c.put( %(name4save)-16s, %(arg)s );
''' % locals()

            arg = 'c.getColumnIndex( "%(extname)s" )' % locals()
            load += me.assign_item( name, typ, arg= arg, convertors= sqlites_get, indent='''\
        ''') % locals()

            sqtype = sqdef.create
            colnames.append( extname)
            coltypes.append( sqtype)


        if not pkey:
            try:
                pkey.append( dialect.get_name_type_extname( 'key'))
            except KeyError: pass

        if pkey:
            all += '''
    public String whereBy( Model x ) {
        %(model_name)s item = (%(model_name)s)x;
        return ''' % locals() + '''
                +" and "+'''.join(
                ' "%(kextname)s = "+' % locals() + getattr( me.get_by_type( ktyp, me.sqlites), 'clause', str)( 'item.'+kname)
                for kname,ktyp,kextname in pkey) + ''' ;
    }
'''
            len_pkey = len( pkey)
            kname,ktyp,kextname  = pkey[0]
            kstr = getattr( me.get_by_type( ktyp, me.sqlites), 'clause', str)( 'item.'+kname)
            all += '''
    public String keyName() {
        int len_pkey = %(len_pkey)s;
        funk.assertTrue( len_pkey == 1);
        return "%(kextname)s";
    }
    public String whereIn( Collection<Model> cc) {
        int len_pkey = %(len_pkey)s;
        funk.assertTrue( len_pkey == 1);
        String s = "";
        for (Model x: cc) {
            %(model_name)s item = (%(model_name)s)x;
            if (funk.any(s)) s += ",";
            s+= %(kstr)s;
        }
        return "IN ( "+s+")";
    }
''' % locals()

        else:
            all += '''
    public String keyName() { return null; }
    public String whereIn( Collection<Model> cc) { return null; }
'''

        if 0:
            all += '''
    public String whereBy( ''' + ', '.join( me.types[ ktyp.__class__] +' '+kname
                                    for kname,ktyp,kextname in pkey) + ''' ) {
        return ''' + '''
                +" and "+'''.join(
                ' "%(kextname)s = "+' % locals() + getattr( me.get_by_type( ktyp, me.sqlites), 'clause', str)( kname)
                for kname,ktyp,kextname in pkey) + ''' ;
    }
'''

        '''
 PRAGMA table_info("T4PersonalChannel")
    ...> ;
    0|_id|integer|0||1
    1|freshness|real|0||0
    2|image|text|0||0
    3|is_locked|integer|0||0
    4|is_news|integer|0||0
    5|is_strict|integer|0||0
    6|key|integer|0||0
    7|name|text|0||0
    8|size|integer|0||0
'''

        make = ', "\n'.join( (8*' '+'+ "%s %s' % kv) for kv in zip( colnames,coltypes) )
        colnames.insert(0, '_id')
        coltypes.insert(0, 'integer')
        colnames = ','.join( ('\n'+8*' '+'"'+c+'"') for c in colnames)
        coltypes = ','.join( ('\n'+8*' '+'"'+c+'"') for c in coltypes)

        all += '''
    static String _makestmt = //"create table " + _tablename + " (" +
          "_id   integer primary key autoincrement, "
%(make)s"
        ;
    static String[] _colnames = { %(colnames)s
    };
    static String[] _coltypes = { %(coltypes)s
    };

    public ContentValues save( Model x, ContentValues c) {
        if (c==null) c = new ContentValues();
        %(model_name)s item = (%(model_name)s)x;
%(save)s
        return c;
    }
    //public Model factory() { return new %(model_name)s(); }   //optimize eventualy
    public Model load( Model x, Cursor c) {
        %(model_name)s item = (%(model_name)s)(x==null ? factory() : x);
%(load)s
        return item;
    }
} //%(item_name)s
''' % locals()

        return all

    if 0: '''
    //public Model load( Cursor c) { return load( new %(model_name)s(), c); }
    _load( (%(model_name)s)x, c);
    _save( (%(model_name)s)x, c);
    void _load( %(model_name)s item, Cursor c) {
%(load)s
    }
    void _save( %(model_name)s item, ContentValues c) {
%(save)s
    }
    public String whereBy( Model x) { return _whereBy( (%(model_name)s)x); }
'''


    def save_sqlites( me, mainklas, klasi =[], **ka):
        klasi = [ me.sqlite( klas)
                    for klas in subclasses( Model) ] + klasi
        if 1:
            klasi += [ '''\
void setup() {
/* example''' + ''.join('''
    new ''' + klas.__name__ + '();'
        for klas in subclasses( Model)) + '''
*/
} // statics apply when class is used, so call these from some class sure-used before anything else, e.g. the app
''' ]

        ka.setdefault( 'head0', '''
import android.content.ContentValues;
import android.database.Cursor;
import java.util.Collection;
''')
#import com.svilendobrev.jbase.funk;
#import com.svilendobrev.jbase.Model;
#import com.actual.app.model.Models;

        me.save_klasi( mainklas, klasi=klasi, **ka)
    #static initialization:
    #see http://www.satyakomatineni.com/akc/display?url=displaynoteimpurl&ownerUserId=satya&reportId=1027

if 0:
    class javahead:
        head0 = ''
        package = ''
        head1 = ''
        imports = {}    #name : from
        head2 = ''

        def javahead( org, imports ={}):
            if imports is None: imports = {}
            else: imports = dict( me.imports, **imports)
            return '\n'.join( x for x in [
                me.head0,
                me.package and 'package '+me.package+';\n',
                me.head1,
                ] + [ 'import '+v+';' for v in imports.values() ] + [
                me.head2
                ] if x )

# vim:ts=4:sw=4:expandtab
