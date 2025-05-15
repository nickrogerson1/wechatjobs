
def iterate_over_potential_wxid_ids():
    # Get values from database
    ids = WxidAlias.objects.all()
    for i,id in enumerate(ids)[100:]:
        if i % 100:
            time.sleep(10)
            id = id.wxid
            if not id.startswith('wxid'):
                print(i)
                payload['wcId'] = id
                res = json.loads(requests.post('http://59.36.146.193:9899/searchUser', headers=headers, data=json.dumps(payload)).text)
                pprint(res)
                
                if int(res['code']) == 1000:
                    print('ID SAVED!')

                    obj = WxidAlias.objects.get(wxid=id)
                    obj.wx_alias += [wx_alias]
                    obj.save()