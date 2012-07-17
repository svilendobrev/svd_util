# 2006 sdobrev
'useful setup for gc-debugging'

import gc
#gc.set_debug( gc.DEBUG_LEAK)
gc.set_debug( gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_SAVEALL | gc.DEBUG_INSTANCES | gc.DEBUG_STATS ) #OBJECTS
def dump():
    gc.collect()
    import pprint
    for a in gc.garbage: pprint.pprint( a)

# vim:ts=4:sw=4:expandtab
