from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured
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
