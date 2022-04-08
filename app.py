from flask import *
from flask_restful import Api, Resource, reqparse, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime as dt
import hashlib, uuid

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

requestsParsed = reqparse.RequestParser()

user_fields = {
    'id': fields.Integer,
    'userName': fields.String,
    'email': fields.String,
#    'taskList': fields.Nested
}

taskList_fields = {
    'id': fields.Integer,
    'user': fields.Integer,
    'date': fields.DateTime,
    'note': fields.String,
#    'tasks': fields.Nested
}

Task_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'description': fields.String,
    'complete': fields.Boolean,
    'priority': fields.Boolean,
    'date': fields.String
}

class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    complete = db.Column(db.Boolean, nullable=False, default=False)
    priority= db.Column(db.Boolean, nullable=False, default=False)
    date = db.Column(db.DateTime, nullable = False, default = dt.utcnow)
    taskList = db.Column(db.Integer, db.ForeignKey("tasklist.id"), nullable=False)


class Tasklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.DateTime, nullable = False, default = dt.utcnow)
    note = db.Column(db.String(300), nullable=True)
    tasks = db.relationship('Tasks', backref='task', lazy = True)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(300), nullable=False)
    salt = db.Column(db.String(20), nullable=False)
    taskList = db.relationship('Tasklist', backref='taskList', lazy = True)


#need to create login and new user actions
class UserController(Resource):
    @marshal_with(user_fields)
    def get(self):
        requestsParsed.add_argument("userName", type=str, help="UserName is required to login")
        requestsParsed.add_argument("password", type=str, help="password is required to login")
        args = requestsParsed.parse_args()
        result = Users.query.filter_by(userName=args['userName']).first()
        password = hashlib.sha512((args['password'] + result.salt).encode('utf-8')).hexdigest()
        requestsParsed.remove_argument("userName")
        requestsParsed.remove_argument("password")
        if password != result.password:
            abort()


        return result, 200

    @marshal_with(user_fields)
    def post(self):
        requestsParsed.add_argument("userName", type=str, help="UserName is required to create account")
        requestsParsed.add_argument("password", type=str, help="password is required to create account")
        requestsParsed.add_argument("email", type=str, help="email is required to create account")
        args = requestsParsed.parse_args()
        newSalt = uuid.uuid4().hex
        hashed_password = hashlib.sha512((args['password'] + newSalt).encode('utf-8')).hexdigest()
        result = Users(userName=args['userName'], email=args['email'], password=hashed_password, salt= newSalt)
        db.session.add(result)
        db.session.commit()

        return result, 201

    @marshal_with(user_fields)
    def delete(self):
        requestsParsed.add_argument("userName", type=str, help="UserName is required to login")
        requestsParsed.add_argument("password", type=str, help="password is required to login")
        args = requestsParsed.parse_args()
        result = Users.query.filter_by(userName=args['userName']).first()
        db.session.delete(result)
        db.session.commit()
        requestsParsed.remove_argument("userName")
        requestsParsed.remove_argument("password")

        return result, 200

