*django-geojson* is a collection of helpers to (de)serialize (Geo)Django objects
into GeoJSON.

.. image:: https://pypip.in/v/django-geojson/badge.png
        :target: https://pypi.python.org/pypi/django-geojson

.. image:: https://pypip.in/d/django-geojson/badge.png
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


If you need to load data from GeoJSON files (deserialize), you'll also need shapely ::

    pip install "django-geojson [shapely]"


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


Consume the vector layer as usual, for example, with Leaflet loaded in Ajax:

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
    url(r'^mushrooms.geojson$', MapLayer.as_view(model=MushroomSpot, fields=('name',)), name='mushrooms')

Most common use-cases of reusable options are: low-fi precision, common list of fields between several views, etc.

Options are :

* **properties** : ``list`` of properties names, or ``dict`` for mapping field names and properties
* **simplify** : generalization of geometries (See ``simplify()``)
* **precision** : number of digit after comma
* **geometry_field** : name of geometry field (*default*: ``geom``)
* **srid** : projection (*default*: 4326, for WGS84)
* **bbox** : Allows you to set your own bounding box on feature collection level
* **bbox_auto** : True/False (default false). Will automatically generate a bounding box on a per feature level.


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


Low-level serializer
====================

::

    from djgeojson.serializers import Serializer as GeoJSONSerializer

    GeoJSONSerializer().serialize(Restaurants.objects.all(), use_natural_keys=True)



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
