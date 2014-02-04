from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.gzip import gzip_page

from .http import HttpJSONResponse
from .serializers import Serializer as GeoJSONSerializer
from . import GEOJSON_DEFAULT_SRID


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
    srid = GEOJSON_DEFAULT_SRID
    """ Geometry field to serialize """
    geometry_field = 'geom'
    """ Force 2D """
    force2d = False
    """ bbox """
    bbox = None
    """ bbox auto """
    bbox_auto = False

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        serializer = GeoJSONSerializer()
        response = self.response_class(**response_kwargs)
        options = dict(properties=self.properties,
                       precision=self.precision,
                       simplify=self.simplify,
                       srid=self.srid,
                       geometry_field=self.geometry_field,
                       force2d=self.force2d,
                       bbox=self.bbox,
                       bbox_auto=self.bbox_auto)
        serializer.serialize(self.get_queryset(), stream=response, ensure_ascii=False,
                             **options)
        return response


class GeoJSONLayerView(GeoJSONResponseMixin, ListView):
    """
    A generic view to serve a model as a layer.
    """
    @method_decorator(gzip_page)
    def dispatch(self, *args, **kwargs):
        return super(GeoJSONLayerView, self).dispatch(*args, **kwargs)
