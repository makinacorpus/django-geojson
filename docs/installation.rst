Installation
============

::

    pip install django-geojson


This package has **optional** `extra dependencies <http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-extras-optional-features-with-their-own-dependencies>`_.


If you need GeoJSON fields with map widgets :

::

    pip install "django-geojson [field]"

Configuration
-------------

Add ``djgeojson`` to your applications :

::

    # settings.py

    INSTALLED_APPS += (
        'djgeojson',
    )

*(not required for views)*