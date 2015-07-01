import json
import re

from six import string_types

from django.core.exceptions import ImproperlyConfigured
from django import template

try:
    from django.contrib.gis.geos.libgeos import geos_version_info
    geos_version_info()

    from django.contrib.gis.geos import GEOSGeometry
    from django.contrib.gis.db.models.fields import GeometryField
except (ImportError, ImproperlyConfigured) as e:
    from ..nogeos import GEOSGeometry
    from ..fields import GeometryField

from .. import GEOJSON_DEFAULT_SRID
from ..serializers import Serializer, DjangoGeoJSONEncoder


register = template.Library()


@register.filter
def geojsonfeature(source, params=''):
    """
    :params: A string with the following optional tokens:
             "properties:field:srid"
    """
    parse = re.search(r'(?P<properties>((\w+)(,\w+)*)?)(:(?P<field>(\w+)?))?(:(?P<srid>(\d+)?))?', params)
    if parse:
        parse = parse.groupdict()
    else:
        parse = {}

    geometry_field = parse.get('field') or 'geom'
    properties = parse.get('properties', '').split(',')
    srid = parse.get('srid') or GEOJSON_DEFAULT_SRID

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
