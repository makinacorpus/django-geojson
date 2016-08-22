"""

    This code mainly comes from @glenrobertson's django-geoson-tiles at:
    https://github.com/glenrobertson/django-geojson-tiles/

    Itself, adapted from @jeffkistler's geojson serializer at: https://gist.github.com/967274
"""
try:
    from cStringIO import StringIO
except ImportError:
    from six import StringIO  # NOQA
import json
import logging

from six import string_types, iteritems

import django
from django.db.models.base import Model

try:
    from django.db.models.query import QuerySet, ValuesQuerySet
except ImportError:
    from django.db.models.query import QuerySet
    ValuesQuerySet = None

from django.forms.models import model_to_dict
from django.core.serializers.python import (_get_model,
                                            Serializer as PythonSerializer,
                                            Deserializer as PythonDeserializer)
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers.base import SerializationError, DeserializationError
from django.utils.encoding import smart_text
from django.core.exceptions import ImproperlyConfigured

try:
    from django.contrib.gis.geos import WKBWriter
    from django.contrib.gis.geos import GEOSGeometry
    from django.contrib.gis.db.models.fields import GeometryField
except (ImportError, ImproperlyConfigured):
    from .nogeos import WKBWriter
    from .nogeos import GEOSGeometry
    from .fields import GeometryField

from . import GEOJSON_DEFAULT_SRID
from .fields import GeoJSONField


logger = logging.getLogger(__name__)


def hasattr_lazy(obj, name):
    if isinstance(obj, dict):
        return name in obj
    return name in dir(obj)


class DjangoGeoJSONEncoder(DjangoJSONEncoder):

    def default(self, o):
        if isinstance(o, GEOSGeometry):
            return json.loads(o.geojson)
        else:
            return super(DjangoGeoJSONEncoder, self).default(o)


