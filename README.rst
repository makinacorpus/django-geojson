*django-geojson* 


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


Consume the vector layer as usual, for example, with Leaflet :

::

    var layer = L.GeoJSON();
    map.addLayer(layer);
    $.getJSON("{% url 'data' %}", function (data) {
        layer.addData(data);
    });


Inherit **only** if you need a reusable set of options :

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
    


Most common use-cases are low-fi precision, common list of fields, etc.


GeoJSON template filter
=======================

Will work either for a model, a geometry field or a queryset.

::

    {% load geojson_tags %}
    
    var feature = {{ object|geojsonfeature }};
    
    var geom = {{ object.geom|geojsonfeature }};

    var collection = {{ object_list|geojsonfeature }};


Dump GIS models
===============

Register the serializer in your project :

::

    # settings.py

    SERIALIZATION_MODULES = {
        'geojson' : 'djgeojson.serializers'
    }

Command-line ``dumpdata`` can export files, viewable in GIS software like QGis :

::

    django dumpdata --format=geojson yourapp.Model > export.geojson

Works with ``loaddata`` as well, which can now import GeoJSON files.



=======
AUTHORS
=======

    * Mathieu Leplatre <mathieu.leplatre@makina-corpus.com>
    * Daniel Sokolowski, author of original serializer snippet
    * ozzmo, python 2.6 compatibility

Relies massively on Sean Gillies' `geojson <http://pypi.python.org/pypi/geojson>`_ python module.

|makinacom|_

.. |makinacom| image:: http://depot.makina-corpus.org/public/logo.gif
.. _makinacom:  http://www.makina-corpus.com

=======
LICENSE
=======

    * Lesser GNU Public License
