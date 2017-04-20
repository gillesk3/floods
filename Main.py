from resources import util
from resources.satellite.api import API
from datetime import datetime
import os

from resources.notifications.notify import notify

#
# pushKey = util.configSectionMap("Keys")['pushbullet']
# print(pushKey)
#
# # a = notify()
# note = notify(pushKey)
# note.getDevices()



api = API('gillesk3','rockyou94',notify=True)
inputLocale = util.checkFolder('Locale', Input=True)
inputLocale = os.path.join(inputLocale,'shannon.geojson')
# start1=datetime.now() - relativedelta(years=1)

year = 2016
while year < 2017:
    start = datetime(year, 12,15)
    end = datetime(year+1, 1,15)
    print(start, end)
    results = api.query(inputLocale,startDate=start,endDate = end)
    print(len(results))
    if len(results) > 0:
        api.download(results,locale = 'Athlone')
    year += 1


note = notify.getNotify();
note.push('Finished')
print('fin')