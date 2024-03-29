#add per-virtualenv commandline history
#use as  PYTHONSTARTUP=/path/to/this/file  python ; or export that once then just run python
import sys,os
venv = os.getenv('VIRTUAL_ENV')
#if sys.version_info >= (3, 0) and
if (hasattr(sys, 'real_prefix')     # not always under 3.x
        or venv and venv.rstrip('/') == sys.prefix.rstrip('/')
    ): # in a VirtualEnv
    import atexit, os, readline
    PYTHON_HISTORY_FILE = os.path.join( os.environ.get('VENV_HOME') or sys.prefix, '_python_history')
    if os.path.exists( PYTHON_HISTORY_FILE):
        readline.read_history_file( PYTHON_HISTORY_FILE)
    atexit.register( readline.write_history_file, PYTHON_HISTORY_FILE)

# vim:ts=4:sw=4:expandtab
