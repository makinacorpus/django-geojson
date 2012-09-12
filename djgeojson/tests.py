from django.test import TestCase
from django.core import serializers
from django.contrib.gis.db import models


class Route(models.Model):
    name = models.CharField(max_length=20)
    geom = models.LineStringField(spatial_index=False)

    @property
    def upper_name(self):
        return self.name.upper()

    objects = models.Manager()


class GeoJsonSerializerTest(TestCase):
    def test_deserializer(self):
        # Input text
        input_geojson = """
        {"type": "FeatureCollection",
         "features": [
            { "type": "Feature",
                "properties": {"model": "djgeojson.route", "name": "green", "upper_name": "GREEN"},
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
        self.assertEqual(objects[0].object.upper_name, "GREEN")
        self.assertEqual(objects[1].object.name, "blue")

    def test_serializer(self):
        # Stuff to serialize
        Route(name='green', geom="LINESTRING (0 0, 1 1)").save()
        Route(name='blue', geom="LINESTRING (0 0, 1 1)").save()
        Route(name='red', geom="LINESTRING (0 0, 1 1)").save()

        # Expected output
        expect_geojson = """{"type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"pk": 1, "model": "djgeojson.route", "name": "green"}, "id": 1}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"pk": 2, "model": "djgeojson.route", "name": "blue"}, "id": 2}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"pk": 3, "model": "djgeojson.route", "name": "red"}, "id": 3}]}"""
        expect_geojson_with_prop = """{"type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"pk": 1, "model": "djgeojson.route", "upper_name": "GREEN", "name": "green"}, "id": 1}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"pk": 2, "model": "djgeojson.route", "upper_name": "BLUE", "name": "blue"}, "id": 2}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"pk": 3, "model": "djgeojson.route", "upper_name": "RED", "name": "red"}, "id": 3}]}"""

        # Do the serialization
        actual_geojson = serializers.serialize('geojson', Route.objects.all(),
                                               fields=['name'])
        actual_geojson_with_prop = serializers.serialize('geojson', Route.objects.all(),
                                                         fields=['name', 'upper_name'])

        # Did it work?
        self.assertEqual(actual_geojson, expect_geojson)
        self.assertEqual(actual_geojson_with_prop, expect_geojson_with_prop)
