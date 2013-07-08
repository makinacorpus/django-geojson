from django.test import TestCase
from django.test.utils import override_settings
from django.core import serializers
from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point, GeometryCollection


from .templatetags.geojson_tags import geojsonfeature
from .serializers import Serializer


TEST_SETTINGS = dict(SERIALIZATION_MODULES={'geojson': 'djgeojson.serializers'})


class Route(models.Model):
    name = models.CharField(max_length=20)
    geom = models.LineStringField(spatial_index=False)

    @property
    def upper_name(self):
        return self.name.upper()

    objects = models.GeoManager()


class GeoJsonDeSerializerTest(TestCase):
    @override_settings(**TEST_SETTINGS)
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
    @override_settings(**TEST_SETTINGS)
    def test_basic(self):
        # Stuff to serialize
        Route(name='green', geom="LINESTRING (0 0, 1 1)").save()
        Route(name='blue', geom="LINESTRING (0 0, 1 1)").save()
        Route(name='red', geom="LINESTRING (0 0, 1 1)").save()

        # Expected output
        expect_geojson = """{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "name": "green"}, "id": 1}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "name": "blue"}, "id": 2}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "name": "red"}, "id": 3}]}"""
        expect_geojson_with_prop = """{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "upper_name": "GREEN", "name": "green"}, "id": 1}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "upper_name": "BLUE", "name": "blue"}, "id": 2}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "upper_name": "RED", "name": "red"}, "id": 3}]}"""
        # Do the serialization
        actual_geojson = serializers.serialize('geojson', Route.objects.all(),
                                               properties=['name'])
        actual_geojson_with_prop = serializers.serialize('geojson', Route.objects.all(),
                                                         properties=['name', 'upper_name'])

        # Did it work?
        self.assertEqual(actual_geojson, expect_geojson)
        self.assertEqual(actual_geojson_with_prop, expect_geojson_with_prop)

    def test_force2d(self):
        serializer = Serializer()
        features2d = serializer.serialize([{'geom': 'SRID=4326;POINT Z (1 2 3)'}], force2d=True, crs=False)
        self.assertEqual(features2d, '{"type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [1.0, 2.0]}, "type": "Feature", "properties": {}}]}')


    def test_geometry_property(self):
        class Basket(models.Model):
            @property
            def geom(self):
                return GeometryCollection(LineString((3, 4, 5), (6, 7, 8)), Point(1, 2, 3), srid=2154)
        serializer = Serializer()
        features = serializer.serialize([Basket()], crs=False, force2d=True)
        self.assertEqual(features, '{"type": "FeatureCollection", "features": [{"geometry": {"type": "GeometryCollection", "geometries": [{"type": "LineString", "coordinates": [[-1.363063925443132, -5.98383036525906], [-1.363046296706177, -5.983810648949802]]}, {"type": "Point", "coordinates": [-1.363075677929551, -5.98384350946429]}]}, "type": "Feature", "properties": {"id": null}}]}')

class GeoJsonTemplateTagTest(TestCase):
    def test_single(self):
        r = Route(name='red', geom="LINESTRING (0 0, 1 1)")
        feature = geojsonfeature(r)
        self.assertEqual(feature, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {}}]}')

    def test_queryset(self):
        Route(name='green', geom="LINESTRING (0 0, 1 1)").save()
        Route(name='blue', geom="LINESTRING (0 0, 1 1)").save()
        Route(name='red', geom="LINESTRING (0 0, 1 1)").save()

        feature = geojsonfeature(Route.objects.all())
        self.assertEqual(feature, '{"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route"}, "id": 1}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route"}, "id": 2}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route"}, "id": 3}]}')

    def test_feature(self):
        r = Route(name='red', geom="LINESTRING (0 0, 1 1)")
        feature = geojsonfeature(r.geom)
        self.assertEqual(feature, '{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {}}')