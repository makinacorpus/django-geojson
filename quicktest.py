import os
import sys
import argparse
from django.conf import settings


class QuickDjangoTest(object):
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
    )

    def __init__(self, *args, **kwargs):
        self.apps = args
        self.version = self.get_test_version()
        self.run_tests()

    def get_test_version(self):
        """
        Figure out which version of Django's test suite we have to play with.
        """
        from django import VERSION
        if VERSION[0] == 1 and VERSION[1] >= 7:
            return '1.7'
        elif VERSION[0] == 1 and VERSION[1] >= 2:
            return '1.2'
        else:
            return

    def run_tests(self):
        """
        Fire up the Django test suite developed for version 1.2
        """
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.contrib.gis.db.backends.spatialite',
                    'NAME': os.path.join(self.DIRNAME, 'database.db'),
                    'USER': '',
                    'PASSWORD': '',
                    'HOST': '',
                    'PORT': '',
                }
            },
            INSTALLED_APPS=self.INSTALLED_APPS + self.apps,
        )
        from django.test.simple import DjangoTestSuiteRunner
        if self.version == '1.7':
            import django
            django.setup()
        failures = DjangoTestSuiteRunner().run_tests(self.apps, verbosity=1)
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
