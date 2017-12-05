from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from django.conf import settings
from django.core import serializers
from django.core.exceptions import ValidationError, SuspiciousOperation
from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point, GeometryCollection
from django.utils.encoding import smart_text

from .templatetags.geojson_tags import geojsonfeature
from .serializers import Serializer
from .views import GeoJSONLayerView, TiledGeoJSONLayerView
from .fields import GeoJSONField, GeoJSONFormField, GeoJSONValidator


settings.SERIALIZATION_MODULES = {'geojson': 'djgeojson.serializers'}


class PictureMixin(object):

    @property
    def picture(self):
        return 'image.png'


class Country(models.Model):
    label = models.CharField(max_length=20)
    geom = models.PolygonField(spatial_index=False, srid=4326)

    if django.VERSION < (1, 9):
        objects = models.GeoManager()

    def natural_key(self):
        return self.label


class Route(PictureMixin, models.Model):
    name = models.CharField(max_length=20)
    geom = models.LineStringField(spatial_index=False, srid=4326)
    countries = models.ManyToManyField(Country)

    def natural_key(self):
        return self.name

    @property
    def upper_name(self):
        return self.name.upper()

    if django.VERSION < (1, 9):
        objects = models.GeoManager()


class Sign(models.Model):
    label = models.CharField(max_length=20)
    route = models.ForeignKey(Route, related_name='signs', on_delete=models.PROTECT)

    def natural_key(self):
        return self.label

    @property
    def geom(self):
        return self.route.geom.centroid


class GeoJsonDeSerializerTest(TestCase):

    def test_basic(self):
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
        self.assertEqual(objects[0].object.geom,
                         LineString((0.0, 0.0), (1.0, 1.0), srid=objects[0].object.geom.srid))

    def test_with_model_name_passed_as_argument(self):
        input_geojson = """
        {"type": "FeatureCollection",
         "features": [
            { "type": "Feature",
                "properties": {"name": "bleh"},
                "id": 24,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [1, 2],
                        [42, 3]
                    ]
                }
            }
        ]}"""

        my_object = list(serializers.deserialize(
            'geojson', input_geojson, model_name='djgeojson.route'))[0].object

        self.assertEqual(my_object.name, "bleh")


