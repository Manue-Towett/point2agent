import re
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    # Cookie: FallbackToDefaultLocation=True; _pk_id.4.0209=266d60174ff4ed6f.1689853526.; _fbp=fb.1.1689853527886.107856469; OptanonAlertBoxClosed=2023-07-20T11:45:31.096Z; P2HRecent=129619187; _bs=4ef76cf3-0d82-285b-f50f-71802146bac5; __utma=110305412.383336141.1689853525.1690559338.1690559338.1; __utmc=110305412; __utmz=110305412.1690559338.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _hjSessionUser_76828=eyJpZCI6ImUxMzBiNjBiLTE5MjctNWEzYS04YzE2LWIyNGJmZTA0NGMwOCIsImNyZWF0ZWQiOjE2OTA1NTkzMzc5NjAsImV4aXN0aW5nIjp0cnVlfQ==; _pbjs_userid_consent_data=3524755945110770; _pubcid=d6c79115-4447-4034-8a45-ed6273658319; _lr_env_src_ats=false; pbjs-unifiedid=%7B%22TDID%22%3A%22650baf6b-7a2d-497b-9bea-567409db43a1%22%2C%22TDID_LOOKUP%22%3A%22TRUE%22%2C%22TDID_CREATED_AT%22%3A%222023-06-28T15%3A51%3A04%22%7D; pbjs_fabrickId=%7B%22fabrickId%22%3A%22E1%3A80_p5t32XS6d0ps3CTi4XgnTVEN4Nocy5EhQU4Lp72_-RnpnCVybzV9XNJK-u7ZKqPwvvVZU5A0OmJCANNp0pLWc2DGla5jSAtpqDekycYA%22%7D; cto_bidid=8xaajV91UDVVdWNGSW9xTms5eGFtRnAlMkJHVVhOMUxqbExqJTJGeiUyQnJxQ1VkOEQ5VGglMkY0UUl3ZnJab0RJSTdud2tqUzFSc1dSNzNZNlpwT29DQWFsQ3ZnSkNBQ1BEdXZJUVFzN0RuOXlxb0dHMW5CMjNIRWJ4JTJCckZkWVdwJTJCU1VNUTNQY3QzWA; __cflb=0H28vFUwUbjB647CRtREnBdSfNZ6zw3MjruEwGFqsAt; _gid=GA1.2.562414172.1690896970; ClientLocationId=3269; ClientCountryCode=US; UserCountryId=MX; UserLocationId=33; __gads=ID=c605cea4f72992b8-222ac2201ce30099:T=1689853560:RT=1690896982:S=ALNI_MYWYNqFsFmchmdNg8qCHEba6nqFWw; __gpi=UID=00000c6cd1fb7a09:T=1689853560:RT=1690896982:S=ALNI_MasgvxTa7z4khal4Dq1F0vPdd6qOw; _cc_id=d5672f5740f305b87111528dad73e9e2; panoramaId_expiry=1690983382701; panoramaId=e3d13609ea5cedbcc9a29075cbada9fb927ade4e7ff98f40d73aa35f9a92c22c; panoramaIdType=panoDevice; cto_bundle=TCM17F9OTTd0MTJlZ0V2Z0lYcGtvb1lBMGRpS21KWjdIOVdJNUhiNmw4M3R1M201WXpyRUlGV2JUb0lQdG9TU2JGOE5uVHdrcUIzdW5XQnlwRnNPeXpFaGhYdHdJRUlqQUxKdVJOMnRpbiUyQm42MzhFenJPTEFMVHJ1NzdtMnd2YlhGcWlnamJ2WHZlUUtybnVkMlQ1dHViRVBoUSUzRCUzRA; g_state={"i_p":1691501786249,"i_l":3}; forms.firstname=Kipngetich; forms.lastname=Towett; forms.email=malingukevin@gmail.com; forms.phonenumber=(074) 661-0723; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Aug+02+2023+09%3A41%3A04+GMT%2B0300+(East+Africa+Time)&version=202303.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0003%3A0%2CC0004%3A0%2CC0002%3A0%2CC0001%3A1&geolocation=%3B&AwaitingReconsent=false; cf_clearance=zowFGeIOT4zYSNH99V1MITCWPyMB7guqdcJ7iXzQfco-1690958464-0-1-25965318.fbb3de28.72970cf8-0.2.1690958464; _ga=GA1.1.383336141.1689853525; arp_scroll_position=120; __cf_bm=aIvnhh13rPVefgnNN_lbL49BRliWy1_BU50XPItEn5I-1690974582-0-ATt9iiLQxett+t99G0fuRGlvszTrvDPtwsjtfOLEmfLjXdx7BAF6pbdFmiOFdQ8Hxd00IDX8j5s4iVjnUExkPSs=; _ga_XBM0745T8C=GS1.1.1690974582.10.0.1690974582.60.0.0
    "Dnt": "1",
    "Origin": "https://www.point2homes.com",
    # "Referer": "https://www.point2homes.com/MX/Real-Estate-Agents/Rob-Kinnon/522458.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

