from __future__ import unicode_literals

from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import (ValidationError,
                                    ImproperlyConfigured)
try:
    from leaflet.forms.widgets import LeafletWidget
    HAS_LEAFLET = True
except:
    import warnings
    warnings.warn('`django-leaflet` is not available.')
    HAS_LEAFLET = False
try:
    from jsonfield.fields import JSONField, JSONFormField
except ImportError:
    class Missing(object):
        def __init__(self, *args, **kwargs):
            err_msg = '`jsonfield` dependency missing. See README.'
            raise ImproperlyConfigured(err_msg)

    JSONField = Missing
    JSONFormField = Missing


class GeoJSONValidator(object):
    def __init__(self, geom_type):
        self.geom_type = geom_type

    def __call__(self, value):
        err_msg = None
        geom_type = value.get('type') or ''
        if self.geom_type == 'GEOMETRY':
            is_geometry = geom_type in (
                "Point", "MultiPoint", "LineString", "MultiLineString",
                "Polygon", "MultiPolygon", "GeometryCollection"
            )
            if not is_geometry:
                err_msg = '%s is not a valid GeoJSON geometry type' % geom_type
        else:
            if self.geom_type.lower() != geom_type.lower():
                err_msg = '%s does not match geometry type' % geom_type

        if err_msg:
            raise ValidationError(err_msg)


class GeoJSONFormField(JSONFormField):
    widget = LeafletWidget if HAS_LEAFLET else HiddenInput

    def __init__(self, *args, **kwargs):
        geom_type = kwargs.pop('geom_type', 'GEOMETRY')
        kwargs.setdefault('validators', [GeoJSONValidator(geom_type)])
        super(GeoJSONFormField, self).__init__(*args, **kwargs)


class GeoJSONField(JSONField):
    description = _("Geometry as GeoJSON")
    form_class = GeoJSONFormField
    dim = 2
    geom_type = 'GEOMETRY'


class GeometryField(GeoJSONField):
    pass


class GeometryCollectionField(GeometryField):
    geom_type = 'GEOMETRYCOLLECTION'


class PointField(GeometryField):
    geom_type = 'POINT'


class MultiPointField(GeometryField):
    geom_type = 'MULTIPOINT'


class LineStringField(GeometryField):
    geom_type = 'LINESTRING'


class MultiLineStringField(GeometryField):
    geom_type = 'MULTILINESTRING'


class PolygonField(GeometryField):
    geom_type = 'POLYGON'


class MultiPolygonField(GeoJSONField):
    geom_type = 'MULTIPOLYGON'


try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^djgeojson\.fields\.(GeoJSONField|GeometryField|GeometryCollectionField|PointField|MultiPointField|LineStringField|MultiLineStringField|PolygonField|MultiPolygonField)"])
except ImportError:
    pass
