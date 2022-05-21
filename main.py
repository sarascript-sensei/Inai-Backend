import os
import pytz
import datetime

from flask import Flask, request, jsonify
from flask_restful import Api, Resource, reqparse, abort
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import flask
load_dotenv()

app = Flask(__name__)
api = Api(app)

app.config["MONGO_URI"] = 'mongodb://localhost:27017/inaiApp'
app.config["MONGO_DBNAME"] = 'inaiApp'

mongo = PyMongo(app)

user_put_args = reqparse.RequestParser()
user_put_args.add_argument('name', type=str)
user_put_args.add_argument('email', type=str)
user_put_args.add_argument('studentId', type=str)
user_put_args.add_argument('id', type=str)

event_put_args = reqparse.RequestParser()
event_put_args.add_argument('title', type=str)
event_put_args.add_argument('date', type=str)
event_put_args.add_argument('startTime', type=str)
event_put_args.add_argument('endTime', type=str)
event_put_args.add_argument('location', type=str)
event_put_args.add_argument('description', type=str)
event_put_args.add_argument('telegram', type=str)
event_put_args.add_argument('id', type=str)
event_put_args.add_argument('creatorId', type=str)
event_put_args.add_argument('type', type=str)
event_put_args.add_argument('imageUrl', type=str)

event_user_put_args = reqparse.RequestParser()
event_user_put_args.add_argument('event_id', type=str)
event_user_put_args.add_argument('user_id', type=str)
event_user_put_args.add_argument('sign_up', type=bool)


def pad_zero(digit):
    return '0' if len(digit) == 1 else ''

def format_date_time(event):
    event['date'] = str(event['date'][2]) + '-' + pad_zero(str(event['date'][1])) + str(event['date'][1]) + '-' + pad_zero(str(event['date'][0])) + str(event['date'][0])
    event['startTime'] = pad_zero(str(event['startTime'][0])) + str(event['startTime'][0]) + ':' + pad_zero(str(event['startTime'][1])) + str(event['startTime'][1])
    event['endTime'] = pad_zero(str(event['endTime'][0])) + str(event['endTime'][0]) + ':' + pad_zero(str(event['endTime'][1])) + str(event['endTime'][1])

    return event

class User(Resource):
    def post(self):
        args = user_put_args.parse_args()
        if len(list(mongo.db.user.find({'studentId': args['studentId']}))) == 0:
            args['events'] = []
            organisers_f = open(f'{os.path.dirname(os.path.abspath(__file__))}/organisers.txt', 'r')
            organisers = [l.strip() for l in organisers_f.readlines()]
            args['permission'] = 0

            if args['studentId'] in organisers:
                args['permission'] = 1
                args['organisedEvents'] = []

            result = mongo.db.user.insert_one(args)
            print(result.inserted_id)
            return {'id': str(result.inserted_id), 'permission': args['permission']}

    def put(self):
        args = user_put_args.parse_args()
        mongo.db.user.update_one({'_id': ObjectId(args['id'])}, {'$set': {'email': args['email'], 'name': args['name'], 'studentId': args['studentId']}})

        return {'success': True}

    def get(self):

        email = request.args.get('email')
        user = mongo.db.user.find_one({'email': email})
        if user != None:
            user['id'] = str(user['_id'])
            del user['_id']

            user['events'] = [str(e) for e in user['events']]
            if 'organisedEvents' in user.keys():
                user['organisedEvents'] = [str(e) for e in user['organisedEvents']]

        return user
@app.route("/add_one")
def add_one():
    mongo.db.event.insert_one({'name': "sara", 'email': "sara@mail.ru"})
    return flask.jsonify(message="success")
@app.route("/")
def index():
    return flask.jsonify(message="ok")