SESSION = requests.Session()

response = SESSION.get("https://www.point2homes.com/MX/Real-Estate-Agents/Rob-Kinnon/522458.html",
                       headers=HEADERS)

soup = BeautifulSoup(response.text, "html.parser")

form = soup.select_one("form#agent_form")

details = {}

for inp in form.select("input"):
    try:
        details[inp["name"]] = inp["value"]
    except:pass

regx = re.compile(r"sitekey'\s+:\s+\S(\w+)\S,", re.DOTALL)

sitekey = regx.search(str(form)).group(1)

print(sitekey)

print(details)

cookies = SESSION.cookies.get_dict()

cookie = ""

for key, value in cookies.items():
    cookie += "{}:{};".format(key, value)

payload = {
    "key": "a8dfbfbbfe30610fbf85e74e84a0ed7f",
    "method": "userrecaptcha",
    "googlekey": sitekey,
    "json": 1,
    "cookies": cookie,
    "pageurl": "https://www.point2homes.com/MX/Real-Estate-Agents/Rob-Kinnon/522458.html"
}

response = requests.post("http://2captcha.com/in.php", 
                         data=payload)

print(response.json())

params = {
    "key": payload["key"],
    "action": "get",
    "id": response.json()["request"],
    "json": 1
}

while True:
    time.sleep(15)

    try: 
        response = requests.get("http://2captcha.com/res.php", 
                                params=params)
        
        data = response.json()

        print(data)

        if data["request"] != "CAPCHA_NOT_READY":
            token = data["request"]

            break
        
    except:pass

details.update({
    "FromFirstName": "Kirui",
    "FromLastName": "Towett",
    "FromEmail": "malingukevin23@gmail.com",
    "FromPhone": "(074) 661-0734",
    "Subject": "Need the assistance of an agent",
    "Message": "Hi, I'm following your listings on Point2 and  would appreciate some suggestions related to my searches. Thanks so much!",
    "g-recaptcha-response": token
})

HEADERS["Content-Type"] = "x-www-form-urlencoded; charset=UTF-8"

HEADERS["Referer"] = "https://www.point2homes.com/MX/Real-Estate-Agents/Rob-Kinnon/522458.html"
import json

print(json.dumps(details))

details_ = "agentId=522458&listingId=0&contactAgentEventPage=AgentProfile&formLocation=AgentProfileLoadedInPage&trackingCategory=Consumer+Leads&trackingAction=Contact+Agent&FromFirstName=Kipngetich&FromLastName=Towett&FromEmail=malingukevin%40gmail.com&FromPhone=(074)+661-0723&Subject=Need+the+assistance+of+an+agent&Message=Hi%2C+I'm+following+your+listings+on+Point2+and++would+appreciate+some+suggestions+related+to+my+searches.%0D%0AThanks+so+much!&g-recaptcha-response={}".format(details["g-recaptcha-response"])


with open("details.json", "w") as file:
    json.dump(details, file, indent=4)

response = SESSION.post("https://www.point2homes.com/Email/ContactAgent/",
                        params=details,
                        headers=HEADERS)

print(response.status_code)

with open("sample.json", "w") as file:
    json.dump(response.json(), file, indent=4)