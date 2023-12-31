from django.conf import settings
from django.core.management.base import BaseCommand
from svd_util.django.env import _ENV as ENV

class Command(BaseCommand):
    help = 'Checks for unused env settings'

    def handle(self, *args, **options):
        unused_env = ENV.from_file - ENV.used
        if unused_env:
            print('Unused env settings:', unused_env)
