from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import (ValidationError,
                                    ImproperlyConfigured)
try:
    from leaflet.forms.widget import LeafletWidget
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


def geojson_geometry(value):
    geom_type = value.get('type')
    is_geometry = geom_type in (
        "Point", "MultiPoint", "LineString", "MultiLineString",
        "Polygon", "MultiPolygon", "GeometryCollection"
    )
    if not is_geometry:
        err_msg = u'%s is not a valid GeoJSON geometry type' % geom_type
        raise ValidationError(err_msg)


class GeoJSONFormField(JSONFormField):
    widget = LeafletWidget if HAS_LEAFLET else HiddenInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('validators', [geojson_geometry])
        super(GeoJSONFormField, self).__init__(*args, **kwargs)


class GeoJSONField(JSONField):
    description = _("Geometry as GeoJSON")
    form_class = GeoJSONFormField
    geom_type = 'GEOMETRY'
    dim = 2

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^djgeojson\.fields\.GeoJSONField"])
except ImportError:
    pass
