import pandas as pd
import requests
import json

from slackclient import SlackClient

def getconfigs(file):
    configs = json.load(open(file))
    apitoken = configs.get("slackapitoken")
    url = configs.get("apinode")
    blockinterval = configs.get("missedblockinterval")
    minmissedblocks = configs.get("minmissedblocks")
    channel_ids = configs.get("channel_ids")
    return apitoken,url,blockinterval,minmissedblocks,channel_ids

def getdelegates(url):
    delegates = pd.DataFrame(requests.get(url+'api/delegates?orderBy=vote').json()['delegates'])
    delegates['vote']=pd.to_numeric(delegates['vote'])
    return delegates

def getdmchannelid(userid,apitoken):
    slack_client = SlackClient(apitoken)
    api_call = slack_client.api_call("im.open",user=userid)
    channel_id=api_call['channel']['id']
    return channel_id

def getusernames(file):
    usernames=json.load(open(file))
    return usernames

def getuserlist(apitoken):
    slack_client = SlackClient(apitoken)
    userlist=slack_client.api_call("users.list")['members']
    return userlist

def processdelegates(delegatesnew,delegates):
    delegatesnew['missedblocksmsg']=0
    if delegates is None:
        delegatesnew['newmissedblocks']=0
        delegatesnew['newproducedblocks']=0
        return delegatesnew
    else:
        delegates.rename(columns={'missedblocks': 'missedold','producedblocks':'producedold','missedblocksmsg':'msgold'}, inplace=True)
        delegates=delegates[['username','missedold','producedold','newmissedblocks','newproducedblocks','msgold']]
        delegatesnew=pd.merge(delegatesnew,delegates,how='left',on='username')
        delegatesnew['missedblocksmsg']=delegatesnew['missedblocksmsg']+delegatesnew['msgold']
        delegatesnew['newmissedblocks']=delegatesnew['newmissedblocks']+delegatesnew['missedblocks']-delegatesnew['missedold']
        delegatesnew.loc[delegatesnew['missedblocks']-delegatesnew['missedold']>0, ['newproducedblocks']] = 0
        delegatesnew['newproducedblocks']=delegatesnew['newproducedblocks']+delegatesnew['producedblocks']-delegatesnew['producedold']
        delegatesnew.loc[delegatesnew['producedblocks']-delegatesnew['producedold']>0, ['newmissedblocks','missedblocksmsg']] = 0
        delegatesnew.loc[delegatesnew['newmissedblocks'].isnull(), ['newmissedblocks','missedblocksmsg','newproducedblocks']] = 0
        delegatesnew=delegatesnew.drop(['missedold','producedold','msgold'],axis=1)
        return delegatesnew

def makemissedblockmsglist(delegates,blockinterval,minmissedblocks):
    missedblockmsglist=[]
    for index, row in delegates.iterrows():
        if ((row['newmissedblocks']>=minmissedblocks)and(row['newmissedblocks']>row['missedblocksmsg']))and((row['missedblocksmsg']<=1)or(row['newmissedblocks']-row['missedblocksmsg']>blockinterval)):
            missedblockmsglist.append({"username":row['username'],"missedblocksmsg":row['newmissedblocks']})
    for i in missedblockmsglist:
        delegates.loc[delegates['username']==i["username"], ['missedblocksmsg']] = i["missedblocksmsg"]
    return delegates,missedblockmsglist

def modifymissedblockmsglist(missedblockmsglist,usernames,userlist):
    newmissedblockmsglist=[]
    for i in missedblockmsglist:
        print(i)
        name=i["username"]
        for j in usernames:
            if name == j["delegate"]:
                name = j["username"]
                for x in userlist:
                    if name==x["profile"].get('display_name'):
                        name="<@"+x.get('id')+">"
                i["username"]=name
        newmissedblockmsglist.append(i)
    return newmissedblockmsglist

def makemissedblockmsg(missedblockmsglist):
    message=""
    for i in missedblockmsglist:
            if message!="":
                message=message+"\n"
            if i["missedblocksmsg"]>1:
                message=message+i["username"] +" red. Missed " + str(int(i["missedblocksmsg"])) + " blocks. :alert:"
            else:
                message=message+i["username"] +" yellow. Missed " + str(int(i["missedblocksmsg"])) + " block. :warning:"
    return message
