# from twilio.rest import Client
#
# account_sid = 'ACfd75c7ca624dcf84a9d2a00a689127dc'
# auth_token = 'b0c62067f3ec95d912c3e978fe9b4051'
# client = Client(account_sid, auth_token)
# for x in range(0, 50):
#     message = client.messages.create(
#         from_='+18652384056',
#         body='eiehfnmdfnjkdnf',
#         to='+919316528832'
#     )
#
# print(message.sid)
import requests

url = "https://www.fast2sms.com/dev/bulkV2"

querystring = {
    "authorization": "API_KEY_OF_YOURS",
    "message": "This is test Message sent from \
    Python Script using REST API.",
    "language": "english",
    "route": "q",
    "numbers": "+919879804683"}

headers = {
    'cache-control': "no-cache"
}
try:
    response = requests.request("GET", url,
                                headers=headers,
                                params=querystring)

    print("SMS Successfully Sent")
except:
    print("Oops! Something wrong")