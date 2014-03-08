try:
    from jsonfield.fields import JSONField, JSONFormField
    HAS_JSON_FIELD = True
except ImportError:
    HAS_JSON_FIELD = False
try:
    from leaflet.forms.widget import LeafletWidget
    HAS_LEAFLET = True
except:
    HAS_LEAFLET = False
from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _


if HAS_JSON_FIELD:

    class GeoJSONFormField(JSONFormField):
        widget = LeafletWidget if HAS_LEAFLET else HiddenInput

    class GeoJSONField(JSONField):
        description = _("Geometry as GeoJSON")
        form_class = GeoJSONFormField

    try:
        from south.modelsinspector import add_introspection_rules
        add_introspection_rules([], ["^djgeojson\.fields\.GeoJSONField"])
    except ImportError:
        pass
