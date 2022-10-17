Model and forms fields
======================

GeoJSON fields are based on Django JSONField.
See :doc:`installation` to install extra dependencies.

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
