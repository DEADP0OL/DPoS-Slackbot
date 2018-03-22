from functions import *

apitoken,url,blockinterval,minmissedblocks,channel_ids=getconfigs('config.json')
delegatesnew=getdelegates(url)

try:
    #delegatesold=None#restartcounters
    delegates = pd.read_csv("delegates.csv",index_col=0)
except FileNotFoundError:
    delegates=None
    print("Program Initialized")

delegates=processdelegates(delegatesnew,delegates)
delegates,missedblockmsglist=makemissedblockmsglist(delegates,blockinterval,minmissedblocks)
delegates.to_csv('delegates.csv')
if len(missedblockmsglist)>0:
    usernames=getusernames('usernames.json')
    userlist=getuserlist(apitoken)
    missedblockmsglist=modifymissedblockmsglist(missedblockmsglist,usernames,userlist)
    message=makemissedblockmsg(missedblockmsglist)
    if message !="":
        slack_client = SlackClient(apitoken)
        for channel_id in channel_ids:
            slack_client.api_call("chat.postMessage",channel=channel_id,text=message,as_user=True)