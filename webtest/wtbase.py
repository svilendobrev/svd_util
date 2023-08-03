import subprocess, os

import enum
class eReuseBrowser( enum.Enum):
    FOREVER  = enum.auto()      #make new once at start, reuse it over and over ; same as using None
    TESTCLASS= enum.auto()      #make new for each test-class, reuse within class
    TESTCASE = enum.auto()      #make new for each test-case, no reuse

#REUSE_BROWSER = False #'forever' # True =per-testclass # False=only-testcase

if 0:
  class hosts_ports:
    UIPORT = 15555
    UIHOST = 'localhost'
    UIHOST_PORT = f'{UIHOST}:{UIPORT}'
    HTTP_UIHOST_PORT = f'http://{UIHOST_PORT}/'

from unittest import TestCase as TC

from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
#https://www.selenium.dev/selenium/docs/api/py/webdriver_support/selenium.webdriver.support.expected_conditions.html
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
#from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions

from selenium.webdriver.support.ui import Select    #dropdowns are tricky

#XXX hack to avoid children webdrivers be killed with ctrl-C on this
try: from . import disown_child_service #as module
except ImportError: import disown_child_service #or free script

class _forever:
    browser = None

class WebTestCase( TC):
    #browsers = ['firefox',]
    #implicit_wait = 30

    REUSE_BROWSER       = eReuseBrowser.TESTCASE
    #REUSE_BROWSER       = eReuseBrowser.FOREVER
    KEEP_OLD_BROWSERS   = False
    NEW_TAB = False
    # TODO maybe new window/tab every time , if not False?

    browser = None
    @classmethod
    def _setupServer( me):
        #def custom( req, req_body, res, res_body):
        #    return res_body
        #    print( f'res_body : {res_body}')
        sw_options = dict(
            #ignore_http_methods= [ 'OPTIONS'],  # Capture all requests, including OPTIONS requests
#            custom_response_handler= custom,
            )
        options = Options()
        #options.headless = True #XXX or pass MOZ_HEADLESS=1 to manage.py    actualy useful for debug
        options.add_argument( '--width=1024')
        options.add_argument( '--height=768')
        #options.add_argument( '--browser')
        options.log.level = 'trace' #XXX: levels options https://developer.mozilla.org/en-US/docs/Web/WebDriver/Capabilities/firefoxOptions#Log
        options.set_preference( 'webdriver.log.driver', 'ALL')
        options.set_preference( 'devtools.console.stdout.content', True)
