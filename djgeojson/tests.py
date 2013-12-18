import json
from django.test import TestCase
from django.conf import settings
from django.core import serializers
from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point, GeometryCollection


from .templatetags.geojson_tags import geojsonfeature
from .serializers import Serializer


settings.SERIALIZATION_MODULES = {'geojson': 'djgeojson.serializers'}


class PictureMixin(object):
    @property
    def picture(self):
        return 'image.png'


class Route(PictureMixin, models.Model):
    name = models.CharField(max_length=20)
    geom = models.LineStringField(spatial_index=False, srid=4326)
    countries = models.ManyToManyField('Country')

    def natural_key(self):
        return self.name

    @property
    def upper_name(self):
        return self.name.upper()

    objects = models.GeoManager()


class Sign(models.Model):
    label = models.CharField(max_length=20)
    route = models.ForeignKey(Route, related_name='signs')

    def natural_key(self):
        return self.label

    @property
    def geom(self):
        return self.route.geom.centroid


class Country(models.Model):
    label = models.CharField(max_length=20)
    geom = models.PolygonField(spatial_index=False, srid=4326)

    def natural_key(self):
        return self.label


class GeoJsonDeSerializerTest(TestCase):
    def test_basic(self):
        # Input text
        input_geojson = """
        {"type": "FeatureCollection",
         "features": [
            { "type": "Feature",
                "properties": {"model": "djgeojson.route", "name": "green", "upper_name": "RED"},
                "id": 1,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [0.0, 0.0],
                        [1.0, 1.0]
                    ]
                }
            },
            { "type": "Feature",
                "properties": {"model": "djgeojson.route", "name": "blue"},
                "id": 2,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [0.0, 0.0],
                        [1.0, 1.0]
                    ]
                }
            }
        ]}"""

        # Deserialize into a list of objects
        objects = list(serializers.deserialize('geojson', input_geojson))

        # Were three objects deserialized?
        self.assertEqual(len(objects), 2)

        # Did the objects deserialize correctly?
        self.assertEqual(objects[1].object.name, "blue")
        self.assertEqual(objects[0].object.upper_name, "GREEN")
        self.assertEqual(objects[0].object.geom, LineString((0.0, 0.0), (1.0, 1.0)))


class GeoJsonSerializerTest(TestCase):
    def test_basic(self):
        # Stuff to serialize
        route1 = Route.objects.create(name='green', geom="LINESTRING (0 0, 1 1)")
        route2 = Route.objects.create(name='blue', geom="LINESTRING (0 0, 1 1)")
        route3 = Route.objects.create(name='red', geom="LINESTRING (0 0, 1 1)")

        actual_geojson = serializers.serialize('geojson', Route.objects.all(),
                                               properties=['name'])
        self.assertEqual(actual_geojson, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "name": "green"}, "id": %s}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "name": "blue"}, "id": %s}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "name": "red"}, "id": %s}]}' % (route1.pk, route2.pk, route3.pk))
        actual_geojson_with_prop = serializers.serialize('geojson', Route.objects.all(),
                                                         properties=['name', 'upper_name', 'picture'])
        self.assertEqual(actual_geojson_with_prop, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"picture": "image.png", "model": "djgeojson.route", "upper_name": "GREEN", "name": "green"}, "id": %s}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"picture": "image.png", "model": "djgeojson.route", "upper_name": "BLUE", "name": "blue"}, "id": %s}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"picture": "image.png", "model": "djgeojson.route", "upper_name": "RED", "name": "red"}, "id": %s}]}' % (route1.pk, route2.pk, route3.pk))

    def test_precision(self):
        serializer = Serializer()
        features = serializer.serialize([{'geom': 'SRID=2154;POINT (1 1)'}], precision=2, crs=False)
        self.assertEqual(features, '{"type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [-1.36, -5.98]}, "type": "Feature", "properties": {}}]}')

    def test_simplify(self):
        serializer = Serializer()
        features = serializer.serialize([{'geom': 'SRID=4326;LINESTRING (1 1, 1.5 1, 2 3, 3 3)'}], simplify=0.5, crs=False)
        self.assertEqual(features, '{"type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[1.0, 1.0], [2.0, 3.0], [3.0, 3.0]]}, "type": "Feature", "properties": {}}]}')

    def test_force2d(self):
        serializer = Serializer()
        features2d = serializer.serialize([{'geom': 'SRID=4326;POINT Z (1 2 3)'}], force2d=True, crs=False)
        self.assertEqual(features2d, '{"type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [1.0, 2.0]}, "type": "Feature", "properties": {}}]}')

    def test_pk_property(self):
        route = Route.objects.create(name='red', geom="LINESTRING (0 0, 1 1)")
        serializer = Serializer()
        features2d = serializer.serialize(Route.objects.all(), properties=['id'], crs=False)
        self.assertEqual(features2d, '{"type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "id": %s}, "id": %s}]}' % (route.pk, route.pk))

    def test_geometry_property(self):
        class Basket(models.Model):
            @property
            def geom(self):
                return GeometryCollection(LineString((3, 4, 5), (6, 7, 8)), Point(1, 2, 3), srid=4326)

        serializer = Serializer()
        features = serializer.serialize([Basket()], crs=False, force2d=True)
        expected_content = '{"type": "FeatureCollection", "features": [{"geometry": {"type": "GeometryCollection", "geometries": [{"type": "LineString", "coordinates": [[3.0, 4.0], [6.0, 7.0]]}, {"type": "Point", "coordinates": [1.0, 2.0]}]}, "type": "Feature", "properties": {"id": null}}]}'
        self.assertEqual(features, expected_content)

    def test_none_geometry(self):
        class Empty(models.Model):
            geom = None
        serializer = Serializer()
        features = serializer.serialize([Empty()], crs=False)
        self.assertEqual(features, '{"type": "FeatureCollection", "features": [{"geometry": null, "type": "Feature", "properties": {"id": null}}]}')


