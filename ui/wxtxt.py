'unicode vs utf vs 1251, and depending on wx'

import wx

MODEL_ENCODING = 'utf-8'
PREFERRED_ENCODING = 'cp1251'

if wx.USE_UNICODE:
    def TXT(txt):
        if txt is None: return ''
        if isinstance(txt, unicode): return txt
        if hasattr( txt, 'UIstr'):
            txt = txt.UIstr()
        else:
            txt = str(txt)
        try:
            return unicode( txt, MODEL_ENCODING)
        except UnicodeDecodeError:
            return unicode( txt, PREFERRED_ENCODING)

    def UNICODE2STR(txt):
        if isinstance( txt, unicode):
            return txt.encode( MODEL_ENCODING)
        return txt
else:
    def TXT(txt):
        if txt is None: return ''
        if hasattr( txt, 'UIstr'):
            r = txt.UIstr()
        else:
            r = str( txt)
        try:
            r = unicode( r, MODEL_ENCODING)
        except UnicodeDecodeError:
            pass
        else:
            r = r.encode( PREFERRED_ENCODING)
        return r

    def UNICODE2STR(txt):
        txt = str(txt)
        try:
            txt = unicode( txt, MODEL_ENCODING)
        except UnicodeDecodeError:
            txt = unicode( txt, PREFERRED_ENCODING)
        return txt.encode( MODEL_ENCODING)

_ = TXT

# vim:ts=4:sw=4:expandtab
