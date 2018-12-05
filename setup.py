import os
from io import open
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

setup(
    name='django-geojson',
    version='2.12.0',
    author='Mathieu Leplatre',
    author_email='mathieu.leplatre@makina-corpus.com',
    url='https://github.com/makinacorpus/django-geojson',
    download_url="http://pypi.python.org/pypi/django-geojson/",
    description="Serve vectorial map layers with Django",
    long_description=open(os.path.join(here, 'README.rst')).read() + '\n\n' +
                     open(os.path.join(here, 'CHANGES'), encoding='utf-8').read(),
    license='LPGL, see LICENSE file.',
    install_requires=[
        'Django',
        'six',
    ],
    extras_require={
        'field': ['jsonfield', 'django-leaflet>=0.12'],
        'docs': ['sphinx', 'sphinx-autobuild'],
    },
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=['Topic :: Utilities',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Intended Audience :: Developers',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Development Status :: 5 - Production/Stable',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5'],
)