class Event(Resource):
    def post(self):
        args = event_put_args.parse_args()
        args['date'] = [int(d) for d in args['date'].split('-')[::-1]]
        args['startTime'] = [int(st) for st in args['startTime'].split(':')]
        args['endTime'] = [int(et) for et in args['endTime'].split(':')]
        if len(list(mongo.db.event.find({'title': args['title'], 'date': args['date'], 'creatorId': args['creatorId']}))) == 0:
            args['attendees'] = []
            result = mongo.db.event.insert_one(args)
            mongo.db.user.update_one({'_id': ObjectId(args['creatorId'])}, {'$push': {'organisedEvents': result.inserted_id}})

            print(str(result.inserted_id))
            return {'id': str(result.inserted_id)}

    def put(self):
        args = event_user_put_args.parse_args()
        operation = "$pull"
        if args['sign_up']:
            operation = "$addToSet"
        
        mongo.db.user.update_one({'_id': ObjectId(args['user_id'])}, {operation: {'events': ObjectId(args['event_id'])}})
        mongo.db.event.update_one({'_id': ObjectId(args['event_id'])}, {operation: {'attendees': ObjectId(args['user_id'])}})
        
        print(args['event_id'])
        print(args['user_id'])

        return {'success': True}

    def get(self):
        event_id = request.args.get('event_id')
        user_id = request.args.get('user_id')
        event = mongo.db.event.find_one({'_id': ObjectId(event_id)})
        if event != None:
            event['id'] = str(event['_id'])            

            event['clashString'] = ''
            event['attendees'] = [str(a) for a in event['attendees']]
            event['creatorId'] = str(event['creatorId'])
            event_start_time = datetime.datetime(event['date'][2], event['date'][1], event['date'][0], event['startTime'][0], event['startTime'][1])
            event_end_time = datetime.datetime(event['date'][2], event['date'][1], event['date'][0], event['endTime'][0], event['endTime'][1])
        
            user = mongo.db.user.find_one({'_id': ObjectId(user_id)})
            print(event_start_time)
            print(event_end_time)
            print('====================')
            for ev in mongo.db.event.find({'_id' : {'$in':user['events'], '$ne': event['_id']}}):
                cur_ev_start_time = datetime.datetime(ev['date'][2], ev['date'][1], ev['date'][0], ev['startTime'][0], ev['startTime'][1])
                cur_ev_end_time = datetime.datetime(ev['date'][2], ev['date'][1], ev['date'][0], ev['endTime'][0], ev['endTime'][1])
                
                print(cur_ev_start_time)
                print(cur_ev_end_time)
                if event['date'] == ev['date'] and ((cur_ev_start_time <= event_start_time and event_start_time <= cur_ev_end_time) or event['date'] == ev['date'] and (cur_ev_start_time <= event_end_time and cur_ev_end_time >= event_end_time)):
                    suffix = 'st' if cur_ev_end_time.day == 1 else 'nd' if cur_ev_end_time.day == 2 else 'rd' if cur_ev_end_time.day == 3 else 'th'
                    event['clashString'] = f'You have "{ev["title"]}" from {cur_ev_start_time.strftime("%#I.%M%p")} to {cur_ev_end_time.strftime("%#I.%M%p")} on {cur_ev_start_time.strftime("%b %#d")}{suffix}'
                    break
                    

            del event['_id']
            event = format_date_time(event)

        # print(event)
        return event

class Events(Resource):
    def get(self):
        upcoming_events = []
        current_date = datetime.datetime.now(pytz.timezone('Asia/Singapore'))
        for event in mongo.db.event.find({}, {'_id': 1, 'imageUrl': 1, 'title': 1, 'date': 1, 'startTime': 1, 'endTime': 1, 'type': 1}):
            event_date = datetime.datetime(event['date'][2], event['date'][1], event['date'][0], event['startTime'][0], event['startTime'][1])
            event_date = event_date.astimezone(pytz.timezone('Asia/Singapore'))
            event['id'] = str(event['_id'])
            del event['_id']
            if event_date >= current_date: 
                event = format_date_time(event)
                upcoming_events.append(event)

        return upcoming_events

