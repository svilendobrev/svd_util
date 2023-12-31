#HACK XXX XXX beware
#SessionMiddleware makes authenticated-posts/puts to require CSRF..
#add this before SessionMiddleware in settings.MIDDLEWARE and remove CsrfViewMiddleware

from django.utils.deprecation import MiddlewareMixin
class DisableCSRF( MiddlewareMixin):
    def process_request( self, request):
        request._dont_enforce_csrf_checks = True

# vim:ts=4:sw=4:expandtab
