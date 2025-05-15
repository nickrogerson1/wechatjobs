from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from django.views import View
from django.http import JsonResponse

from ..models import Job, WxidAlias, GroupId, Handle
from .parser import text_parser
from difflib import SequenceMatcher
from celery import shared_task

import time
import requests
import json
import os
import redis

r = redis.Redis(host=os.getenv('REDISHOST'), port=os.getenv('REDISPORT'),username="default", password=os.getenv('REDISPASSWORD'),decode_responses=True)
wId = os.getenv('wId')
#https://wechatjobs.com/wx-endpoint/





# Get alias, group_name then handle
def get_additional_info(group_id, wxid):
    t1 = time.time()

    headers = {
        'Authorization': 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzE2MzI3MzY3NyIsInBhc3N3b3JkIjoiJDJhJDEwJHlUamdScXFNQnJvb3VWbGk2Y1hvc2VoL3V1cnVOSnYuWnU4Mjh1aDBJZWM0cDFrVHMwZENDIn0.3m2bDjrQzDJkV8poSZHakWgmt3zMKdeb1NX_hTrhDs5p0TWnpHZA5BiVj43rSZZ4z8AtkXyqgZCHAXoirKi8fw',
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json'
    }

    url = 'http://36.111.205.110:9899/getContact'
    
    payload = {
        'wId' : wId,
        'wcId' : wxid
    }

    try:
        # See if there is wxid for this wxid
        wxid_alias = WxidAlias.objects.get(wxid=wxid)
        print(f'wxid_alias: {wxid_alias}')

        wx_alias = wxid_alias.wx_alias
        alias = ''
        print(f'ALIAS LIST: {wx_alias}')

    # Only check if there are no aliases for this person
        if not wx_alias:
        # Otherwise try and get it
            try:
                res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
                alias = json.loads(res.text)['data'][0]['aliasName']

                # print('PART 1')
                # print('#######################')
                # print(res)
                # print(alias)
                # print('#######################')

            except Exception as e:
                print(e)

        print(f'ALIAS FROM REQ: {alias}')

        alias_changed = False

    # Check not None, then check it's not a dupe
        if alias and alias.upper() not in map(str.upper, wxid_alias.wx_alias):
            print(f'\033[33mALIAS ADDED TO ALIAS LIST!: {wxid}\033[0m')
            wxid_alias.wx_alias += [alias]
            alias_changed = True

    # Add in wxids that don't start with wxid
        if not wxid.startswith('wxid_') and wxid.upper() not in map(str.upper, wxid_alias.wx_alias):
            wxid_alias.wx_alias += [wxid]
            alias_changed = True
            
    # Save everything if changed
        if alias_changed:
            wxid_alias.save()
        
        
    except WxidAlias.DoesNotExist as e:
        print(e)
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)

        # print('PART 2')
        # print('#######################')
        # print(res)
        # # print(alias)
        # print('#######################')

        alias = json.loads(res.text)['data'][0]['aliasName']
        if alias:
            wxid_alias = WxidAlias.objects.create(wxid=wxid, wx_alias=[alias])
        else:
        # Use default
            wxid_alias = WxidAlias.objects.create(wxid=wxid)

    except IntegrityError as e:
    # Errors out if duplicate WXID
        print(e)




    url = "http://36.111.205.110:9899/getChatRoomInfo"
    payload = {
        'wId' : wId,
        'chatRoomId' : group_id
    }
    wx_handle = ''

    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        r = json.loads(res.text)

        # print('PART 3')
        # print('#######################')
        # print(r)
        # # print(r['data'])
        # # print(alias)
        # print('#######################')


        group_name = r['data'][0]['nickName']

        for u in r['data'][0]['chatRoomMembers']:
            # print(u['userName'])
            if u['userName'] == wxid:
                wx_handle = u['nickName']
                break
    except Exception as e:
        print(e)



    # try:
    #     # If group name different, then change it
    #     group = GroupId.objects.get(group_id=group_id)
    #     if group.group_name != group_name:
    #         group.group_name = group_name   
    #         group.save()
    #         print(f'CHANGED GROUP NAME FOR: {group_name}')
    # except GroupId.DoesNotExist:
    #     # Create a new one otherwise
    #     group = GroupId.objects.create(group_id=group_id, group_name=group_name)
    # except IntegrityError as e:
    #     print(e)

    # Remove '@chatroom' before search
    group_id = group_id[:group_id.index('@')]

    group, created = GroupId.objects.get_or_create(group_id=group_id)
    if group.group_name != group_name:
        group.group_name = group_name   
        group.save()
        print(f'CHANGED GROUP NAME FOR: {group_name}')



    try:
    # If handle different, then change it
        handle = Handle.objects.get(wxid=wxid_alias,group=group,handle=wx_handle)
        if handle.handle != wx_handle:
            handle.handle = wx_handle  
            handle.save()
            print(f'CHANGED GROUP NAME FOR: {handle}')
    except Handle.DoesNotExist:
        # Create a new one otherwise
        if wx_handle:
            handle = Handle.objects.create(wxid=wxid_alias,group=group,handle=wx_handle)
            print(f'New handle created for {wx_handle}!')
        else:
        # Create an instance which has no Handle and is not saved to DB
            handle = Handle(wxid=wxid_alias,group=group,handle='')
            print(f'New handle INSTANCE created for {wxid}!')
    except IntegrityError as e:
        print(e)

    
    print(f'TIME TAKEN: {time.time() - t1}')

    return [wxid_alias, group, handle]



