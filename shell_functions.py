# MAKE SURE DATABASE NOT USING INTERNAL SETTINGS!!!
# SOME FUNCTIONS NOT WORKING WITH MULTIPLE INDENTATIONS



# 3) Check for new wx_aliases based on their wxid

import requests
import json
import os
from django.db import IntegrityError
from time import sleep
from jobsboard.models import Job, WxidAlias

# from jobsboard.models import *
# import sys
# sys.path.append("..")
# from wx_scripts import check_new_ids
# check_new_ids(Job, WxidAlias)

def check_new_ids(start, end):
    wId = os.getenv('wId')
    headers = {
            'Authorization': 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzE2MzI3MzY3NyIsInBhc3N3b3JkIjoiJDJhJDEwJHlUamdScXFNQnJvb3VWbGk2Y1hvc2VoL3V1cnVOSnYuWnU4Mjh1aDBJZWM0cDFrVHMwZENDIn0.3m2bDjrQzDJkV8poSZHakWgmt3zMKdeb1NX_hTrhDs5p0TWnpHZA5BiVj43rSZZ4z8AtkXyqgZCHAXoirKi8fw',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }
    url = 'http://59.36.146.193:9899/getContact'

    wxids = list(Job.objects.filter(is_job=True, wxid_alias__wx_alias__len=0).values_list('wxid_alias__wxid', flat=True).distinct())
    print(f'TOTAL WKIDS: {len(wxids)}')

    new_aliases = []

    wxids = wxids[start:end]

    for i,wxid in enumerate(wxids):
        if i and not i % 30:
            print('sleeping...')
            sleep(30)

        print(f'wId: {wId}')
        print(f'WXID: {wxid}')
        payload = {
            'wId' : wId,
            'wcId' : wxid
        }

        res = requests.post(url, headers=headers, data=json.dumps(payload))
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
            except IntegrityError as e:
                print(e)
        else:
            print('No Alias Found.')

    print(f'Execution complete with {len(new_aliases)} new aliases found.')
    print('**********************************')
    for i,alias in enumerate(new_aliases):
        print(i, alias)


# Run main function once a day to check ALL IDs
# Run a smaller version to just check requested IDs, 6 times a day and email people that have requested IDs