#need to create action to find tasklist by date for requesting user
class TaskListController(Resource):
    @marshal_with(taskList_fields)
    def get(self):
        requestsParsed.add_argument("userId", type=int, help="UserId is required to locate taskList")
        requestsParsed.add_argument("date", type=str, help="Date is required to locate taskList")
        args = requestsParsed.parse_args()
        dateconv = dt.strptime(args['date'], '%m-%d-%Y')
        result = Tasklist.query.filter_by(user=args['userId'], date=dateconv).first()

        requestsParsed.remove_argument("userId")
        requestsParsed.remove_argument("date")

        return result, 200

    @marshal_with(taskList_fields)
    def post(self):
        requestsParsed.add_argument("userId", type=int, help="UserId is required to add taskList")
        requestsParsed.add_argument("date", type=str, help="Date is required to add taskList")
        requestsParsed.add_argument("note", type=str, help="note is required to add taskList")
        args = requestsParsed.parse_args()
        dateconv = dt.strptime(args['date'], '%m-%d-%Y')
        result = Tasklist(user=args['userId'], date=dateconv, note=args['note'])
        db.session.add(result)
        db.session.commit()

        requestsParsed.remove_argument("userId")
        requestsParsed.remove_argument("date")
        requestsParsed.remove_argument("note")

        return result, 201

    @marshal_with(taskList_fields)
    def delete(self):
        requestsParsed.add_argument("userId", type=int, help="UserId is required to add taskList")
        requestsParsed.add_argument("date", type=str, help="Date is required to add taskList")

        args = requestsParsed.parse_args()

        dateconv = dt.strptime(args['date'], '%m-%d-%Y')
        result = Tasklist.query.filter_by(user=args['userId'], date=dateconv).first()
        db.session.delete(result)
        db.session.commit()

        requestsParsed.remove_argument("userId")
        requestsParsed.remove_argument("date")

        return result, 200

#need to create action for grabbing tasks for a given tasklist
class TaskController(Resource):
    @marshal_with(Task_fields)
    def get(self):
        requestsParsed.add_argument("tasklistId", type=int, help="tasklistId is required to add taskList")
        args = requestsParsed.parse_args()
        result = Tasks.query.filter_by(taskList=args['tasklistId']).all()
        requestsParsed.remove_argument("tasklistId")

        return result, 200

    @marshal_with(Task_fields)
    def post(self):
        requestsParsed.add_argument("title", type=str, help="title is required to add task")
        requestsParsed.add_argument("description", type=str, help="description is required to add task")
        requestsParsed.add_argument("priority", type=bool, help="priority is required to add taskList")
        requestsParsed.add_argument("tasklistId", type=int, help="tasklistId is required to add taskList")
        args = requestsParsed.parse_args()

        result = Tasks(title=args['title'], description=args['description'], priority=args['priority'], taskList=args['tasklistId'])

        db.session.add(result)
        db.session.commit()
        requestsParsed.remove_argument("title")
        requestsParsed.remove_argument("description")
        requestsParsed.remove_argument("priority")
        requestsParsed.remove_argument("tasklistId")

        return result, 201

    @marshal_with(Task_fields)
    def patch(self):
        requestsParsed.add_argument("taskId", type=int, help="taskId is required to add taskList")
        requestsParsed.add_argument("title", type=str, help="title is required to add task")
        requestsParsed.add_argument("description", type=str, help="description is required to add task")
        requestsParsed.add_argument("priority", type=bool, help="priority is required to add taskList")
        requestsParsed.add_argument("tasklistId", type=int, help="tasklistId is required to add taskList")
        requestsParsed.add_argument("complete", type=bool, help="complete is required to add taskList")
        requestsParsed.add_argument("date", type=str, help="date is required to add taskList")
        args = requestsParsed.parse_args()
        dateconv = dt.strptime(args['date'], '%m-%d-%Y')

        result = Tasks.query.filter_by(id=args['taskId']).first()

        result.title = args['title']
        result.description = args['description']
        result.priority = args['priority']
        result.taskList = args['tasklistId']
        result.complete = args['complete']
        result.date = dateconv
        db.session.add(result)
        db.session.commit()

        return result, 200

    @marshal_with(Task_fields)
    def delete(self):
        requestsParsed.add_argument("taskId", type=int, help="taskId is required to add taskList")
        args = requestsParsed.parse_args()
        result = Tasks.query.filter_by(id=args['taskId']).first()
        db.session.delete(result)
        db.session.commit()
        requestsParsed.remove_argument("taskId")

        return result, 200

api.add_resource(UserController, '/', '/user')
api.add_resource(TaskListController, '/', '/tasklist')
api.add_resource(TaskController, '/', '/task')

if __name__ == "__main__":
    app.run(debug=True)



#functions to change fonts, color, size

#reminders (nice to have not a most have

#get tasks by month, day and week

