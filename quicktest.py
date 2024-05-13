import argparse
import os
import sys

import django
from django.conf import settings
from django.test.runner import DiscoverRunner


class QuickDjangoTest:
    """
    A quick way to run the Django test suite without a fully-configured project.

    Example usage:

        >>> QuickDjangoTest('app1', 'app2')

    Based on a script published by Lukasz Dziedzia at:
    http://stackoverflow.com/questions/3841725/how-to-launch-tests-for-django-reusable-app
    """
    DIRNAME = os.path.dirname(__file__)
    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'django.contrib.messages',
    )

    def __init__(self, *args, **kwargs):
        self.apps = args
        self.run_tests()

    def run_tests(self):
        """
        Fire up the Django test suite developed for version 1.2
        """
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.contrib.gis.db.backends.spatialite',
                    'NAME': os.path.join(self.DIRNAME, 'database.db'),
                }
            },
            INSTALLED_APPS=self.INSTALLED_APPS + self.apps,
            SPATIALITE_LIBRARY_PATH=os.getenv('SPATIALITE_LIBRARY_PATH', 'mod_spatialite'),
            TEMPLATES=[
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [],
                    'APP_DIRS': True,
                    'OPTIONS': {
                        "context_processors": [
                            "django.contrib.auth.context_processors.auth",
                            "django.contrib.messages.context_processors.messages",
                        ]
                    },
                },
            ],
            MIDDLEWARE=[
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
                'django.contrib.sessions.middleware.SessionMiddleware',
            ],
            SECRET_KEY="not-secret",
            # django.VERSION >= (3, 2)
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        )

        django.setup()

        # Workaround for incompatibility between SQLite 3.36+ and SpatiaLite 5,
        # as used on GitHub Actions. This change monkey patches
        # prepare_database() to avoid a call to InitSpatialMetaDataFull(). See:
        # https://code.djangoproject.com/ticket/32935
        # https://groups.google.com/g/spatialite-users/c/SnNZt4AGm_o
        from django.contrib.gis.db.backends.spatialite.base import DatabaseWrapper

        def prepare_database(self):
            super(DatabaseWrapper, self).prepare_database()
            with self.cursor() as cursor:
                cursor.execute("PRAGMA table_info(geometry_columns);")
                if cursor.fetchall() == []:
                    cursor.execute("SELECT InitSpatialMetaData(1)")

        DatabaseWrapper.prepare_database = prepare_database

        failures = DiscoverRunner().run_tests(self.apps, verbosity=1)
        if failures:  # pragma: no cover
            sys.exit(failures)

if __name__ == '__main__':
    """
    What do when the user hits this file from the shell.

    Example usage:

        $ python quicktest.py app1 app2

    """
    parser = argparse.ArgumentParser(
        usage="[args]",
        description="Run Django tests on the provided applications."
    )
    parser.add_argument('apps', nargs='+', type=str)
    args = parser.parse_args()
    QuickDjangoTest(*args.apps)