#       options.set_preference( 'webdriver.log.file', 'zzz.log')

        me.browser = webdriver.Firefox(
            #service_log_path= 'webtest.log',   default is geckodriver.log
            options= options,
            seleniumwire_options= sw_options
            )

    def tearDown( me):
        if not me.KEEP_OLD_BROWSERS:
            if me.REUSE_BROWSER == eReuseBrowser.TESTCASE:
                me.browser.quit()
                me.browser = None
        super().tearDown()

    @classmethod
    def tearDownClass( me):
        if 0:
            #actualy this is long gone.. it's nodejs that remains
            me.webapp_server.terminate()
            me.webapp_server.wait()
            subprocess.run( 'pkill -f node.*dyra4webtest'.split())
        if not me.KEEP_OLD_BROWSERS:
            if me.REUSE_BROWSER == eReuseBrowser.TESTCLASS:
                me.browser.quit()
                me.browser = None
        super().tearDownClass()
    @classmethod
    def setUpClass( me):
        super().setUpClass()
        if 0:
            #this spawns a node server and quits
            me.webapp_server = subprocess.Popen( ['npm', 'start', 'dyra4webtest',], cwd='./ui',
                                env= dict( os.environ,
                                    BROWSER= 'none',
                                    HOST= hosts_ports.UIHOST,
                                    PORT= str( hosts_ports.UIPORT),
                                    REACT_APP_FLEETPAL_ENV= 'webtest',
                                    ),
                                stdout= subprocess.PIPE, stderr= subprocess.STDOUT,)

        if me.REUSE_BROWSER == eReuseBrowser.TESTCLASS:
            me._setupServer()
        elif me.REUSE_BROWSER == eReuseBrowser.FOREVER:
            if _forever.browser:
                me.browser = _forever.browser
            else:
                me._setupServer()
                _forever.browser = me.browser

    #HTTP_UI = hosts_ports.HTTP_UIHOST_PORT
    HTTP_AUTO_TARGET = None
    def setUp( me):
        super().setUp()

        if me.REUSE_BROWSER == eReuseBrowser.TESTCASE:
            me._setupServer()

        if me.NEW_TAB:
            me._new_tab()
        # open application for every test
        if me.HTTP_AUTO_TARGET:
            me.browser.get( me.HTTP_AUTO_TARGET)
            me._title2testcase()

    if 0*'not tried':
        def _new_window( me):
            if 0:   #js-hacky-way
                me.browser.execute_script( 'window.open()')
                me.browser.switch_to_window( me.browser.window_handles[-1])
            else:
                me.browser.switch_to.new_window( 'window')

    def _new_tab( me):
        me.browser.switch_to.new_window( 'tab')
        ''' hacky-way:
            ctrl = Keys.CONTROL     #ctrl=Keys.COMMAND if Apple :/
            some-root-element.send_keys( ctrl + 't')
        or,
            ActionChains( driver ).key_down( ctrl).send_keys( 't' ).key_up( ctrl ).perform()
            https://stackoverflow.com/questions/21779470/open-new-tab-in-firefox-using-selenium-webdriver-on-mac
        '''

    def _titler( me, title): return title
    def _title2testcase( me, pfx ='', append =False):
        op = '+= " : " + ' if append else '='
        testcase_name = (me._subtest or me).id()
        title = pfx + me._titler( testcase_name)
        me.browser.execute_script( f'document.title {op} "{title}"')


    my2by = dict(
        id          = By.ID,
        name        = By.NAME,
        xpath       = By.XPATH,
        link        = By.LINK_TEXT,
        link_partial= By.PARTIAL_LINK_TEXT,
        tag         = By.TAG_NAME,
        tag_name    = By.TAG_NAME,
        classname   = By.CLASS_NAME,
        class_name  = By.CLASS_NAME,
        klas        = By.CLASS_NAME,
        _class      = By.CLASS_NAME,
        class_      = By.CLASS_NAME,
        css         = By.CSS_SELECTOR,
        css_selector= By.CSS_SELECTOR,
        selector    = By.CSS_SELECTOR,
        )

    def _element2by_key( me, **kv):
        assert len( kv)==1, kv
        by,key = list( kv.items() )[0]
        return me.my2by[ by], key

    def element( me, **kv):
        by,key = me._element2by_key( **kv)
        return me.browser.find_element( by, key)

    def keyboard( me, element, input_text):
        element.send_keys( input_text)
    def select( me, element, input_text):
        ''' 1: drv.find_element_by_xpath( "//select[@name='element_name']/option[text()='option_text']" ).click() or .../option[@value='2']"
            2: # s=Select( el) ; s.select_by_index or s.select_by_value or s.select_by_visible_text
            '''
        Select( element).select_by_value( input_text)
    def input( me, element, input_text):
        if element.tag_name == 'select':
            me.select( element, input_text)
        else:
            me.keyboard( element, input_text)
    def click( me, element):   #useless
        element.click()

    def wait_for_element_clickable( me, timeout_sec =30, **kv):
        by_key = me._element2by_key( **kv)
        #print( 111111, by_key)
        wait = WebDriverWait( me.browser, timeout_sec)
        return wait.until( EC.element_to_be_clickable( by_key))

    def wait_for_frame_then_switch_to_it( me, timeout_sec =30, **kv):
        by_key = me._element2by_key( **kv)
        wait = WebDriverWait( me.browser, timeout_sec)
        return wait.until( EC.frame_to_be_available_and_switch_to_it( by_key))

    def wait_for_url_change_and_settle( me, current_url, what ='', timeout_sec =30):
        wait = WebDriverWait( me.browser, timeout_sec)
        #see selenium.webdriver.support.expected_conditions: .until( any-callable( driver) )
        #wtbase.EC.url_changes( 'oldurl-exact')
        #url_to_be( 'newurl-exact')
        #url_contains( partial_url)
        #url_matches( pattern_regex)
        #title_contains( substring)
        #title_is( string-exact)
        if what: print( '..wait to change', what)
        wait.until( EC.url_changes( current_url))
        if what: print( '..wait to settle', what)
        wait.until( SettledCond( current_url))
        new_url = me.browser.current_url
        if what: print( '..settled', what, new_url)
        return new_url

    def wait_for_element_visible( me, timeout_sec =30, **kv):
        by_key = me._element2by_key( **kv)
        wait = WebDriverWait( me.browser, timeout_sec)
        wait.until( EC.visibility_of_element_located( by_key))

    def wait_for_alert( me, timeout_sec =3, ):
        wait = WebDriverWait( me.browser, timeout_sec)
        return wait.until( EC.alert_is_present())

    #browser.switch_to.frame( element or id or ..)
    #browser.switch_to.default_content()  = go back/parent

if 0:
  class example( WebTestCase):
    def test_page_title( me):
        me.assertIn( 'payform be', me.browser.title)

    def test_invalid_token( me):
        me._type( 'login', me.u1.email)
        me._click( 'sign-in-btn')

        invalid_token = '123456'
        me._type( 'token', invalid_token)
        me._click( 'sign-in-btn')

        e = me.browser.find_element_by_id( 'form-errors')
        errors = e.get_attribute( 'errors')
        me.assertEqual( errors, 'Invalid token for auth method: EMAIL_TOKEN')

    def test_invalid_email( me):
        me._type( 'login', 'zz')#+me.u1.email)
        me._click( 'sign-in-btn')

        e = me.browser.find_element_by_id( 'errs')
        me.assertEqual( e.text, 'Enter a valid email address.')

import time

class SettledCond:
    '''True when no url change for some settled_time
    use like:
        current_url = driver.current_url
        wait.until( wtbase.EC.url_changes( current_url))
        wait.until( SettledCond( current_url))
    '''
    def __init__( me, current_url, settled_time_s =1.0):
        me.settled_time_s = settled_time_s
        me.current_url = current_url
        me.reset( current_url)
    def reset( me, url):
        me.last_url = url
        me.due_time = time.time() + me.settled_time_s
    def __call__( me, driver):
        if me.last_url != driver.current_url:
            me.reset( driver.current_url )
        return time.time() >= me.due_time

# vim:ts=4:sw=4:expandtab
