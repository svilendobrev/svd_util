#XXX beware: all this is imported too late - after all models etc have been processed
#the way to catch those as well, is in http://coverage.readthedocs.io/en/coverage-4.2/subprocess.html
# create a sitecustomize.py with: import coverage ; coverage.process_startup()
# somewhere in system pythonpath (before django/project is involved).. i.e. probably in virtualenv/lib/python3.x/
# then to turn on, before running python, export COVERAGE_PROCESS_START=.coveragerc
# and all this below is not needed

from django.conf import settings
from django.conf import global_settings
from django.test.utils import get_runner

from coverage import Coverage
coverage = Coverage( branch=True)

class CoverageRunner( get_runner( settings, getattr( settings, 'TEST_RUNNER0', global_settings.TEST_RUNNER ))):
    """usage: in settings.py:
            ###### coverage
            TEST_RUNNER0 = TEST_RUNNER_WHATEVER_IT_WAS
            TEST_RUNNER = 'svd_util.django.covrunner.CoverageRunner'
            COVERAGE_CODE_EXCLUDES = '''
                '''.split() #regex i.e. 'def __unicode__\(self\):', 'from .* import .*', 'import .*',

        running tests will produce .coverage ; it is read by 'coverage report'
        i.e. run this (makefile syntax):
            COV_EXCL = *site-pack* *env*/somevirtenv/src/* *migrations/* */management/* test/*  admin/* .hg*
        	coverage report --omit "$(subst $(SPC),$(COMMA),$(COV_EXCL))"  | grep -v "  *0  *0  *100%"
    """

    def run_tests( self, *a,**ka):
        for e in getattr( settings, 'COVERAGE_CODE_EXCLUDES', None) or ():
            coverage.exclude(e)
        coverage.start()
        results = super().run_tests( *a,**ka)
        coverage.stop()
        coverage.save()
        #coverage.report( show_missing=1)
        #if settings.COVERAGE_REPORT_HTML_OUTPUT_DIR: coverage.html_report( directory= settings.COVERAGE_REPORT_HTML_OUTPUT_DIR)
        return results

# vim:ts=4:sw=4:expandtab