class ForeignKeyTest(TestCase):
    def setUp(self):
        self.route = Route.objects.create(name='green', geom="LINESTRING (0 0, 1 1)")
        Sign(label='A', route=self.route).save()

    def test_serialize_foreign(self):
        serializer = Serializer()
        features = serializer.serialize(Sign.objects.all(), properties=['route'])
        self.assertEqual(features, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [0.5, 0.5]}, "type": "Feature", "properties": {"route": 1, "model": "djgeojson.sign"}, "id": %s}]}' % self.route.pk)

    def test_serialize_foreign_natural(self):
        serializer = Serializer()
        features = serializer.serialize(Sign.objects.all(), use_natural_keys=True, properties=['route'])
        self.assertEqual(features, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [0.5, 0.5]}, "type": "Feature", "properties": {"route": "green", "model": "djgeojson.sign"}, "id": %s}]}' % self.route.pk)


class ManyToManyTest(TestCase):
    def setUp(self):
        country1 = Country(label='C1', geom="POLYGON ((0 0,1 1,0 2,0 0))")
        country1.save()
        country2 = Country(label='C2', geom="POLYGON ((0 0,1 1,0 2,0 0))")
        country2.save()

        self.route1 = Route.objects.create(name='green', geom="LINESTRING (0 0, 1 1)")
        self.route2 = Route.objects.create(name='blue', geom="LINESTRING (0 0, 1 1)")
        self.route2.countries.add(country1)
        self.route3 = Route.objects.create(name='red', geom="LINESTRING (0 0, 1 1)")
        self.route3.countries.add(country1)
        self.route3.countries.add(country2)

    def test_serialize_manytomany(self):
        serializer = Serializer()
        features = serializer.serialize(Route.objects.all(), properties=['countries'])
        self.assertEqual(features, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": []}, "id": %s}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": [1]}, "id": %s}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": [1, 2]}, "id": %s}]}' % (self.route1.pk, self.route2.pk, self.route3.pk))

    def test_serialize_manytomany_natural(self):
        serializer = Serializer()
        features = serializer.serialize(Route.objects.all(), use_natural_keys=True, properties=['countries'])
        self.assertEqual(features, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": []}, "id": %s}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": ["C1"]}, "id": %s}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": ["C1", "C2"]}, "id": %s}]}' % (self.route1.pk, self.route2.pk, self.route3.pk))


class ReverseForeignkeyTest(TestCase):
    def setUp(self):
        self.route = Route(name='green', geom="LINESTRING (0 0, 1 1)")
        self.route.save()
        self.sign1 = Sign.objects.create(label='A', route=self.route)
        self.sign2 = Sign.objects.create(label='B', route=self.route)
        self.sign3 = Sign.objects.create(label='C', route=self.route)

    def test_relation_set(self):
        self.assertEqual(len(self.route.signs.all()), 3)

    def test_serialize_reverse(self):
        serializer = Serializer()
        features = serializer.serialize(Route.objects.all(), properties=['signs'])
        self.assertEqual(features, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "signs": [%s, %s, %s]}, "id": %s}]}' % (self.sign1.pk, self.sign2.pk, self.sign3.pk, self.route.pk))

    def test_serialize_reverse_natural(self):
        serializer = Serializer()
        features = serializer.serialize(Route.objects.all(), use_natural_keys=True, properties=['signs'])
        self.assertEqual(features, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "signs": ["A", "B", "C"]}, "id": %s}]}' % self.route.pk)


class GeoJsonTemplateTagTest(TestCase):
    def test_single(self):
        r = Route(name='red', geom="LINESTRING (0 0, 1 1)")
        feature = geojsonfeature(r)
        self.assertEqual(feature, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {}}]}')

    def test_queryset(self):
        route1 = Route.objects.create(name='green', geom="LINESTRING (0 0, 1 1)")
        route2 = Route.objects.create(name='blue', geom="LINESTRING (0 0, 1 1)")
        route3 = Route.objects.create(name='red', geom="LINESTRING (0 0, 1 1)")

        feature = geojsonfeature(Route.objects.all())
        self.assertEqual(feature, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route"}, "id": %s}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route"}, "id": %s}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route"}, "id": %s}]}' % (route1.pk, route2.pk, route3.pk))

    def test_feature(self):
        r = Route(name='red', geom="LINESTRING (0 0, 1 1)")
        feature = geojsonfeature(r.geom)
        self.assertEqual(feature, '{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {}}')
