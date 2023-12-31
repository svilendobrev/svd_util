import os
from io import StringIO

os.environ['DJANGO_COLORS'] = 'nocolor'

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.apps import apps
from django.db import connection

class Command(BaseCommand):
    help = 'Set all db sequences to MAX value of the according primary keys'

    def handle(self, *args, **options):
        commands = StringIO()
        cursor = connection.cursor()

        for app in apps.get_app_configs():
            label = app.label
            call_command('sqlsequencereset', label, stdout=commands)

        cursor.execute(commands.getvalue())
