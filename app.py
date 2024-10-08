import datetime
from flask import Flask, request, jsonify
import jwt
#from salesforce import Salesforce
from flask_cors import CORS
import requests
import os
import json
import firebase_admin
from firebase_admin import credentials, messaging


cred = credentials.Certificate('./mobile-push-d5660-firebase-adminsdk-j7187-03d78489b6.json')
firebase_admin.initialize_app(cred)

json_file_path = './mobile-push-d5660-firebase-adminsdk-j7187-03d78489b6.json'

# Open the JSON file and load its content
with open(json_file_path, 'r') as json_file:
    data = json.load(json_file)

# Print the full JSON data in a readable format
print(json.dumps(data, indent=4))  # Use i

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'FLEKNNIRQSQ'

obj = {}
obj['isError'] = False

endpoint_url = 'https://account-dev-ed.develop.my.site.com/paaraiboys/services/apexrest/paaraiboys'
headers = {'Content-Type': 'application/json'}

@app.route('/sendEmail', methods=['POST'])
def send_email():
    data = request.json
    sender = data.get('sender')
    to = data.get('to')
    cc = data.get('cc')
    subject = data.get('subject')
    html_body = data.get('html_body')
    smtp2go_url = 'https://api.smtp2go.com/v3/email/send'
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'X-Smtp2go-Api-Key': os.environ.get('EMAIL_API')
    }

    payload = {
        "sender": sender,
        "to": to,
        "cc": cc,
        "subject": subject,
        "html_body": html_body
    }
    print(payload)
    print(headers)
    try:
        response = requests.post(smtp2go_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status() 

        return jsonify({
            'isError': False,
            'message': 'Email sent successfully!',
            'response': response.json()
        })

    except requests.exceptions.RequestException as err:
        return jsonify({
            'payload' : payload,
            'headers' : headers,
            'isError': True,
            'message': f'Failed to send email: {str(err)}'
        })

@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/sendNotification', methods=['POST'])
def send_notification():
    data = request.json
    title = data.get('title')
    body = data.get('body')
    registration_tokens = data.get('registration_tokens')

    # Debug prints to check incoming data
    print("Received Notification Data:")
    print("Title:", title)
    print("Body:", body)
    print("Registration Tokens:", registration_tokens)

    try:
        if len(registration_tokens) == 1:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                token=registration_tokens[0],
            )
            # This is line 87 where the error occurs
            response = messaging.send(message)
        else:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                tokens=registration_tokens,
            )
            response = messaging.send_multicast(message)

        print('Successfully sent message:', response)
    except Exception as e:
        print("Error sending notification:", str(e))
        json_file_path = './mobile-push-d5660-firebase-adminsdk-j7187-03d78489b6.json'

        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
        print(json.dumps(data, indent=4))
        #raise

    return 'Notification sent'

@app.route('/getToken', methods=['POST'])
def get_token():
    data = request.json
    user_name = data.get('userName')
    pin = data.get('pin')
    deviceToken = data.get('deviceToken')
    post_data = {'userName': user_name, 'type' : 'gettoken', 'deviceToken': deviceToken}
    print(112)
    response = requests.post(endpoint_url, data=json.dumps(post_data), headers=headers)
    print(114, response)
    if response.status_code == 200:
        member = json.loads(response.json())
        if 'PIN__c' in member and pin == member['PIN__c']:
            payload = {
                'memberId': member['Id'],
                'paaraiId': member['Paarai_Id__c']
            }
            obj['Name'] = member['Name']
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            obj['token'] = token
        else:
            obj['isError'] = True
            obj['message'] = 'Incorrect Pin'
    else:
        obj['isError'] = True
        obj['message'] = 'Error in fetching member info from the server'
    print(obj)
    return jsonify(obj)