class GeoJsonSerializerTest(TestCase):

    def test_basic(self):
        # Stuff to serialize
        route1 = Route.objects.create(
            name='green', geom="LINESTRING (0 0, 1 1)")
        route2 = Route.objects.create(
            name='blue', geom="LINESTRING (0 0, 1 1)")
        route3 = Route.objects.create(name='red', geom="LINESTRING (0 0, 1 1)")

        actual_geojson = json.loads(serializers.serialize(
            'geojson', Route.objects.all(), properties=['name']))
        self.assertEqual(
            actual_geojson, {"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "name": "green"}, "id": route1.pk}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "name": "blue"}, "id": route2.pk}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "name": "red"}, "id": route3.pk}]})
        actual_geojson_with_prop = json.loads(
            serializers.serialize(
                'geojson', Route.objects.all(),
                properties=['name', 'upper_name', 'picture']))
        self.assertEqual(actual_geojson_with_prop,
                         {"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"picture": "image.png", "model": "djgeojson.route", "upper_name": "GREEN", "name": "green"}, "id": route1.pk}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"picture": "image.png", "model": "djgeojson.route", "upper_name": "BLUE", "name": "blue"}, "id": route2.pk}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"picture": "image.png", "model": "djgeojson.route", "upper_name": "RED", "name": "red"}, "id": route3.pk}]})

    def test_precision(self):
        serializer = Serializer()
        features = json.loads(serializer.serialize(
            [{'geom': 'SRID=2154;POINT (1 1)'}], precision=2, crs=False))
        self.assertEqual(
            features, {"type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [-1.36, -5.98]}, "type": "Feature", "properties": {}}]})

    def test_simplify(self):
        serializer = Serializer()
        features = json.loads(serializer.serialize(
            [{'geom': 'SRID=4326;LINESTRING (1 1, 1.5 1, 2 3, 3 3)'}], simplify=0.5, crs=False))
        self.assertEqual(
            features, {"type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[1.0, 1.0], [2.0, 3.0], [3.0, 3.0]]}, "type": "Feature", "properties": {}}]})

    def test_force2d(self):
        serializer = Serializer()
        features2d = json.loads(serializer.serialize(
            [{'geom': 'SRID=4326;POINT Z (1 2 3)'}],
            force2d=True, crs=False))
        self.assertEqual(
            features2d, {"type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [1.0, 2.0]}, "type": "Feature", "properties": {}}]})

    def test_named_crs(self):
        serializer = Serializer()
        features = json.loads(serializer.serialize(
            [{'geom': 'SRID=4326;POINT (1 2)'}],
            crs_type="name"))
        self.assertEqual(
            features['crs'], {"type": "name", "properties": {"name": "EPSG:4326"}})

    def test_misspelled_named_crs(self):
        serializer = Serializer()
        features = json.loads(serializer.serialize(
            [{'geom': 'SRID=4326;POINT (1 2)'}],
            crs_type="named"))
        self.assertEqual(
            features['crs'], {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}})

    def test_pk_property(self):
        route = Route.objects.create(name='red', geom="LINESTRING (0 0, 1 1)")
        serializer = Serializer()
        features2d = json.loads(serializer.serialize(
            Route.objects.all(), properties=['id'], crs=False))
        self.assertEqual(
            features2d, {"type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "id": route.pk}, "id": route.pk}]})

    def test_geometry_property(self):
        class Basket(models.Model):

            @property
            def geom(self):
                return GeometryCollection(LineString((3, 4, 5), (6, 7, 8)), Point(1, 2, 3), srid=4326)

        serializer = Serializer()
        features = json.loads(
            serializer.serialize([Basket()], crs=False, force2d=True))
        expected_content = {"type": "FeatureCollection", "features": [{"geometry": {"type": "GeometryCollection", "geometries": [{"type": "LineString", "coordinates": [[3.0, 4.0], [6.0, 7.0]]}, {"type": "Point", "coordinates": [1.0, 2.0]}]}, "type": "Feature", "properties": {"id": None}}]}
        self.assertEqual(features, expected_content)

    def test_none_geometry(self):
        class Empty(models.Model):
            geom = None
        serializer = Serializer()
        features = json.loads(serializer.serialize([Empty()], crs=False))
        self.assertEqual(
            features, {
                "type": "FeatureCollection",
                "features": [{
                    "geometry": None,
                    "type": "Feature",
                    "properties": {"id": None}}]
            })

    def test_bbox_auto(self):
        serializer = Serializer()
        features = json.loads(serializer.serialize([{'geom': 'SRID=4326;LINESTRING (1 1, 3 3)'}],
                                                   bbox_auto=True, crs=False))
        self.assertEqual(
            features, {
                "type": "FeatureCollection",
                "features": [{
                    "geometry": {"type": "LineString", "coordinates": [[1.0, 1.0], [3.0, 3.0]]},
                    "type": "Feature",
                    "properties": {},
                    "bbox": [1.0, 1.0, 3.0, 3.0]
                }]
            })


class ForeignKeyTest(TestCase):

    def setUp(self):
        self.route = Route.objects.create(
            name='green', geom="LINESTRING (0 0, 1 1)")
        Sign(label='A', route=self.route).save()

    def test_serialize_foreign(self):
        serializer = Serializer()
        features = json.loads(serializer.serialize(Sign.objects.all(), properties=['route']))
        self.assertEqual(
            features, {"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [0.5, 0.5]}, "type": "Feature", "properties": {"route": 1, "model": "djgeojson.sign"}, "id": self.route.pk}]})

    def test_serialize_foreign_natural(self):
        serializer = Serializer()
        features = json.loads(serializer.serialize(
            Sign.objects.all(), use_natural_keys=True, properties=['route']))
        self.assertEqual(
            features, {"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [0.5, 0.5]}, "type": "Feature", "properties": {"route": "green", "model": "djgeojson.sign"}, "id": self.route.pk}]})


class ManyToManyTest(TestCase):

    def setUp(self):
        country1 = Country(label='C1', geom="POLYGON ((0 0,1 1,0 2,0 0))")
        country1.save()
        country2 = Country(label='C2', geom="POLYGON ((0 0,1 1,0 2,0 0))")
        country2.save()

        self.route1 = Route.objects.create(
            name='green', geom="LINESTRING (0 0, 1 1)")
        self.route2 = Route.objects.create(
            name='blue', geom="LINESTRING (0 0, 1 1)")
        self.route2.countries.add(country1)
        self.route3 = Route.objects.create(
            name='red', geom="LINESTRING (0 0, 1 1)")
        self.route3.countries.add(country1)
        self.route3.countries.add(country2)

    def test_serialize_manytomany(self):
        serializer = Serializer()
        features = json.loads(serializer.serialize(
            Route.objects.all(), properties=['countries']))
        self.assertEqual(
            features, {"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": []}, "id": self.route1.pk}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": [1]}, "id": self.route2.pk}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": [1, 2]}, "id": self.route3.pk}]})

    def test_serialize_manytomany_natural(self):
        serializer = Serializer()
        features = json.loads(serializer.serialize(
            Route.objects.all(), use_natural_keys=True, properties=['countries']))
        self.assertEqual(
            features, {"crs": {"type": "link", "properties": {"href": "http://spatialreference.org/ref/epsg/4326/", "type": "proj4"}}, "type": "FeatureCollection", "features": [{"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": []}, "id": self.route1.pk}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": ["C1"]}, "id": self.route2.pk}, {"geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}, "type": "Feature", "properties": {"model": "djgeojson.route", "countries": ["C1", "C2"]}, "id": self.route3.pk}]})


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
        features = json.loads(serializer.serialize(
            Route.objects.all(), properties=['signs']))
        self.assertEqual(
            features, {
                "crs": {
                    "type": "link", "properties": {
                        "href": "http://spatialreference.org/ref/epsg/4326/",
                        "type": "proj4"
                    }
                },
                "type": "FeatureCollection",
                "features": [{
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[0.0, 0.0], [1.0, 1.0]]
                    },
                    "type": "Feature",
                    "properties": {
                        "model": "djgeojson.route",
                        "signs": [
                            self.sign1.pk,
                            self.sign2.pk,
                            self.sign3.pk]},
                    "id": self.route.pk
                }]
            })

    def test_serialize_reverse_natural(self):
        serializer = Serializer()
        features = json.loads(serializer.serialize(
            Route.objects.all(), use_natural_keys=True, properties=['signs']))
        self.assertEqual(
            features, {
                "crs": {
                    "type": "link",
                    "properties": {
                        "href": "http://spatialreference.org/ref/epsg/4326/",
                        "type": "proj4"
                    }
                },
                "type": "FeatureCollection",
                "features": [{
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[0.0, 0.0], [1.0, 1.0]]},
                    "type": "Feature",
                    "properties": {
                        "model": "djgeojson.route",
                        "signs": ["A", "B", "C"]},
                    "id": self.route.pk
                }]
            })


class GeoJsonTemplateTagTest(TestCase):

    def setUp(self):
        self.route1 = Route.objects.create(name='green',
                                           geom="LINESTRING (0 0, 1 1)")
        self.route2 = Route.objects.create(name='blue',
                                           geom="LINESTRING (0 0, 1 1)")
        self.route3 = Route.objects.create(name='red',
                                           geom="LINESTRING (0 0, 1 1)")

    def test_templatetag_renders_single_object(self):
        feature = json.loads(geojsonfeature(self.route1))
        self.assertEqual(
            feature, {
                "crs": {
                    "type": "link",
                    "properties": {
                        "href": "http://spatialreference.org/ref/epsg/4326/",
                        "type": "proj4"
                    }
                },
                "type": "FeatureCollection",
                "features": [{
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[0.0, 0.0], [1.0, 1.0]]},
                    "type": "Feature", "properties": {}}]
            })

    def test_templatetag_renders_queryset(self):
        feature = json.loads(geojsonfeature(Route.objects.all()))
        self.assertEqual(
            feature, {
                "crs": {
                    "type": "link", "properties": {
                        "href": "http://spatialreference.org/ref/epsg/4326/",
                        "type": "proj4"
                    }
                },
                "type": "FeatureCollection",
                "features": [
                    {
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[0.0, 0.0], [1.0, 1.0]]
                        },
                        "type": "Feature",
                        "properties": {
                            "model": "djgeojson.route"
                        },
                        "id": self.route1.pk
                    },
                    {
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[0.0, 0.0], [1.0, 1.0]]
                        },
                        "type": "Feature",
                        "properties": {"model": "djgeojson.route"},
                        "id": self.route2.pk
                    },
                    {
                        "geometry": {"type": "LineString",
                                     "coordinates": [[0.0, 0.0], [1.0, 1.0]]},
                        "type": "Feature",
                        "properties": {"model": "djgeojson.route"},
                        "id": self.route3.pk
                    }
                ]
            })

    def test_template_renders_geometry(self):
        feature = json.loads(geojsonfeature(self.route1.geom))
        self.assertEqual(
            feature, {
                "geometry": {"type": "LineString",
                             "coordinates": [[0.0, 0.0], [1.0, 1.0]]},
                "type": "Feature", "properties": {}
            })

    def test_property_can_be_specified(self):
        features = json.loads(geojsonfeature(self.route1,
                                             "name"))
        feature = features['features'][0]
        self.assertEqual(feature['properties']['name'],
                         self.route1.name)

    def test_several_properties_can_be_specified(self):
        features = json.loads(geojsonfeature(self.route1,
                                             "name,id"))
        feature = features['features'][0]
        self.assertEqual(feature['properties'],
                         {'name': self.route1.name,
                          'id': self.route1.id})

    def test_srid_can_be_specified(self):
        feature = json.loads(geojsonfeature(self.route1.geom, "::2154"))
        self.assertEqual(feature['geometry']['coordinates'],
                         [[253531.1305237495, 909838.9305578759],
                          [406035.7627716485, 1052023.2925472297]])

    def test_geom_field_name_can_be_specified(self):
        features = json.loads(geojsonfeature(self.route1, ":geom"))
        feature = features['features'][0]
        self.assertEqual(feature['geometry']['coordinates'],
                         [[0.0, 0.0], [1.0, 1.0]])

    def test_geom_field_raises_attributeerror_if_unknown(self):
        self.assertRaises(AttributeError, geojsonfeature, self.route1, ":geo")


