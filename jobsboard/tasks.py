from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db import IntegrityError
from django.utils import timezone
from django_drf_filepond.models import TemporaryUpload
from .models import Job, GroupId, AdMessage, WxidAlias
import redis
import random
from datetime import datetime, timedelta
import requests
import json
from pathlib import Path
import shutil
import os
from time import sleep
from random import randint

r = redis.Redis(host=os.getenv('REDISHOST'), port=os.getenv('REDISPORT'),username="default", password=os.getenv('REDISPASSWORD'),decode_responses=True)


@shared_task
def send_email(email_subject, message, sender, recipients):

    return send_mail(
        email_subject,
        message,
        sender,
        recipients,
        html_message = message
    )


@shared_task
def delete_temp_files(*stored_uploads):
    print(f'STORED UPLOADS: {stored_uploads}')
    print(f'TYPE: {type(stored_uploads)}')

    temp_folder = Path(__file__).resolve().parent.parent / 'filepond-temp-uploads'

    for f in stored_uploads:
        shutil.rmtree(temp_folder / f, ignore_errors=False)
        print(temp_folder / f)




# *********************** 
# CELERY BEAT FUNCTIONS:
# *********************** 
@shared_task
def remove_stagnant_temp_files():
    temp_folder = Path(__file__).resolve().parent.parent / 'filepond-temp-uploads'
    dir_files = os.listdir(temp_folder)
    print(f'DIR FILES: {dir_files}')

    for f in dir_files[:2]:
        if f != '.DS_Store':
            tu = TemporaryUpload.objects.get(upload_id=f)
            print(f'SINCE UPLOAD TIME: {timezone.now() - tu.uploaded}')
            if (timezone.now() - tu.uploaded) < timezone.timedelta(hours=1):
                print("It's less than an hour old and not deleted.")
                continue

            shutil.rmtree(temp_folder / f, ignore_errors=False)
            print(temp_folder / f)


# Keep the postgres DB job descriptions in sync with the Redis ones
# Can fall out of sync due to errors, connection failures etc
@shared_task
def sync_redis_postgres():
    pg_job_vals = list(Job.objects.all().order_by('-time_created').values_list('job_description', flat=True))
    with r.lock('jd_lock'):
        r.delete('jds')
        r.sadd('jds', *pg_job_vals)







headers = {
    'Authorization': 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzE2MzI3MzY3NyIsInBhc3N3b3JkIjoiJDJhJDEwJHlUamdScXFNQnJvb3VWbGk2Y1hvc2VoL3V1cnVOSnYuWnU4Mjh1aDBJZWM0cDFrVHMwZENDIn0.3m2bDjrQzDJkV8poSZHakWgmt3zMKdeb1NX_hTrhDs5p0TWnpHZA5BiVj43rSZZ4z8AtkXyqgZCHAXoirKi8fw',
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Content-Type': 'application/json'
}

# Marketing Related Beat Tasks
@shared_task
def post_message(delay):

    groups = r.lrange('groups',0,-1)
    print(f'REDIS GROUPS LIST LEN: {len(groups)}')

    if not groups:
    # Then pull the group IDs out of the DB
        groups = list(GroupId.objects.all().values_list('group_id', flat=True))

    num = random.randint(0,len(groups)-1)
    print(f'RAND NUM: {num}')

    group_id = groups.pop(num)
    group_name = GroupId.objects.get(group_id=group_id).group_name
    print(f'Group ID: {group_id}')
    print(f'Group Name: {group_name}')
    # print(f'New Group: {groups}')

    # Update Redis groups tally
    r.delete('groups')
    r.rpush('groups', *groups)


    message = AdMessage.objects.order_by('?').first()
    # if message:
    print(f'Ad Text: {message.text}')

    payload = { 
        'wId': os.getenv('wId'),
        'wcId': group_id + '@chatroom',
        'content': message.text
    }

    # Send the actual group message!!
    res = requests.post('http://36.111.205.110:9899/sendText', headers=headers, data=json.dumps(payload))
    print(f"Message result: {json.loads(res.text)['message']}")

    result = json.loads(res.text)['message']
    # message_id = 2 #message.id


    new_data = [delay.isoformat(),datetime.now().isoformat(),
                group_name,group_id,len(groups),message.id,result]

    print(new_data)

    retrieved_list = r.get('todays_post_data')

    # Can probably combine this into one step
    new_list = json.loads(retrieved_list) if retrieved_list else []
    new_list.append(new_data)

    r.set('todays_post_data', json.dumps(new_list))

    # Can remove this post testing
    stored_list = json.loads(r.get('todays_post_data'))
    print(f'Stored List: {stored_list}')
    print('Data saved!')

    last_run_date = r.get('daily_task_last_run')
    print(f'last run day: {last_run_date}')
    if last_run_date:
    # check the day of the month with the stored one
        has_run_today = datetime.fromisoformat(last_run_date).day == datetime.now().day
    else:
        has_run_today = False

    print(f'Curr hour: {datetime.now().hour}')
    print(f'Has run today: {has_run_today}')

        
    # If it's passed 12 noon and retrieved_list not empty
    # Then empty list and run following code
    # Then publish the daily report
    if datetime.now().hour >= 11 and not has_run_today:
        print('Daily report fired!')

        for data in new_list:
            data[0] = datetime.fromisoformat(data[0])
            data[1] = datetime.fromisoformat(data[1])

        # Reassign message
        message = render_to_string('admin_emails/wx_post.html', {
            'data' : new_list,
            'now': datetime.now()
        })

        print(message)

        print(f'Time: {datetime.now()}')
        send_email('Cron job email', 
                message, 
                'cj@wechatjobs.com', 
                ['nickrogerson11@gmail.com'])
        
        print('CJ Email sent!!')
        
    # Finally clear data and start again
        r.delete('todays_post_data')
        r.set('daily_task_last_run', datetime.now().isoformat())



