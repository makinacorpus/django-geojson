==============
django-geojson
==============

See the `documentation <https://django-geojson.readthedocs.io/en/latest/>`_ for more information.

*django-geojson* is a set of tools to manipulate GeoJSON with Django >= 3.2:

* (De)Serializer for (Geo)Django objects, querysets and lists
* Base views to serve GeoJSON map layers from models
* GeoJSON model and form fields to avoid spatial database backends
  (compatible with *django-leaflet* for map widgets)


.. image:: https://readthedocs.org/projects/django-geojson/badge/?version=latest
    :target: http://django-geojson.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/django-geojson.svg
        :target: https://pypi.python.org/pypi/django-geojson

.. image:: https://img.shields.io/pypi/dm/django-geojson.svg
        :target: https://pypi.python.org/pypi/django-geojson

.. image:: https://travis-ci.org/makinacorpus/django-geojson.png?branch=master
    :target: https://travis-ci.org/makinacorpus/django-geojson

.. image:: https://coveralls.io/repos/makinacorpus/django-geojson/badge.png?branch=master
    :target: https://coveralls.io/r/makinacorpus/django-geojson


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
* Yann Fouillat (alias Gagaro) <yann.fouillat@makina-corpus.com>

Version 1.X:

* Daniel Sokolowski, serializer snippet
* ozzmo, python 2.6 compatibility

|makinacom|_

.. |makinacom| image:: http://depot.makina-corpus.org/public/logo.gif
.. _makinacom:  http://www.makina-corpus.com

=======
LICENSE
=======

Lesser GNU Public License
