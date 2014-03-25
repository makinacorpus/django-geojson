import json
import re

from six import string_types

from django import template
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.fields import GeometryField

from .. import GEOJSON_DEFAULT_SRID
from ..serializers import Serializer, DjangoGeoJSONEncoder


register = template.Library()


@register.filter
def geojsonfeature(source, params=''):
    """
    :params: A string with the following optional tokens:
             "properties:field:srid"
    """
    geometry_field = 'geom'
    properties = []
    srid = GEOJSON_DEFAULT_SRID
    parse = re.search(r'((\w)+)(:(\w))?(:(\d))?', params)
    if parse:
        properties = [parse.group(1)]

    if source is None or isinstance(source, string_types):
        return 'null'

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

    return serializer.serialize(source, properties=properties,
                                geometry_field=geometry_field, srid=srid)
