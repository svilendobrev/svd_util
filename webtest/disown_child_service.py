#XXX hack to inject calling os.setpgrp at start of child geckodriver subprocess,
# so it stops belonging to parent process hence is not killed by ctrl-C of parent
# https://stackoverflow.com/questions/6011235/run-a-program-from-python-and-have-it-continue-to-run-after-the-script-is-kille
#not-working alternative is starting separate geckodriver + use webdriver.Remote, it can only reuse ONE stored session_id, cannot create more ; faking newSession command isn't useful

from selenium.webdriver.common.service import Service
_start = Service.start
import subprocess,os
_Popen = subprocess.Popen
class Popen( _Popen):
    def __init__( self, *a,**ka):
        super().__init__( *a,  **ka, preexec_fn= os.setpgrp)
def start( *a,**ka):
    try:
        subprocess.Popen = Popen    #patch
        return _start( *a,**ka)
    finally:
        subprocess.Popen = _Popen   #restore
Service.start = start

# vim:ts=4:sw=4:expandtab
