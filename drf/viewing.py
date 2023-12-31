
class ListSerializer_ViewSet_Mixin( object):
    serializer_class_list = None    #list,readonly,defaults to usual serializer_class
    def get_serializer_class(self):
        return self.action == 'list' and self.serializer_class_list or super().get_serializer_class()

class FullSerializers_ViewSet_Mixin( object):
    'works for separate view and also for viewset, inherit before ListSerializer_ViewSet_Mixin'
    serializer_class_full = None
    serializer_class_list_full = None

    def get_serializer_class(self):
        islist = getattr( self, 'action', None) == 'list'
        full = self.serializer_class_list_full if islist else self.serializer_class_full
        #XXX if .*_full are not set, being list has priority over being full
        return 'full' in self.request.query_params and full or super().get_serializer_class()


from rest_framework.permissions import SAFE_METHODS

class OutputSerializer_ViewSet_Mixin(object):
    serializer_class_output = None

    def get_serializer_class(self):
        s = getattr( self, 'serializer_class_output', None)
        if s and self.request.method in SAFE_METHODS:
            return s
        return super().get_serializer_class()

    #TODO create() uses inserlz for output... autoswicth it by default, but allow no switch

from rest_framework import viewsets, mixins, response, serializers

class NoCreate_ModelViewSet(
        mixins.ListModelMixin,
        mixins.UpdateModelMixin,
        mixins.DestroyModelMixin,
        mixins.RetrieveModelMixin, viewsets.GenericViewSet ):
    pass

class NoDelete_ModelViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        mixins.UpdateModelMixin, viewsets.GenericViewSet ):
    pass

class NoUpdate_ModelViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        mixins.DestroyModelMixin, viewsets.GenericViewSet ):
    pass

class NoUpdateDelete_ModelViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin, viewsets.GenericViewSet ):
    pass


class CreateIO_ModelAPIMixin( mixins.CreateModelMixin):
    """
    Create a model instance.. but:
    - perform_create also has request, and returns the output serializer-instance or data
    - status_created = whatever --- None is OK
    """
    status_created = mixins.status.HTTP_201_CREATED
    def create( self, request, *args, **kwargs):
        serializer = self.get_serializer( data= request.data)
        serializer.is_valid( raise_exception=True)
        result = self.perform_create( serializer, request)
        if isinstance( result, serializers.Serializer):
            serdata = result.data
            headers = self.get_success_headers( serdata)
        else:
            serdata = result
            headers = {}
        return response.Response( serdata, status= self.status_created, headers= headers)
    post = create

    def perform_create( self, serializer, request):
        serializer.save()
        return serializer

# vim:ts=4:sw=4:expandtab
