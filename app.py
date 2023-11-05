import datetime
from flask import Flask, request, jsonify
import jwt
from salesforce import Salesforce
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'FLEKNNIRQSQ'
sf = Salesforce()

@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/getToken', methods=['POST'])
def get_token():
    data = request.json
    user_name = data.get('userName')
    pin = data.get('pin')
    if(data.get('isPaarai') == True):
        result = sf.query(f"SELECT Id,Paarai_Id__c,Name,Pin__c FROM Member__c WHERE UserName__c='{user_name}'")
    else:
        result = sf.query(f"SELECT Id,Member_Id__c,Name,Pin__c FROM Group_Member__c WHERE UserName__c='{user_name}'")
    obj = {}
    if result['records']:
        member = result['records'][0]
        if pin == member['PIN__c']:
            if(data.get('isPaarai') == True):
                payload = {
                    'memberId': member['Id'],
                    'paaraiId': member['Paarai_Id__c']
                }
            else:
                payload = {
                    'Id': member['Id'],
                    'memberId': member['Member_Id__c'],
                }
            obj['Name'] = member['Name']
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            obj['token'] = token
        else:
            obj['isError'] = True
            obj['message'] = 'Incorrect Pin'
    else:
        obj['isError'] = True
        obj['message'] = 'Incorrect username'
    return jsonify(obj)

@app.route('/getMemberInfo', methods=['POST'])
def get_member_info():
    data = request.json
    token = data.get('token')
    obj = {}
    obj['isError'] = False

    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if(data.get('isPaarai') == True):
            member_id = decoded['memberId']
            result = sf.query(f"SELECT Id, Name, Work__c, Location__c, Paarai_Id__c, PIN__c, Date_of_Birth__c, Is_Approved__c, Phone_Number__c, UserName__c, Position__c FROM Member__c WHERE Id = '{member_id}'")
        else:
            member_id = decoded['Id']
            result = sf.query(f"SELECT Id, Name, Aadhar_Number__c, Address__c, Joining_Date__c, Member_Id__c, Mobile__c, Username__c, Position__c FROM Group_Member__c WHERE Id = '{member_id}'")
        if result['records']:
            obj['data'] = result['records'][0]
        else:
            obj['isError'] = True
            obj['message'] = 'Member not found'
    except jwt.InvalidTokenError:
        obj['isError'] = True
        obj['message'] = 'Invalid token'
    
    return jsonify(obj)

@app.route('/getMemberList', methods=['POST'])
def get_member_list():
    data = request.json
    token = data.get('token')
    obj = {}
    obj['isError'] = False

    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if(data.get('isPaarai') == True):
            result = sf.query("SELECT Id, Name, Work__c, Paarai_Id__c, Phone_Number__c, UserName__c, Position__c, Location__c FROM Member__c WHERE Is_Approved__c = true ORDER BY Paarai_Id__c ASC")
        else:
            result = sf.query("SELECT Id, Name, Member_Id__c, Position__c FROM Group_Member__c ORDER BY Member_Id__c ASC")
        if result['records']:
            obj['data'] = result['records']
        else:
            obj['isError'] = True
            obj['message'] = 'No approved members found'
    except jwt.InvalidTokenError:
        obj['isError'] = True
        obj['message'] = 'Invalid token'

    return jsonify(obj)

@app.route('/getEventList', methods=['POST'])
def get_event_list():
    data = request.json
    token = data.get('token')
    obj = {}
    obj['isError'] = False

    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        query = ("SELECT Id, Name, Start_Date__c, End_Date__c, Member__r.Name, "
                 "(SELECT Name, Incharge__r.Name, Start_Time__c, Duration__c FROM Competitions__r) "
                 "FROM Event__c ORDER BY Start_Date__c DESC")
        result = sf.query(query)
        
        if result['records']:
            obj['data'] = result['records']
        else:
            obj['isError'] = True
            obj['message'] = 'No events found'
    except jwt.InvalidTokenError:
        obj['isError'] = True
        obj['message'] = 'Invalid token'

    return jsonify(obj)

@app.route('/getNews', methods=['POST'])
def get_news():
    token = request.json.get('token')
    obj = {'isError': False}
    try:
        decoded = jwt.decode(token, 'FLEKNNIRQSQ', algorithms=['HS256'])
        result = sf.query(
            "SELECT Id, Title__c, Description__c, Created_Date__c, Member__r.Name FROM News__c WHERE Is_Approved__c = true ORDER BY Created_Date__c DESC"
        )

        obj['data'] = result.get('records')
    except Exception as err:
        obj['isError'] = True
        obj['message'] = str(err)

    return jsonify(obj)

@app.route('/getTransaction', methods=['POST'])
def get_Transactions():
    token = request.json.get('token')
    obj = {'isError': False}
    try:
        decoded = jwt.decode(token, 'FLEKNNIRQSQ', algorithms=['HS256'])
        member_id = decoded['Id']
        result = sf.query(
            f"SELECT Id, Name, Type__c, Month__c, Date__c, Description__c, Amount__c, Group_Account__r.Total_Amount__c FROM Group_Transaction__c WHERE Group_Member__c = '{member_id}' AND Group_Account__r.Account_Type__c = 'Savings Account' ORDER BY CreatedDate DESC"
        )

        obj['data'] = result.get('records')
    except Exception as err:
        obj['isError'] = True
        obj['message'] = str(err)

    return jsonify(obj)


@app.route('/saveNews', methods=['POST'])
def save_news():
    token = request.json.get('token')
    obj = {'isError': False}

    try:
        decoded = jwt.decode(token, 'FLEKNNIRQSQ', algorithms=['HS256'])
        memberId = decoded['memberId']
        data = request.json.get('news')
        current_date = datetime.datetime.now().isoformat().split('T')[0]
        
        news_inst = {
            'Is_Approved__c': False,
            'Member__c': memberId,
            'Description__c': data['description'],
            'Created_Date__c': current_date,
            'Title__c': data['title'],
        }
        result = sf.create('News__c', news_inst)

        if result and 'id' in result:
            obj['data'] = result['id']
        else:
            obj['isError'] = True
            obj['message'] = "News creation failed"

    except jwt.ExpiredSignatureError as err:
        obj['isError'] = True
        obj['message'] = str(err)
    except Exception as err:
        obj['isError'] = True
        obj['message'] = str(err)

    return jsonify(obj)

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