class ViewsTest(TestCase):

    def setUp(self):
        self.route = Route.objects.create(
            name='green', geom="LINESTRING (0 0, 1 1)")
        Sign(label='A', route=self.route).save()

    def test_view_default_options(self):
        view = GeoJSONLayerView(model=Route)
        view.object_list = []
        response = view.render_to_response(context={})
        geojson = json.loads(smart_text(response.content))
        self.assertEqual(geojson['features'][0]['geometry']['coordinates'],
                         [[0.0, 0.0], [1.0, 1.0]])

    def test_view_can_control_properties(self):
        class FullGeoJSON(GeoJSONLayerView):
            properties = ['name']
        view = FullGeoJSON(model=Route)
        view.object_list = []
        response = view.render_to_response(context={})
        geojson = json.loads(smart_text(response.content))
        self.assertEqual(geojson['features'][0]['properties']['name'],
                         'green')

    def test_view_foreign(self):
        class FullGeoJSON(GeoJSONLayerView):
            properties = ['label', 'route']
        view = FullGeoJSON(model=Sign)
        view.object_list = []
        response = view.render_to_response(context={})
        geojson = json.loads(smart_text(response.content))
        self.assertEqual(geojson['features'][0]['properties']['route'],
                         1)

    def test_view_foreign_natural(self):
        class FullGeoJSON(GeoJSONLayerView):
            properties = ['label', 'route']
            use_natural_keys = True
        view = FullGeoJSON(model=Sign)
        view.object_list = []
        response = view.render_to_response(context={})
        geojson = json.loads(smart_text(response.content))
        self.assertEqual(geojson['features'][0]['properties']['route'],
                         'green')


