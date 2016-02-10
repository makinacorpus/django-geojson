*django-geojson* is a set of tools to manipulate GeoJSON with Django :

* (De)Serializer for (Geo)Django objects, querysets and lists
* Base views to serve GeoJSON map layers from models
* GeoJSON model and form fields to avoid spatial database backends
  (compatible with *django-leaflet* for map widgets)


.. image:: https://img.shields.io/pypi/v/django-geojson.svg
        :target: https://pypi.python.org/pypi/django-geojson

.. image:: https://img.shields.io/pypi/dm/django-geojson.svg
        :target: https://pypi.python.org/pypi/django-geojson

.. image:: https://travis-ci.org/makinacorpus/django-geojson.png?branch=master
    :target: https://travis-ci.org/makinacorpus/django-geojson

.. image:: https://coveralls.io/repos/makinacorpus/django-geojson/badge.png?branch=master
    :target: https://coveralls.io/r/makinacorpus/django-geojson


=======
INSTALL
=======

::

    pip install django-geojson


This package has **optional** `extra dependencies <http://pythonhosted.org/setuptools/setuptools.html#declaring-extras-optional-features-with-their-own-dependencies>`_.


If you need GeoJSON fields with map widgets :

::

    pip install "django-geojson [field]"


=====
USAGE
=====

Add ``djgeojson`` to your applications :

::

    # settings.py

    INSTALLED_APPS += (
        'djgeojson',
    )

*(not required for views)*


GeoJSON layer view
==================

Very useful for web mapping :

::

    # urls.py
    from djgeojson.views import GeoJSONLayerView
    ...
    url(r'^data.geojson$', GeoJSONLayerView.as_view(model=MushroomSpot), name='data'),


Consume the vector layer as usual, for example, with Leaflet loaded with jQuery Ajax:

::

    # Leaflet JS
    var layer = L.geoJson();
    map.addLayer(layer);
    $.getJSON("{% url 'data' %}", function (data) {
        layer.addData(data);
    });


Inherit generic views **only** if you need a reusable set of options :

::

    # views.py
    from djgeojson.views import GeoJSONLayerView

    class MapLayer(GeoJSONLayerView):
        # Options
        precision = 4   # float
        simplify = 0.5  # generalization


    # urls.py
    from .views import MapLayer, MeetingLayer
    ...
    url(r'^mushrooms.geojson$', MapLayer.as_view(model=MushroomSpot, properties=('name',)), name='mushrooms')

Most common use-cases of reusable options are: low-fi precision, common list of fields between several views, etc.

Options are :

* **properties** : ``list`` of properties names, or ``dict`` for mapping field names and properties
* **simplify** : generalization of geometries (See ``simplify()``)
* **precision** : number of digit after comma
* **geometry_field** : name of geometry field (*default*: ``geom``)
* **srid** : projection (*default*: 4326, for WGS84)
* **bbox** : Allows you to set your own bounding box on feature collection level
* **bbox_auto** : True/False (default false). Will automatically generate a bounding box on a per feature level.
* **use_natural_keys** : serialize natural keys instead of primary keys (*default*: ``False``)


Tiled GeoJSON layer view
========================

Vectorial tiles can help display a great number of objects on the map,
with `reasonnable performance <https://groups.google.com/forum/?fromgroups#!searchin/leaflet-js/GeoJSON$20performance$3F$20River$20vector$20tile$20map./leaflet-js/_WJquNpdmH0/qQsasZpCTPUJ>`_.

::

    # urls.py
    from djgeojson.views import TiledGeoJSONLayerView
    ...

    url(r'^data/(?P<z>\d+)/(?P<x>\d+)/(?P<y>\d+).geojson$',
        TiledGeoJSONLayerView.as_view(model=MushroomSpot), name='data'),


Consume the vector tiles using `Leaflet TileLayer GeoJSON <https://github.com/glenrobertson/leaflet-tilelayer-geojson/>`_, `Polymaps <http://polymaps.org/>`_, `OpenLayers 3 <http://twpayne.github.io/ol3/remote-vector/examples/tile-vector.html>`_ or `d3.js <http://d3js.org>`_ for example.

