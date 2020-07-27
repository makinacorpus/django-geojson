import math

import django
from django.core.exceptions import ImproperlyConfigured

try:
    from django.contrib.gis.db.models.functions import Intersection
except (ImportError, ImproperlyConfigured):
    Intersection = None
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.gzip import gzip_page
from django.core.exceptions import SuspiciousOperation
from django.core.exceptions import ImproperlyConfigured

try:
    from django.contrib.gis.geos import Polygon
except (ImportError, ImproperlyConfigured):
    try:
        from django.contrib.gis.geos.geometry import Polygon
    except (ImportError, ImproperlyConfigured):
        from .nogeos import Polygon

try:
    from django.contrib.gis.db.models import PointField
except (ImportError, ImproperlyConfigured):
    from .fields import PointField

from .http import HttpGeoJSONResponse
from .serializers import Serializer as GeoJSONSerializer
from . import GEOJSON_DEFAULT_SRID


class GeoJSONResponseMixin(object):
    """
    A mixin that can be used to render a GeoJSON response.
    """
    response_class = HttpGeoJSONResponse
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

    use_natural_keys = False

    with_modelname = True

    crs_type = 'name'

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        serializer = GeoJSONSerializer()
        response = self.response_class(**response_kwargs)
        queryset = self.get_queryset()

        options = dict(properties=self.properties,
                       precision=self.precision,
                       simplify=self.simplify,
                       srid=self.srid,
                       geometry_field=self.geometry_field,
                       force2d=self.force2d,
                       bbox=self.bbox,
                       bbox_auto=self.bbox_auto,
                       use_natural_keys=self.use_natural_keys,
                       with_modelname=self.with_modelname,
                       crs_type=self.crs_type)
        serializer.serialize(queryset, stream=response, ensure_ascii=False,
                             **options)
        return response


class GeoJSONLayerView(GeoJSONResponseMixin, ListView):
    """
    A generic view to serve a model as a layer.
    """
    @method_decorator(gzip_page)
    def dispatch(self, *args, **kwargs):
        return super(GeoJSONLayerView, self).dispatch(*args, **kwargs)


class TiledGeoJSONLayerView(GeoJSONLayerView):
    width = 256
    height = 256
    tile_srid = 3857
    trim_to_boundary = True
    """Simplify geometries by zoom level (dict <int:float>)"""
    simplifications = None

    def tile_coord(self, xtile, ytile, zoom):
        """
        This returns the NW-corner of the square. Use the function
        with xtile+1 and/or ytile+1 to get the other corners.
        With xtile+0.5 & ytile+0.5 it will return the center of the tile.
        http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_numbers_to_lon..2Flat._2
        """
        assert self.tile_srid == 3857, 'Custom tile projection not supported yet'
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return (lon_deg, lat_deg)

    def _parse_args(self):
        try:
            return [int(v) for v in (self.args[0], self.args[1], self.args[2])]
        except (ValueError, IndexError):
            try:
                return [int(v) for v in (self.kwargs['z'],
                                         self.kwargs['x'],
                                         self.kwargs['y'])]
            except (ValueError, TypeError, KeyError):
                # Raise suspicious, Django will return ``400 Bad Request``.
                error_msg = "Tile (z, x, y) parameters could not be processed."
                raise SuspiciousOperation(error_msg)

    def get_queryset(self):
        """
        Inspired by Glen Roberton's django-geojson-tiles view
        """
        self.z, self.x, self.y = self._parse_args()
        nw = self.tile_coord(self.x, self.y, self.z)
        se = self.tile_coord(self.x + 1, self.y + 1, self.z)
        bbox = Polygon((nw, (se[0], nw[1]),
                       se, (nw[0], se[1]), nw))
        bbox.srid = self.srid
        qs = super(TiledGeoJSONLayerView, self).get_queryset()
        qs = qs.filter(**{
            '%s__intersects' % self.geometry_field: bbox
        })
        self.bbox = bbox.extent

        # Simplification dict by zoom level
        simplifications = self.simplifications or {}
        z = self.z
        self.simplify = simplifications.get(z)
        while self.simplify is None and z < 32:
            z += 1
            self.simplify = simplifications.get(z)

        # Won't trim point geometries to a boundary
        model_field = qs.model._meta.get_field(self.geometry_field)
        self.trim_to_boundary = (self.trim_to_boundary and
                                 not isinstance(model_field, PointField) and
                                 Intersection is not None)
        if self.trim_to_boundary:
            if django.VERSION < (1, 9):
                qs = qs.intersection(bbox)
            else:
                qs = qs.annotate(intersection=Intersection(self.geometry_field, bbox))
            self.geometry_field = 'intersection'

        return qs
