from django import template
from django.conf import settings
from django.utils import simplejson
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.fields import GeometryField

import geojson

from djgeojson.serializers import Serializer


register = template.Library()


@register.filter
def geojsonfeature(obj, srid=None):
    if obj is None or isinstance(obj, basestring):
        return 'null'

    if srid is None:
        # Try to guess SRID from potential settings
        srid = getattr(settings, 'API_SRID', 
                       getattr(settings, 'MAP_SRID', 
                               getattr(settings, 'SRID', 4326)))
    geojsonvalue = ''
    if isinstance(obj, (GEOSGeometry, GeometryField)):
        if obj.srid != srid:
            obj.transform(srid)
        feature = geojson.Feature(geometry=simplejson.loads(obj.geojson))
        geojsonvalue = geojson.dumps(feature)
    else:
        serializer = Serializer()
        geojsonvalue = serializer.serialize([obj], fields=[], srid=srid)
    return geojsonvalue
