import collections

from django.http import Http404

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

try:
    from django.urls.resolvers import NoReverseMatch #django 2.0
except ImportError:
    try:
        from rest_framework.compat import NoReverseMatch
    except ImportError:
        from django.core.urlresolvers import NoReverseMatch  # django <=1.11

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.pagination import LimitOffsetPagination as _LimitOffsetPagination
try:
    from rest_framework.decorators import list_route as _list_route
except ImportError:
    from rest_framework.decorators import action
    _list_route = action( detail=False)
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import exception_handler as _exception_handler



class HybridRouterMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._api_view_urls = collections.OrderedDict()

    def add_api_view(self, url):
        self._api_view_urls[url.name] = url

    def remove_api_view(self, name):
        del self._api_view_urls[name]

    def get_urls(self):
        urls = super().get_urls()
        urls.extend(self._api_view_urls.values())
        return urls

    def get_api_root_view(self, api_urls=None):
        list_name = self.routes[0].name
        api_root_dict = dict(
            (prefix, list_name.format(basename=basename))
            for prefix, viewset, basename in self.registry
        )
        api_view_urls = self._api_view_urls

        class APIRoot(APIView):
            _ignore_model_permissions = True
            permission_classes = (AllowAny,)

            def get(self, request, *args, **kwargs):
                ret = {}
                namespace = request.resolver_match.namespace
                for key, url_name in api_root_dict.items():
                    if namespace:
                        url_name = namespace + ':' + url_name

                    try:
                        ret[key] = reverse(
                            url_name,
                            args=args,
                            kwargs=kwargs,
                            request=request,
                            format=kwargs.get('format', None)
                        )
                    except NoReverseMatch:
                        # Don't bail out if eg. no list routes exist, only detail routes.
                        pass
                # In addition to what had been added, now add the APIView urls
                for key in api_view_urls:
                    ret[key] = reverse(
                        api_view_urls[key].name,
                        args=args,
                        kwargs=kwargs,
                        request=request,
                        format=kwargs.get('format', None)
                    )
                ret = collections.OrderedDict(
                    sorted(ret.items(), key=lambda x: x[0])
                )
                return Response(ret)
        return APIRoot.as_view()



def list_route(methods=None, **kwargs):
    """
    For compatibility with the less maintained drf-extensions router
    set is_for_list=True|False
    """
    methods = ['get'] if (methods is None) else methods

    _decorator = _list_route(methods=methods, **kwargs)

    def decorator(func):
        func = _decorator(func)
        func.is_for_list = True
        return func
    return decorator


def declare_fields(serializer, **fields):
    serializer._declared_fields.update(fields)


def add_detail_route(viewset, view, view_base_name=None, **lookup_attrs):
    name = view.__name__
    setattr(viewset, name, view)
    fields = {name: RelatedResourceUrlField(view_base_name, **lookup_attrs)}
    declare_fields(viewset.serializer_class, **fields)



class LimitOffsetPagination(_LimitOffsetPagination):
    max_limit = 100



class ActionViewMixin(object):
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.action(serializer)


# middleware
class DisableCSRF(MiddlewareMixin):
    def process_request(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)


class APIViewMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        cls = getattr(view_func, 'cls', None)
        if cls and issubclass(cls, APIView):
            self.view_class = cls
            return self.process_api_view(request, view_func, view_args, view_kwargs)
        return None


class APIError(APIException):
    status_code = HTTP_400_BAD_REQUEST

    def __init__(self, code, data=None, message=None):
        self.detail = dict(
            code=code,
            data=data,
            message=message or ''
        )


def exception_handler(exc, context):
    response = _exception_handler(exc, context)

    if isinstance(exc, APIError):
        response.data = exc.detail
    if isinstance(exc, ValidationError):
        response.data = dict(
            code='INVALID',
            data=exc.detail
        )
    return response

from .fields import *
from .hyperlink import HyperlinkedModelSerializer

#gone, see glueing.py
#def make_serializer(viewset_bases, name):
#def make_viewset(name, bases):

# vim:ts=4:sw=4:expandtab
