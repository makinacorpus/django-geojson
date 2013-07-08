import json

from django import template
from django.db.models import Model
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.fields import GeometryField

from .. import GEOJSON_DEFAULT_SRID
from ..serializers import Serializer, DjangoGeoJSONEncoder


register = template.Library()


@register.filter
def geojsonfeature(source, geometry_field='geom', properties=None, srid=GEOJSON_DEFAULT_SRID):
    if source is None or isinstance(source, basestring):
        return 'null'

    properties = properties or []

    if isinstance(source, (GEOSGeometry, GeometryField)):
        encoder = DjangoGeoJSONEncoder()
        if source.srid != srid:
            source.transform(srid)
        feature = {"type": "Feature", "properties": {}}
        feature['geometry'] = encoder.default(source)
        return json.dumps(feature)

    serializer = Serializer()

    if not hasattr(source, '__iter__'):
        source = [source]

    return serializer.serialize(source, properties=properties, geometry_field=geometry_field, srid=srid)
