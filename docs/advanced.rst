Advanced usage
==============

Low-level serializer
--------------------

::

    from djgeojson.serializers import Serializer as GeoJSONSerializer

    GeoJSONSerializer().serialize(Restaurants.objects.all(), use_natural_keys=True, with_modelname=False)



Low-level deserializer
----------------------

::

    from djgeojson.serializers import Serializer as GeoJSONSerializer

    GeoJSONSerializer().deserialize('geojson', my_geojson)

You can optionally specify the model name directly in the parameters:

::

    GeoJSONSerializer().deserialize('geojson', my_geojson, model_name=my_model_name)




Dump GIS models, or fixtures
----------------------------

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