# Sets the precise time to post the message 
@shared_task
def set_group_post_time(mins):
    print('Post Ad To Groups Fired!')
    rand_mins = random.randint(0,mins)
    rand_secs = random.randint(0,59)
    rand_milli = random.randint(0,999)
    print(f'Rand Mins: {rand_mins}')
    print(f'Rand Secs: {rand_secs}')
    print(f'Rand Milli: {rand_milli}')
    delay = datetime.now() + timedelta(minutes=rand_mins, seconds=rand_secs, microseconds=rand_milli)
    post_message.apply_async(args=[delay],eta=delay)


# from requests.exceptions import ConnectTimeoutError

def get_contact_info(wxid, time=70):
    payload = {
        'wId' : os.getenv('wId'),
        'wcId' : wxid
    }
    try:
        return requests.post('http://36.111.205.110:9899/getContact', headers=headers, data=json.dumps(payload))
    except Exception as e:
        # print(e)
        print(f'ConnectionError so sleeping for {time}...')
        sleep(time)
        # Then try again
        return get_contact_info(wxid, time+30)


# Update the DB with new IDs
def check_new_ids(daily_check):

    print(f'Daily Check: {daily_check}')

    # wxid_alias__wx_alias_request_by_user__isnull=daily_check - this decides whether to just check the requested ones or not
    wxids = list(Job.objects.filter(is_job=True,wxid_alias__wx_alias__len=0,wxid_alias__wx_alias_request_by_user__isnull=daily_check)
                 .values_list('wxid_alias__wxid', flat=True).distinct())

    print(f'TOTAL WKIDS: {len(wxids)}')

    new_aliases = []

    for i,wxid in enumerate(wxids):
# Unlikely to be enough for the requested check to add extra logic here
        if i and not i % 10:
            print('sleeping...')
            sleep(randint(40,60))

        print(f'WXID: {wxid}')
        
        res = get_contact_info(wxid)
        print(res)

        alias = json.loads(res.text)['data'][0]['aliasName']
        print(f'\033[32m{i}) ALIAS: {alias}\033[0m')

        if alias:
            try:
                obj = WxidAlias.objects.get(wxid=wxid)
                obj.wx_alias += [alias]
                obj.save()
                print(f'\033[35mALIAS SAVED: {alias}\033[0m')
                new_aliases.append(alias)

                if not daily_check:
                # Inform the candidate that we found the Alias
                    handles = set(handle.handle for handle in obj.handle.all())
                    candidate_email = obj.wx_alias_request_by_user.user.email
                    jobs = Job.objects.filter(is_job=True,wxid_alias__wxid=wxid)
                    
                    message = render_to_string('admin_emails/email_requester_success.html', {
                        'poster_handles': handles,
                        'wx_alias': obj.wx_alias,
                        'jobs': jobs
                    })

                    print(message)

                    send_email('Your Wechat ID Request Has Been Successful', 
                            message, 
                            '"Wechat Jobs" <wechat_id_request@wechatjobs.com>',
                            [candidate_email, 'nickrogerson11@gmail.com'])
                    
                    print('Email sent to WXID requester!')

            except IntegrityError as e:
                print(e)
            
        else:
            print('No Alias Found.')


    print(f'Execution complete with {len(new_aliases)} new aliases found.')
    print('**********************************')
    for i,alias in enumerate(new_aliases):
        print(i+1, alias)


# Beat functions which call the function above
@shared_task
def wxid_daily_check():
    check_new_ids(True)
    
@shared_task
def wxid_requested_check():
    check_new_ids(False)


@shared_task
def publish_and_reset_rejected():

    rejected_count = r.getset('rejected',0)
    message = f'{rejected_count} were rejected in the last 24 hours.'

    send_mail(
        'Rejected Count',
        message,
        'mail@wechatjobs.com',
        ['nickrogerson11@gmail.com'],
        html_message = message
    )