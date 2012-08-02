*django-geojson* 


=======
INSTALL
=======

::

    pip install django-geojson

=====
USAGE
=====

GeoJSON layer view
------------------

Very useful for web mapping :

::

    from djgeojson.views import GeoJSONLayerView


    class MeetingLayer(GeoJSONLayerView):
        model = Meeting
        fields = ('title', 'datetime',)
        # Options
        srid = 4326     # projection
        precision = 4   # float
        simplify = 0.5  # generalization


Consume the vector layer as usual, for example, with Leaflet :

::

    var layer = L.GeoJSON();
    map.addLayer(layer);
    $.getJSON('{% url viewname %}', function (data){
        layer.addData(data);
    });


GeoJSON template filter
-----------------------

Will work either for a model, a geometry field or a queryset.

::

    {% load geojson_tags %}
    
    var feature = {{ object|geojsonfeature }};
    
    var geom = {{ object.geom|geojsonfeature }};

    var collection = {{ object_list|geojsonfeature }};


Dump GIS models
---------------

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

Relies massively on Sean Gillies' `geojson <>`_ python module.

|makinacom|_

.. |makinacom| image:: http://depot.makina-corpus.org/public/logo.gif
.. _makinacom:  http://www.makina-corpus.com

=======
LICENSE
=======

    * Lesser GNU Public License