class TileEnvelopTest(TestCase):
    def setUp(self):
        self.view = TiledGeoJSONLayerView()

    def test_raises_error_if_not_spherical_mercator(self):
        self.view.tile_srid = 2154
        self.assertRaises(AssertionError, self.view.tile_coord, 0, 0, 0)

    def test_origin_is_north_west_for_tile_0(self):
        self.assertEqual((-180.0, 85.0511287798066),
                         self.view.tile_coord(0, 0, 0))

    def test_origin_is_center_for_middle_tile(self):
        self.assertEqual((0, 0), self.view.tile_coord(8, 8, 4))


class TiledGeoJSONViewTest(TestCase):
    def setUp(self):
        self.view = TiledGeoJSONLayerView(model=Route)
        self.view.args = []
        self.r1 = Route.objects.create(geom=LineString((0, 1), (10, 1)))
        self.r2 = Route.objects.create(geom=LineString((0, -1), (-10, -1)))

    def test_view_with_kwargs(self):
        self.view.kwargs = {'z': 4,
                            'x': 8,
                            'y': 7}
        response = self.view.render_to_response(context={})
        geojson = json.loads(smart_text(response.content))
        self.assertEqual(geojson['features'][0]['geometry']['coordinates'], [[0.0, 1.0], [10.0, 1.0]])

    def test_view_with_kwargs_wrong_type_z(self):
        self.view.kwargs = {'z': 'a',
                            'x': 8,
                            'y': 7}
        self.assertRaises(SuspiciousOperation,
                          self.view.render_to_response,
                          context={})

    def test_view_with_kwargs_wrong_type_x(self):
        self.view.kwargs = {'z': 1,
                            'x': 'a',
                            'y': 7}
        self.assertRaises(SuspiciousOperation,
                          self.view.render_to_response,
                          context={})

    def test_view_with_kwargs_wrong_type_y(self):
        self.view.kwargs = {'z': 4,
                            'x': 8,
                            'y': 'a'}
        self.assertRaises(SuspiciousOperation,
                          self.view.render_to_response,
                          context={})

    def test_view_with_kwargs_no_z(self):
        self.view.kwargs = {'x': 8,
                            'y': 7}
        self.assertRaises(SuspiciousOperation,
                          self.view.render_to_response,
                          context={})

    def test_view_with_kwargs_no_x(self):
        self.view.kwargs = {'z': 8,
                            'y': 7}
        self.assertRaises(SuspiciousOperation,
                          self.view.render_to_response,
                          context={})

    def test_view_with_kwargs_no_y(self):
        self.view.kwargs = {'x': 8,
                            'z': 7}
        self.assertRaises(SuspiciousOperation,
                          self.view.render_to_response,
                          context={})

    def test_view_is_serialized_as_geojson(self):
        self.view.args = [4, 8, 7]
        response = self.view.render_to_response(context={})
        geojson = json.loads(smart_text(response.content))
        self.assertEqual(geojson['features'][0]['geometry']['coordinates'],
                         [[0.0, 1.0], [10.0, 1.0]])

    def test_view_trims_to_geometries_boundaries(self):
        self.view.args = [8, 128, 127]
        response = self.view.render_to_response(context={})
        geojson = json.loads(smart_text(response.content))
        self.assertEqual(geojson['features'][0]['geometry']['coordinates'],
                         [[0.0, 1.0], [1.40625, 1.0]])

    def test_geometries_trim_can_be_disabled(self):
        self.view.args = [8, 128, 127]
        self.view.trim_to_boundary = False
        response = self.view.render_to_response(context={})
        geojson = json.loads(smart_text(response.content))
        self.assertEqual(geojson['features'][0]['geometry']['coordinates'],
                         [[0.0, 1.0], [10.0, 1.0]])

    def test_tile_extent_is_provided_in_collection(self):
        self.view.args = [8, 128, 127]
        response = self.view.render_to_response(context={})
        geojson = json.loads(smart_text(response.content))
        self.assertEqual(geojson['bbox'],
                         [0.0, 0.0, 1.40625, 1.4061088354351565])

    def test_url_parameters_are_converted_to_int(self):
        self.view.args = ['0', '0', '0']
        self.assertEqual(2, len(self.view.get_queryset()))

    def test_zoom_0_queryset_contains_all(self):
        self.view.args = [0, 0, 0]
        self.assertEqual(2, len(self.view.get_queryset()))

    def test_zoom_4_filters_by_tile_extent(self):
        self.view.args = [4, 8, 7]
        self.assertEqual([self.r1], list(self.view.get_queryset()))

    def test_some_tiles_have_empty_queryset(self):
        self.view.args = [4, 6, 8]
        self.assertEqual(0, len(self.view.get_queryset()))

    def test_simplification_depends_on_zoom_level(self):
        self.view.simplifications = {6: 100}
        self.view.args = [6, 8, 4]
        self.view.get_queryset()
        self.assertEqual(self.view.simplify, 100)

    def test_simplification_is_default_if_not_specified(self):
        self.view.simplifications = {}
        self.view.args = [0, 8, 4]
        self.view.get_queryset()
        self.assertEqual(self.view.simplify, None)

    def test_simplification_takes_the_closest_upper_level(self):
        self.view.simplifications = {3: 100, 6: 200}
        self.view.args = [4, 8, 4]
        self.view.get_queryset()
        self.assertEqual(self.view.simplify, 200)


