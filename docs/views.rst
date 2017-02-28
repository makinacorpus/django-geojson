Views
=====

GeoJSON layer view
------------------

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
------------------------

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
-----------------------

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
