import os
from io import open

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

setup(
    name='django-geojson',
    version='4.1.1dev',
    author='Mathieu Leplatre',
    author_email='mathieu.leplatre@makina-corpus.com',
    url='https://github.com/makinacorpus/django-geojson',
    download_url="http://pypi.python.org/pypi/django-geojson/",
    description="Serve vectorial map layers with Django",
    long_description=open(os.path.join(here, 'README.rst')).read() + '\n\n' +
                     open(os.path.join(here, 'CHANGES'), encoding='utf-8').read(),
    license='LPGL, see LICENSE file.',
    install_requires=[
        'Django>=4.0',
    ],
    extras_require={
        'field': ['django-leaflet>=0.12'],
        'docs': ['sphinx', 'sphinx-autobuild'],
    },
    packages=find_packages(),
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
    classifiers=['Topic :: Utilities',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Intended Audience :: Developers',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Development Status :: 5 - Production/Stable',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: 3.9',
                 'Programming Language :: Python :: 3.10',
                 'Programming Language :: Python :: 3.11',
                 'Programming Language :: Python :: 3.12',
    ],
)