Options are :
 
* **trim_to_boundary** : if ``True`` geometries are trimmed to the tile boundary
* **simplifications** : a dict of simplification values by zoom level



GeoJSON template filter
=======================

Mainly useful to dump features in HTML output and bypass AJAX call :

::

    // Leaflet JS
    L.geoJson({{ object_list|geojsonfeature|safe}}).addTo(map);


Will work either for a model, a geometry field or a queryset.

::

    {% load geojson_tags %}
    
    var feature = {{ object|geojsonfeature|safe }};
    
    var geom = {{ object.geom|geojsonfeature|safe }};

    var collection = {{ object_list|geojsonfeature|safe }};


Properties and custom geometry field name can be provided.

::

    {{ object|geojsonfeature:"name,age" }}
    {{ object|geojsonfeature:"name,age:the_geom" }}
    {{ object|geojsonfeature:":geofield" }}


Model and forms fields
======================

GeoJSON fields are based on Brad Jasper's `JSONField <https://pypi.python.org/pypi/jsonfield>`_.
See `INSTALL`_ to install extra dependencies.

They are useful to avoid usual GIS stacks (GEOS, GDAL, PostGIS...)
for very simple use-cases (no spatial operation yet).

::

    from djgeojson.fields import PointField

    class Address(models.Model):
        geom = PointField()

    address = Address()
    address.geom = {'type': 'Point', 'coordinates': [0, 0]}
    address.save()


Form widgets are rendered with Leaflet maps automatically if
`django-leaflet <https://github.com/makinacorpus/django-leaflet>`_
is available.

All geometry types are supported and respectively validated :
`GeometryField`, `PointField`, `MultiPointField`, `LineStringField`,
`MultiLineStringField`, `PolygonField`, `MultiPolygonField`,
`GeometryCollectionField`.


Low-level serializer
====================

::

    from djgeojson.serializers import Serializer as GeoJSONSerializer

    GeoJSONSerializer().serialize(Restaurants.objects.all(), use_natural_keys=True, with_modelname=False)



Low-level deserializer
======================

::

    from djgeojson.serializers import Serializer as GeoJSONSerializer

    GeoJSONSerializer().deserialize('geojson', my_geojson)

You can optionally specify the model name directly in the parameters:

::

    GeoJSONSerializer().deserialize('geojson', my_geojson, model_name=my_model_name)




Dump GIS models, or fixtures
============================

Register the serializer in your project :

::

    # settings.py

    SERIALIZATION_MODULES = {
        'geojson' : 'djgeojson.serializers'
    }

Command-line ``dumpdata`` can export files, viewable in GIS software like QGis :

::

    python manage.py dumpdata --format=geojson yourapp.Model > export.geojson

Works with ``loaddata`` as well, which can now import GeoJSON files.



=======
AUTHORS
=======

    * Mathieu Leplatre <mathieu.leplatre@makina-corpus.com>
    * Glen Robertson author of django-geojson-tiles at: https://github.com/glenrobertson/django-geojson-tiles/
    * @jeffkistler's author of geojson serializer at: https://gist.github.com/967274
    * Ben Welsh and Lukasz Dziedzia for `quick test script <http://datadesk.latimes.com/posts/2012/06/test-your-django-app-with-travisci/>`_
    * Florent Lebreton http://github.com/fle
    * Julien Le Sech http://www.idreammicro.com
    * Kevin Cooper @kevcooper
    * Achille Ash @AchilleAsh

Version 1.X:

    * Daniel Sokolowski, serializer snippet
    * ozzmo, python 2.6 compatibility

|makinacom|_

.. |makinacom| image:: http://depot.makina-corpus.org/public/logo.gif
.. _makinacom:  http://www.makina-corpus.com

=======
LICENSE
=======

    * Lesser GNU Public License