@app.route('/getMemberInfo', methods=['POST'])
def get_member_info():
    data = request.json
    token = data.get('token')
    obj = {}
    obj['isError'] = False
    decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    member_id = decoded['memberId']
    print('member_id ', member_id)
    post_data = {'member_id': member_id, 'type' : 'getInfo'}
    
    response = requests.post(endpoint_url, data=json.dumps(post_data), headers=headers)
    
    if response.status_code == 200:
        member = json.loads(response.json())
        obj['data'] = member
    else:
        obj['isError'] = True
        obj['message'] = 'Error in fetching member info from the server'
    print('kalai ', obj)
    return jsonify(obj)

@app.route('/getNews', methods=['POST'])
def get_news():
    token = request.json.get('token')
    obj = {'isError': False}
    try:
        decoded = jwt.decode(token, 'FLEKNNIRQSQ', algorithms=['HS256'])
        post_data = {'type' : 'getNews'}
        response = requests.post(endpoint_url, data=json.dumps(post_data), headers=headers)
        print(response)
        if response.status_code == 200:
            obj['data'] = json.loads(response.json())
    except Exception as err:
        obj['isError'] = True
        obj['message'] = str(err)
    return jsonify(obj)


@app.route('/getMemberList', methods=['POST'])
def get_member_list():
    token = request.json.get('token')
    obj = {'isError': False}
    try:
        decoded = jwt.decode(token, 'FLEKNNIRQSQ', algorithms=['HS256'])
        post_data = {'type' : 'getMemberList'}
        response = requests.post(endpoint_url, data=json.dumps(post_data), headers=headers)
        print(response)
        if response.status_code == 200:
            obj['data'] = json.loads(response.json())
    except Exception as err:
        obj['isError'] = True
        obj['message'] = str(err)
    return jsonify(obj)

# @app.route('/getEventList', methods=['POST'])
# def get_event_list():
#     data = request.json
#     token = data.get('token')
#     obj = {}
#     obj['isError'] = False

#     try:
#         decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
#         query = ("SELECT Id, Name, Start_Date__c, End_Date__c, Member__r.Name, "
#                  "(SELECT Name, Incharge__r.Name, Start_Time__c, Duration__c FROM Competitions__r) "
#                  "FROM Event__c ORDER BY Start_Date__c DESC")
#         result = sf.query(query)
        
#         if result['records']:
#             obj['data'] = result['records']
#         else:
#             obj['isError'] = True
#             obj['message'] = 'No events found'
#     except jwt.InvalidTokenError:
#         obj['isError'] = True
#         obj['message'] = 'Invalid token'

#     return jsonify(obj)

# @app.route('/saveNews', methods=['POST'])
# def save_news():
#     token = request.json.get('token')
#     obj = {'isError': False}

#     try:
#         decoded = jwt.decode(token, 'FLEKNNIRQSQ', algorithms=['HS256'])
#         memberId = decoded['memberId']
#         data = request.json.get('news')
#         current_date = datetime.datetime.now().isoformat().split('T')[0]
        
#         news_inst = {
#             'Is_Approved__c': False,
#             'Member__c': memberId,
#             'Description__c': data['description'],
#             'Created_Date__c': current_date,
#             'Title__c': data['title'],
#         }
#         result = sf.create('News__c', news_inst)

#         if result and 'id' in result:
#             obj['data'] = result['id']
#         else:
#             obj['isError'] = True
#             obj['message'] = "News creation failed"

#     except jwt.ExpiredSignatureError as err:
#         obj['isError'] = True
#         obj['message'] = str(err)
#     except Exception as err:
#         obj['isError'] = True
#         obj['message'] = str(err)

#     return jsonify(obj)

@app.route('/getWeather', methods=['GET'])
def get_weather():
    api_key = os.environ.get('WEATHER_API')
    city = '10.957008,78.608787'
    api_url = f'http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&days=1&aqi=no&alerts=yes&lang=ta'
    obj = {}

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        obj['error'] = False
        obj['data'] = response.json()
    except requests.exceptions.RequestException as error:
        obj['error'] = True
        obj['message'] = str(error)

    return jsonify(obj)

if __name__ == '__main__':
    app.run(debug=True)