class Serializer(PythonSerializer):

    internal_use_only = False

    def start_serialization(self):
        self.feature_collection = {"type": "FeatureCollection", "features": []}
        if self.crs is not False:
            self.feature_collection["crs"] = self.get_crs()

        bbox = self.options.pop('bbox', None)
        if bbox:
            self.feature_collection["bbox"] = bbox

        self._current = None

    def get_crs(self):
        crs = {}
        crs_type = self.options.pop('crs_type', None)
        properties = {}
        if crs_type == "name":
            # todo: GeoJSON Spec: OGC CRS URNs such as "urn:ogc:def:crs:OGC:1.3:CRS84" shall be preferred over legacy identifiers such as "EPSG:4326":
            properties["name"] = "EPSG:%s" % (str(self.srid))
        else:  # preserve default behaviour
            crs_type = "link"
            properties["href"] = "http://spatialreference.org/ref/epsg/%s/" % (str(self.srid))
            properties["type"] = "proj4"
        crs["type"] = crs_type
        crs["properties"] = properties
        return crs

    def start_object(self, obj):
        self._current = {"type": "Feature", "properties": {}}

        # Try to determine the primary key from the obj
        # self.primary_key can be a function (callable on obj), or a string
        # if self.primary_key is not set, use obj.pk if obj is a Model
        # otherwise the primary key will not be used
        primary_key = None
        if self.primary_key and hasattr(self.primary_key, '__call__'):
            primary_key = self.primary_key(obj)
        elif self.primary_key and isinstance(self.primary_key, string_types):
            if isinstance(obj, Model):
                primary_key = getattr(obj, self.primary_key)
            else:
                primary_key = obj[self.primary_key]
        elif isinstance(obj, Model):
            primary_key = obj.pk

        if primary_key:
            self._current['id'] = primary_key

    def end_object(self, obj):
        # Add extra properties from dynamic attributes
        extras = []
        if isinstance(self.properties, dict):
            extras = [field for field, name in self.properties.items()
                      if name not in self._current['properties']]
        elif isinstance(self.properties, (list, tuple)):
            extras = [field for field in self.properties
                      if field not in self._current['properties']]

        for field in extras:
            if hasattr_lazy(obj, field):
                self.handle_field(obj, field)

        # Add extra-info for deserializing
        with_modelname = self.options.pop('with_modelname', True)
        if hasattr(obj, '_meta') and with_modelname:
            self._current['properties']['model'] = smart_text(obj._meta)

        # If geometry not in model fields, may be a dynamic attribute
        if 'geometry' not in self._current:
            if hasattr_lazy(obj, self.geometry_field):
                geometry = getattr(obj, self.geometry_field)
                self._handle_geom(geometry)
            else:
                logger.warn("No GeometryField found in object")

        self.feature_collection["features"].append(self._current)
        self._current = None

    def end_serialization(self):
        self.options.pop('stream', None)
        self.options.pop('properties', None)
        self.options.pop('primary_key', None)
        self.options.pop('geometry_field', None)
        self.options.pop('use_natural_keys', None)
        self.options.pop('crs', None)
        self.options.pop('srid', None)
        self.options.pop('force2d', None)
        self.options.pop('simplify', None)
        self.options.pop('bbox', None)
        self.options.pop('bbox_auto', None)
        self.options.pop('with_modelname', None)

        # Optional float precision control
        precision = self.options.pop('precision', None)
        floatrepr = json.encoder.FLOAT_REPR
        if precision is not None:
            # Monkey patch for float precision!
            json.encoder.FLOAT_REPR = lambda o: format(o, '.%sf' % precision)

        json.dump(self.feature_collection, self.stream, cls=DjangoGeoJSONEncoder, **self.options)

        json.encoder.FLOAT_REPR = floatrepr  # Restore

    def _handle_geom(self, value):
        """ Geometry processing (in place), depending on options """
        if value is None:
            geometry = None
        elif isinstance(value, dict) and 'type' in value:
            geometry = value
        else:
            if isinstance(value, GEOSGeometry):
                geometry = value
            else:
                try:
                    # this will handle string representations (e.g. ewkt, bwkt)
                    geometry = GEOSGeometry(value)
                except ValueError:
                    # if the geometry couldn't be parsed.
                    # we can't generate valid geojson
                    error_msg = 'The field ["%s", "%s"] could not be parsed as a valid geometry' % (
                        self.geometry_field, value
                    )
                    raise SerializationError(error_msg)

            # Optional force 2D
            if self.options.get('force2d'):
                wkb_w = WKBWriter()
                wkb_w.outdim = 2
                geometry = GEOSGeometry(wkb_w.write(geometry), srid=geometry.srid)
            # Optional geometry simplification
            simplify = self.options.get('simplify')
            if simplify is not None:
                geometry = geometry.simplify(tolerance=simplify, preserve_topology=True)
            # Optional geometry reprojection
            if geometry.srid and geometry.srid != self.srid:
                geometry.transform(self.srid)
            # Optional bbox
            if self.options.get('bbox_auto'):
                self._current['bbox'] = geometry.extent

        self._current['geometry'] = geometry

    def handle_field(self, obj, field_name):
        if isinstance(obj, Model):
            value = getattr(obj, field_name)
        elif isinstance(obj, dict):
            value = obj[field_name]
        else:
            # Only supports dicts and models, not lists (e.g. values_list)
            return

        if field_name == self.geometry_field:
            self._handle_geom(value)

        elif self.properties and field_name in self.properties:
            # set the field name to the key's value mapping in self.properties
            if isinstance(self.properties, dict):
                property_name = self.properties[field_name]
                self._current['properties'][property_name] = value
            else:
                self._current['properties'][field_name] = value

        elif not self.properties:
            self._current['properties'][field_name] = value

    def getvalue(self):
        if callable(getattr(self.stream, 'getvalue', None)):
            return self.stream.getvalue()

    def handle_fk_field(self, obj, field):
        related = getattr(obj, field.name)
        if related is not None:
            if self.use_natural_keys and hasattr(related, 'natural_key'):
                related = related.natural_key()
            else:
                if field.rel.field_name == related._meta.pk.name:
                    # Related to remote object via primary key
                    related = related._get_pk_val()
                else:
                    # Related to remote object via other field
                    related = smart_text(getattr(related, field.rel.field_name), strings_only=True)
        self._current['properties'][field.name] = related

    def handle_m2m_field(self, obj, field):
        if field.rel.through._meta.auto_created:
            if self.use_natural_keys and hasattr(field.rel.to, 'natural_key'):
                def m2m_value(value):
                    return value.natural_key()
            else:
                def m2m_value(value):
                    return smart_text(value._get_pk_val(), strings_only=True)
            self._current['properties'][field.name] = [m2m_value(related)
                                                       for related in getattr(obj, field.name).iterator()]

    def handle_reverse_field(self, obj, field, field_name):
        if self.use_natural_keys and hasattr(field.model, 'natural_key'):
            def reverse_value(value):
                return value.natural_key()
        else:
            def reverse_value(value):
                return smart_text(value._get_pk_val(), strings_only=True)
        values = [reverse_value(related) for related in getattr(obj, field_name).iterator()]
        self._current['properties'][field_name] = values

    def serialize_object_list(self, objects):
        if len(objects) == 0:
            return

        # Transform to list of dicts instead of objects
        if not isinstance(objects[0], dict):
            values = []
            for obj in objects:
                objdict = model_to_dict(obj)
                # In case geometry is not a DB field
                if self.geometry_field not in objdict:
                    objdict[self.geometry_field] = getattr(obj, self.geometry_field)
                if self.properties:
                    extras = [f for f in self.properties if hasattr(obj, f)]
                    for field_name in extras:
                        objdict[field_name] = getattr(obj, field_name)
                values.append(objdict)
            objects = values

        self.serialize_values_queryset(objects)

    def serialize_values_queryset(self, queryset):
        for obj in queryset:
            self.start_object(obj)

            # handle the geometry field
            self.handle_field(obj, self.geometry_field)

            for field_name in obj:
                if field_name not in obj:
                    continue
                if self.properties is None or field_name in self.properties:
                    self.handle_field(obj, field_name)

            self.end_object(obj)

    def serialize_queryset(self, queryset):
        opts = queryset.model._meta
        local_fields = opts.local_fields
        many_to_many_fields = opts.many_to_many
        reversed_fields = [obj.field for obj in get_all_related_objects(opts)]
        reversed_fields += [obj.field for obj in get_all_related_many_to_many_objects(opts)]

        # populate each queryset obj as a feature
        for obj in queryset:
            self.start_object(obj)

            # handle the geometry field
            self.handle_field(obj, self.geometry_field)

            # handle the property fields
            for field in local_fields:
                # don't include the pk in the properties
                # as it is in the id of the feature
                # except if explicitly listed in properties
                if field.name == opts.pk.name and \
                        (self.properties is None or 'id' not in self.properties):
                    continue
                # ignore other geometries
                if isinstance(field, GeometryField):
                    continue

                if field.serialize or field.primary_key:
                    if field.rel is None:
                        if self.properties is None or field.attname in self.properties:
                            self.handle_field(obj, field.name)
                    else:
                        if self.properties is None or field.attname[:-3] in self.properties:
                            self.handle_fk_field(obj, field)

            for field in many_to_many_fields:
                if field.serialize:
                    if self.properties is None or field.attname in self.properties:
                        self.handle_m2m_field(obj, field)

            for field in reversed_fields:
                if field.serialize:
                    field_name = field.rel.related_name or opts.object_name.lower()
                    if self.properties is None or field_name in self.properties:
                        self.handle_reverse_field(obj, field, field_name)
            self.end_object(obj)

    def serialize(self, queryset, **options):
        """
        Serialize a queryset.
        """
        self.options = options

        self.stream = options.get("stream", StringIO())
        self.primary_key = options.get("primary_key", None)
        self.properties = options.get("properties")
        self.geometry_field = options.get("geometry_field", "geom")
        self.use_natural_keys = options.get("use_natural_keys", False)
        self.bbox = options.get("bbox", None)
        self.bbox_auto = options.get("bbox_auto", None)
        self.srid = options.get("srid", GEOJSON_DEFAULT_SRID)
        self.crs = options.get("crs", True)

        self.start_serialization()

        if ValuesQuerySet is not None and isinstance(queryset, ValuesQuerySet):
            self.serialize_values_queryset(queryset)

        elif isinstance(queryset, list):
            self.serialize_object_list(queryset)

        elif isinstance(queryset, QuerySet):
            self.serialize_queryset(queryset)

        self.end_serialization()
        return self.getvalue()