# Get the list from redis
# Block access the list with lock
# If val not in list, then add it and continue
# If val in list, stop immediately
# Release lock 



# Hands over to Redis/Celery
@shared_task
def process_message(d):

    # print('Process Message fired!')

    text = d['content']
    group_id = d['fromGroup']
    wxid = d['fromUser']

    # Check if an exact match
    if r.sismember('jds',text):
        r.incr('rejected')
        print('Exact Match!')
        return
    else:
    # Add the val immediately to the Set
         r.sadd('jds',text)

# This is an expensive check, so try to use sparingly!!
# Get all jobs and check new job similarity against db
    with r.lock('jd_lock'):
        job_descs = r.smembers('jds')
        print(f'JD SET LEN: {len(job_descs)}')
    # Remove the val from the Set before the similarity check starts
        job_descs.discard(text)

        # Add to job desc here to stop further near match checks
        # r.sadd('jds',text)
        
        for jd in job_descs:   
            diff = SequenceMatcher(a=text, b=jd).ratio()
            if diff > 0.9:
                print('************************************')
                print('************************************')
                print(f'The likeness ratio is {diff}')
                print('************************************')
                print('************************************\n\n')
            
            # Count rejected
                r.incr('rejected')
                return
            
        # Add job desc to list if loop finishes
        # r.sadd('jds',text)


    # Release lock and move out of the cxt manager
    print('NO MATCH. MADE IT THROUGH TO PARSER!')
    
    cities, job_types, subjects, is_job, trans = text_parser(text)

    # Return here if the word count is not enough
    if cities == 'Not Long Enough':
        return


    wxid_alias, group, handle = get_additional_info(group_id, wxid)

    print('\043[35mJOB BEING ADDED TO DB....\043[0m' if is_job else '\042[35mNONE JOB BEING ADDED TO DB\042[0m')
    
    fields = {
        'wx_handle': handle,
        'wxid_alias': wxid_alias,
        'group': group,
        'cities': cities,
        'job_types': job_types,
        'subjects': subjects,
        'job_description': text,
        'jd_translation': trans,
        'is_job': is_job
    }

    try:
        Job.objects.create(**fields)
    except IntegrityError as e:
        print(e)
    except Exception as e:
        print(e)

    print('************************************************')





# This only intercepts the POST and decides whether to send it to Redis/Celery
@method_decorator(csrf_exempt, name='dispatch')
class HttpCallback(View):

    def post(self, request, *args, **kwargs):

        message_type = json.loads(request.body)["messageType"]
        print(f'Message Type: {message_type}\n')
        
        d = json.loads(request.body)['data']

        if d['fromUser'] == 'wxid_2g8rvewqmqf612':
            print("It's ME!!")
            return

        if message_type == 9:
            # print('Point 1')
            process_message.delay(d)
            # print('Point 2')
        return JsonResponse({'success':True})
    
#https://wechatjobs.com/wx-endpoint/