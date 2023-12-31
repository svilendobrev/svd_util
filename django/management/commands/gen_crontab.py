from django.core.management.base import BaseCommand
from svd_util.django.jobs import cron_registry


class Command(BaseCommand):
    help = 'Generates text in crontab format from jobs registered in the cron registry'

    def add_arguments(self, parser):
        parser.add_argument(
            '-o', '--output', dest='output_file',
            help='Write result to output file',
        )

        parser.add_argument(
            '-u', '--user', dest='user',
            help='Include a linux user in crontab entries, suitable for generating files in /etc/cron.d/',
        )

    def handle(self, *args, **options):
        fpath = options.get('output_file')
        s = cron_registry.generate_crons( include_user=options.get('user'))
        if fpath:
            with open(fpath, 'w') as f:
                f.write(s)
                return
        return s


# vim:ts=4:sw=4:expandtab
