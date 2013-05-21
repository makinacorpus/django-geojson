"""

    This code is a modified version of Daniel's GeoJSON serializer.

    http://djangosnippets.org/snippets/2596/

    Created on 2011-05-12
    Updated on 2011-11-09 -- added desrializer support

    @author: Daniel Sokolowski

    Extends django's built in JSON serializer to support GEOJSON encoding
"""
import logging
import json
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.core.serializers.base import DeserializationError
from django.core.serializers.json import (Serializer as JsonSerializer,
                                          DjangoJSONEncoder)
from django.utils.translation import gettext as _
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.fields import GeometryField
from django.core.serializers.python import Deserializer as PythonDeserializer
from django.core.serializers.python import _get_model
from django.utils.encoding import smart_unicode

import geojson
from shapely.geometry import asShape


def hasattr_lazy(obj, name):
    return any(name in d for d in (obj.__dict__, obj.__class__.__dict__))


class Serializer(JsonSerializer):
    def __init__(self, *args, **kwargs):
        super(Serializer, self).__init__(*args, **kwargs)
        self.collection = None
        self.objects = []

    def start_serialization(self):
        pass  # parent's method writes to stream !

    def end_serialization(self):
        precision = self.options.get('precision')
        floatrepr = json.encoder.FLOAT_REPR
        if precision is not None:
            # Monkey patch for float precision!
            json.encoder.FLOAT_REPR = lambda o: format(o, '.%sf' % precision)

        self.collection = geojson.FeatureCollection(features=self.objects)
        dump = geojson.dump(self.collection, self.stream)
        json.encoder.FLOAT_REPR = floatrepr  # Restore
        return dump

    def _geomfield(self, obj):
        is_geom = lambda f: isinstance(f, (GEOSGeometry, GeometryField))
        
        geomfield = None
        if hasattr_lazy(obj, 'geom'):
            geomfield = obj.geom
        elif hasattr_lazy(obj, 'the_geom'):
            geomfield = obj.the_geom
        else:
            geomattrs = [field for field in obj._meta.fields if is_geom(field)]
            if not geomattrs:
                raise ValueError("No GeometryField found in object")
            geomattr = geomattrs.pop(0)
            if geomattrs:
                logging.warn(_("More than one GeometryField found in object, used %s" % geomattr.name))
            geomfield = getattr(obj, geomattr.name)
        return geomfield

    def _preparegeom(self, geomfield):
        """ Geometry processing (in place), depending on options """
        # Optional geometry simplification
        simplify = self.options.get('simplify')
        if simplify is not None:
            geomfield = geomfield.simplify(tolerance=simplify, preserve_topology=True)
        # Optional geometry reprojection
        srid = self.options.get('srid')
        if srid is not None and srid != geomfield.srid:
            geomfield.transform(srid)
        return geomfield

    def _properties(self):
        """ Build properties from object fields """
        properties = dict(self._current.iteritems())
        if self.selected_fields is not None:
            properties = dict((k, v) for (k, v) in properties.items() if k in self.selected_fields)
        # Properties are expected to be serializable, force it brutally
        properties = json.loads(json.dumps(properties, cls=DjangoJSONEncoder))
        return properties

    def end_object(self, obj):
        pk = smart_unicode(obj._get_pk_val(), strings_only=True)
        if isinstance(obj, GeometryField):
            geomfield = obj
        else:
            geomfield = self._geomfield(obj)

        geometry = None
        if geomfield is not None:
            geomfield = self._preparegeom(geomfield)
            # Load Django geojson representation as dict
            geometry = dict(type=geomfield.geom_type, coordinates=geomfield.coords)

        properties = self._properties()
        # Add extra-info for deserializing
        properties['model'] = smart_unicode(obj._meta)
        properties['pk'] = pk
        # Add information from dynamic properties
        is_prop = lambda o, f: f in dir(obj)
        for f in self.selected_fields:
            if f not in properties and is_prop(obj, f):
                properties[f] = getattr(obj, f)
        # Build pure geojson object
        feature = geojson.Feature(id=pk,
                                  properties=properties,
                                  geometry=geometry)
        self.objects.append(feature)
        self._current = None

    def handle_field(self, obj, field):
        """
        If field is of GeometryField than encode otherwise call parent's method
        """
        value = field._get_val_from_obj(obj)
        if isinstance(field, GeometryField):
            self._current[field.name] = value
        else:
            super(Serializer, self).handle_field(obj, field)


def Deserializer(stream_or_string, **options):
    """
    Deserialize a stream or string of JSON data.
    """
    def FeatureToPython(dictobj):
        properties = dictobj['properties']
        model_name = properties.pop('model')
        # Deserialize concrete fields only (bypass dynamic properties)
        model = _get_model(model_name)
        field_names = [f.name for f in model._meta.fields]
        fields = {}
        for k, v in properties.iteritems():
            if k in field_names:
                fields[k] = v
        obj = {
            "model"  : model_name,
            "pk"     : dictobj['id'],
            "fields" : fields
        }
        shape = asShape(dictobj['geometry'])
        obj['geom'] = shape.wkt
        return obj
    
    if isinstance(stream_or_string, basestring):
        stream = StringIO(stream_or_string)
    else:
        stream = stream_or_string
    try:
        collection = json.load(stream)
        objects = map(FeatureToPython, collection['features'])
        for obj in PythonDeserializer(objects, **options):
            yield obj
    except GeneratorExit:
        raise
    except Exception, e:
        # Map to deserializer error
        raise DeserializationError(e)