def Deserializer(stream_or_string, **options):
    """
    Deserialize a stream or string of JSON data.
    """

    geometry_field = options.get("geometry_field", "geom")

    def FeatureToPython(dictobj):
        properties = dictobj['properties']
        model_name = options.get("model_name") or properties.pop('model')
        # Deserialize concrete fields only (bypass dynamic properties)
        model = _get_model(model_name)
        field_names = [f.name for f in model._meta.fields]
        fields = {}
        for k, v in iteritems(properties):
            if k in field_names:
                fields[k] = v
        obj = {
            "model": model_name,
            "pk": dictobj.get('id') or properties.get('id'),
            "fields": fields
        }
        if isinstance(model._meta.get_field(geometry_field), GeoJSONField):
            obj['fields'][geometry_field] = dictobj['geometry']
        else:
            shape = GEOSGeometry(json.dumps(dictobj['geometry']))
            obj['fields'][geometry_field] = shape.wkt
        return obj

    if isinstance(stream_or_string, string_types):
        stream = StringIO(stream_or_string)
    else:
        stream = stream_or_string
    try:
        collection = json.load(stream)
        objects = [FeatureToPython(f) for f in collection['features']]
        for obj in PythonDeserializer(objects, **options):
            yield obj
    except GeneratorExit:
        raise
    except Exception as e:
        # Map to deserializer error
        raise DeserializationError(repr(e))


def get_all_related_objects(opts):
    """
    Django 1.8 changed meta api, see
    https://docs.djangoproject.com/en/1.8/ref/models/meta/#migrating-old-meta-api
    https://code.djangoproject.com/ticket/12663
    https://github.com/django/django/pull/3848
    Initially from Django REST Framework:
    https://github.com/tomchristie/django-rest-framework/blob/3.3.2/rest_framework/compat.py
    :param opts: Options instance
    :return: list of relations except many-to-many ones
    """
    if django.VERSION < (1, 8):
        return opts.get_all_related_objects()
    else:
        return [r for r in opts.related_objects if not r.field.many_to_many]


def get_all_related_many_to_many_objects(opts):
    """
    Django 1.8 changed meta api, see docstr in get_all_related_objects()

    :param opts: Options instance
    :return: list of many-to-many relations
    """
    if django.VERSION < (1, 8):
        return opts.get_all_related_many_to_many_objects()
    else:
        return [r for r in opts.related_objects if r.field.many_to_many]
