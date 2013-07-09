#: Module version, as defined in PEP-0396.
pkg_resources = __import__('pkg_resources')
distribution = pkg_resources.get_distribution('django-geojson')

__version__ = distribution.version


GEOJSON_DEFAULT_SRID = 4326
