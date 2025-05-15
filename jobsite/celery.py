import os
from celery import Celery
from celery.schedules import crontab

# Call the setup first then import this function
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsite.settings')
django.setup()
from jobsboard.tasks import *


# Set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobsite.settings')

app = Celery('jobsite', backend=os.getenv('REDIS_URL'), broker=os.getenv('REDIS_URL'))

# app.control.purge()

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    # result_extended = True,
    worker_max_memory_per_child = 120000,
    # worker_max_tasks_per_child = 4,
    worker_concurrency = 1,
    result_expires = 600 # 10 minutes
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')





# Celery Beat config
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # ,hour='22-15'
    every_mins = 20
    # sender.add_periodic_task(crontab(minute=f'*/{every_mins}'), set_group_post_time.s(every_mins-1), name='Set Group Post Time')
    
    # Knocked off as to expensive (£££) to run
    # sender.add_periodic_task(crontab(minute='0',hour='18'), wxid_daily_check.s(), name='Daily WXID Check')
    # sender.add_periodic_task(crontab(minute='0',hour='22,5,10,15'), wxid_requested_check.s(), name='Frequent Requested ID Check')
    # sender.add_periodic_task(crontab(minute='40',hour='*'), wxid_requested_check.s(), name='Frequent Requested ID Check')


    sender.add_periodic_task(crontab(minute='0',hour='*/6'), remove_stagnant_temp_files.s(), name='Remove Stagnant Files')
    # sender.add_periodic_task(crontab(), sync_redis_postgres.s(), name='Sync Redis and Postgres')

    
    # sender.add_periodic_task(crontab(minute='0',hour='0'), publish_and_reset_rejected.s(), name='Publish and Reset Rejected')

    