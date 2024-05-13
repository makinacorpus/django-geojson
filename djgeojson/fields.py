from django.core.exceptions import ValidationError
from django.db.models import JSONField
from django.forms.fields import InvalidJSONInput
from django.forms.fields import JSONField as JSONFormField
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext_lazy as _

try:
    from leaflet.forms.widgets import LeafletWidget
    HAS_LEAFLET = True
except ImportError:
    HAS_LEAFLET = False


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
        if not HAS_LEAFLET:
            import warnings
            warnings.warn('`django-leaflet` is not available.')
        geom_type = kwargs.pop('geom_type')
        kwargs.setdefault('validators', [GeoJSONValidator(geom_type)])
        kwargs.setdefault('initial', InvalidJSONInput(''))
        super(GeoJSONFormField, self).__init__(*args, **kwargs)


class GeoJSONField(JSONField):
    description = _("Geometry as GeoJSON")
    form_class = GeoJSONFormField
    dim = 2
    geom_type = 'GEOMETRY'

    def formfield(self, **kwargs):
        kwargs.setdefault('geom_type', self.geom_type)
        kwargs.setdefault('form_class', self.form_class)
        return super(GeoJSONField, self).formfield(**kwargs)


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
