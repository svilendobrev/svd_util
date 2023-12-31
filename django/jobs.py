import sys
import os
from redis.exceptions import ConnectionError as RedisConnectionError
from django.db.utils import ProgrammingError
from django.conf import settings


class AppConfigMixin:
    regular_jobs = {}
    '''
    Sample:
    regular_jobs = {
        'my regular job1': dict(
            callable='python.path.to.rq_job_callable',
            queue='default', # optional
            cron_string='0 0 * * *', # daily at midnight
            exclusive=True, # run this task only if already running, default is True
        ),
    }
    '''
    def ready(self):
        super().ready()
        self.register_regular_jobs()

    def register_regular_jobs(self):
        for name, descr in self.regular_jobs.items():
            cron_registry.add_job( name, descr)


use_rqscheduler = 'scheduler' in settings.INSTALLED_APPS

class CronRegistry:
    jobs = {}

    def add_job(self, name, descr):
        assert name not in self.jobs
        self.jobs[ name] = descr
        if use_rqscheduler:
            try:
                return self._rqscheduler_add_job( name, descr)
            except ProgrammingError:
                print('"scheduler" app not migrated yet?')
            except RedisConnectionError:
                print('redis not running?')

    def _rqscheduler_add_job(self, name, descr):
        from scheduler.models import CronJob
        o, created = CronJob.objects.get_or_create(
            name=name,
            callable = descr['callable'],
            defaults = dict(
                queue = descr.get('queue', 'default'),
                cron_string = descr['cron_string'],
            )
        )
        return o

    def generate_crons(self, include_user=None):  # use include_user='<linux user>' for generating files in /etc/cron.d/; otherwise leave empty for user crontab
        lines = []
        python_executable = sys.executable
        for name, descr in self.jobs.items():
            cron_string = descr['cron_string']
            queue = descr.get('queue', 'default')
            job = descr['callable']
            project_path = settings.PROJECT_ROOT
            cmd = f'{python_executable} manage.py rqenqueue --queue {queue} {job}'
            if descr.get('exclusive', True):
                namespace = os.path.basename( project_path) # in case of multiple installs on the same machine
                lock = f'{namespace}-{name}-cron.lock'.replace(' ', '-')
                cmd = f'/usr/bin/flock -n /tmp/{lock} {cmd}'
            cmd = f'cd {project_path} && {cmd}'
            if include_user:
                lines.append(f'{cron_string} {include_user} {cmd}')
            else:
                lines.append(f'{cron_string} {cmd}')
        return '\n'.join(lines) + '\n'


cron_registry = CronRegistry()  # singleton


# vim:ts=4:sw=4:expandtab
