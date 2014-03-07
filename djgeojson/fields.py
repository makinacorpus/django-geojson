try:
    from jsonfield.fields import JSONField
    HAS_JSON_FIELD = True
except ImportError:
    HAS_JSON_FIELD = False
from django.utils.translation import ugettext_lazy as _


if HAS_JSON_FIELD:

    class GeoJSONField(JSONField):
        description = _("Geometry as GeoJSON")

    try:
        from south.modelsinspector import add_introspection_rules
        add_introspection_rules([], ["^djgeojson\.fields\.GeoJSONField"])
    except ImportError:
        pass