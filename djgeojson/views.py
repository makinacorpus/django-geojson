from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.gzip import gzip_page

from .http import HttpJSONResponse
from .serializers import Serializer as GeoJSONSerializer


class GeoJSONResponseMixin(object):
    """
    A mixin that can be used to render a GeoJSON response.
    """
    response_class = HttpJSONResponse
    """ Select fields for properties """
    properties = []
    """ Limit float precision """
    precision = None
    """ Simplify geometries """
    simplify = None
    """ Change projection of geometries """
    srid = None
    """ Geometry field to serialize """
    geometry_field = 'geom'

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        serializer = GeoJSONSerializer()
        response = self.response_class(**response_kwargs)
        serializer.serialize(self.get_queryset(), stream=response,
                             properties=self.properties, simplify=self.simplify,
                             srid=self.srid, precision=self.precision,
                             geometry_field=self.geometry_field,
                             ensure_ascii=False)
        return response


class GeoJSONLayerView(GeoJSONResponseMixin, ListView):
    """
    A generic view to serve a model as a layer.
    """
    @method_decorator(gzip_page)
    def dispatch(self, *args, **kwargs):
        return super(GeoJSONLayerView, self).dispatch(*args, **kwargs)
