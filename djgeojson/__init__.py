#: Module version, as defined in PEP-0396.
pkg_resources = __import__('pkg_resources')
try:
    distribution = pkg_resources.get_distribution('django-geojson')
    __version__ = distribution.version
except:
    __version__ = 'unknown'
    import warnings
    warnings.warn('No distribution found.')

GEOJSON_DEFAULT_SRID = 4326