class Calendar(Resource):
    def get(self):
        user_id = request.args.get("user_id")
        start_date = [int(d) for d in request.args.get("start_date").split('-')]
        start_date = datetime.date(start_date[0], start_date[1], start_date[2])

        end_date = [int(d) for d in request.args.get("end_date").split('-')]
        end_date = datetime.date(end_date[0], end_date[1], end_date[2])

        user = mongo.db.user.find_one({'_id': ObjectId(user_id)})
        events = []

        for ev in mongo.db.event.find({'_id': {'$in': user['events']}}):
            event_date = datetime.date(ev['date'][2], ev['date'][1], ev['date'][0])

            if event_date >= start_date and event_date <= end_date:
                ev['creatorId'] = str(ev['creatorId'])
                ev['id'] = str(ev['_id'])
                del ev['_id']
                ev = format_date_time(ev)
                ev['attendees'] = [str(a) for a in ev['attendees']]

                events.append(ev)
                print(ev)

        return events

class Organised(Resource):
    def get(self):
        user_id = request.args.get("user_id")
        user = mongo.db.user.find_one({'_id': ObjectId(user_id), 'permission': 1})
        events = []
        current_date = datetime.datetime.now(pytz.timezone('Asia/Singapore'))

        if user == None:
            return;
        
        if user['permission'] == 1:
            for ev in mongo.db.event.find({'_id': {'$in': user['organisedEvents']}}):
                event_date = datetime.datetime(ev['date'][2], ev['date'][1], ev['date'][0], ev['startTime'][0], ev['startTime'][1])
                event_date = event_date.astimezone(pytz.timezone('Asia/Singapore'))
                ev['id'] = str(ev['_id'])
                del ev['_id']
                ev['creatorId'] = str(ev['creatorId'])
                if event_date >= current_date: 
                    ev = format_date_time(ev)
                    ev['attendees'] = [str(a) for a in ev['attendees']]
                    events.append(ev)
                    
        print(events)
        return events


class Participants(Resource):
    def get(self):
        event_id = request.args.get("event_id")
        event = mongo.db.event.find_one({"_id": ObjectId(event_id)})
        print(event_id)
        users = []

        for usr in mongo.db.user.find({'_id': {'$in': event['attendees']}}, {'organisedEvents': 0}):
            usr['id'] = str(usr['_id'])
            del usr['_id']

            usr['events'] = [str(ev) for ev in usr['events']]

            users.append(usr)

        print(users)

        return users

class Populate(Resource):
    def get(self):
        users = mongo.db.user.find({})
        events = mongo.db.event.find({})

        for user in users:
            if 'events' in user.keys() and len(user['events']) < 4:
                mongo.db.user.update_one({'_id': user['_id']}, {'$set': {'events': [events[0]['_id'], events[3]['_id'], events[2]['_id']]}})
                events[0]['attendees'].append(user['_id'])
                events[2]['attendees'].append(user['_id'])
                events[3]['attendees'].append(user['_id'])

        mongo.db.event.update_one({'_id': events[0]['_id']}, {'$set': {'attendees': events[0]['attendees']}})
        mongo.db.event.update_one({'_id': events[2]['_id']}, {'$set': {'attendees': events[1]['attendees']}})
        mongo.db.event.update_one({'_id': events[3]['_id']}, {'$set': {'attendees': events[2]['attendees']}})

class Creatorinfo(Resource):
    def get(self):
        creator_id = request.args.get('user_id')
        creator = mongo.db.user.find_one({'_id': ObjectId(creator_id)}, {'events': 0, 'organisedEvents': 0})
        creator['id'] = str(creator['_id'])
        del creator['_id']
        return(creator)


api.add_resource(User, '/user', endpoint='user')
api.add_resource(Event, '/event')
api.add_resource(Events, '/events')
api.add_resource(Calendar, '/calendar')
api.add_resource(Organised, '/organised')
api.add_resource(Participants, '/participants')
api.add_resource(Populate, '/populate')
api.add_resource(Creatorinfo, '/creatorinfo')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)