class Address(models.Model):
    geom = GeoJSONField()


class ModelFieldTest(TestCase):
    def setUp(self):
        self.address = Address()
        self.address.geom = {'type': 'Point', 'coordinates': [0, 0]}
        self.address.save()

    def test_models_can_have_geojson_fields(self):
        saved = Address.objects.get(id=self.address.id)
        if isinstance(saved.geom, dict):
            self.assertDictEqual(saved.geom, self.address.geom)
        else:
            # Django 1.8 !
            self.assertEqual(json.loads(saved.geom.geojson), self.address.geom)

    def test_default_form_field_is_geojsonfield(self):
        field = self.address._meta.get_field('geom').formfield()
        self.assertTrue(isinstance(field, GeoJSONFormField))

    def test_default_form_field_has_geojson_validator(self):
        field = self.address._meta.get_field('geom').formfield()
        validator = field.validators[0]
        self.assertTrue(isinstance(validator, GeoJSONValidator))

    def test_form_field_raises_if_invalid_type(self):
        field = self.address._meta.get_field('geom').formfield()
        self.assertRaises(ValidationError, field.clean,
                          {'type': 'FeatureCollection', 'foo': 'bar'})

    def test_form_field_raises_if_type_missing(self):
        field = self.address._meta.get_field('geom').formfield()
        self.assertRaises(ValidationError, field.clean,
                          {'foo': 'bar'})

    def test_field_can_be_serialized(self):
        serializer = Serializer()
        geojson = serializer.serialize(Address.objects.all(), crs=False)
        features = json.loads(geojson)
        self.assertEqual(
            features, {
                'type': u'FeatureCollection',
                'features': [{
                    'id': self.address.id,
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [0, 0]},
                    'properties': {
                        'model': 'djgeojson.address'
                    }
                }]
            })

    def test_field_can_be_deserialized(self):
        input_geojson = """
        {"type": "FeatureCollection",
         "features": [
            { "type": "Feature",
                "properties": {"model": "djgeojson.address"},
                "id": 1,
                "geometry": {
                    "type": "Point",
                    "coordinates": [0.0, 0.0]
                }
            }
        ]}"""
        objects = list(serializers.deserialize('geojson', input_geojson))
        self.assertEqual(objects[0].object.geom,
                         {'type': 'Point', 'coordinates': [0, 0]})

    def test_model_can_be_omitted(self):
        serializer = Serializer()
        geojson = serializer.serialize(Address.objects.all(),
                                       with_modelname=False)
        features = json.loads(geojson)
        self.assertEqual(
            features, {
                "crs": {
                    "type": "link",
                    "properties": {
                        "href": "http://spatialreference.org/ref/epsg/4326/",
                        "type": "proj4"
                    }
                },
                'type': 'FeatureCollection',
                'features': [{
                    'id': self.address.id,
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [0, 0]},
                    'properties': {}
                }]
            })


class GeoJSONValidatorTest(TestCase):
    def test_validator_raises_if_missing_type(self):
        validator = GeoJSONValidator('GEOMETRY')
        self.assertRaises(ValidationError, validator, {'foo': 'bar'})

    def test_validator_raises_if_type_is_wrong(self):
        validator = GeoJSONValidator('GEOMETRY')
        self.assertRaises(ValidationError, validator,
                          {'type': 'FeatureCollection',
                           'features': []})

    def test_validator_succeeds_if_type_matches(self):
        validator = GeoJSONValidator('POINT')
        self.assertIsNone(validator({'type': 'Point', 'coords': [0, 0]}))

    def test_validator_succeeds_if_type_is_generic(self):
        validator = GeoJSONValidator('GEOMETRY')
        self.assertIsNone(validator({'type': 'Point', 'coords': [0, 0]}))
        self.assertIsNone(validator({'type': 'LineString', 'coords': [0, 0]}))
        self.assertIsNone(validator({'type': 'Polygon', 'coords': [0, 0]}))

    def test_validator_fails_if_type_does_not_match(self):
        validator = GeoJSONValidator('POINT')
        self.assertRaises(ValidationError, validator,
                          {'type': 'LineString', 'coords': [0, 0]})
