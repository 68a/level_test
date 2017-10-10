from flask_sqlalchemy import SQLAlchemy
import datetime
from passlib.hash import sha256_crypt

db = SQLAlchemy()

class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True

    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        """Define a base way to print models"""
        return '%s(%s)' % (self.__class__.__name__, {
            column: value
            for column, value in self._to_dict().items()
        })

    def json(self):
        """
                Define a base way to jsonify models, dealing with datetime objects
        """
        return {
            column: value if not isinstance(value, datetime.date) else value.strftime('%Y-%m-%d')
            for column, value in self._to_dict().items()
        }



class User(BaseModel, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))

    def __init__(self, username, password):
        self.username = username
        self.password = sha256_crypt.encrypt(password)

    def auth(username, password):
        print(username, password)
        data = User.query.filter_by(username=username).first()

        if data is not None:
            print("data password: %s password: %s" % (data.password, password))
            if sha256_crypt.verify(password, data.password):
                return True
            else:
                return False
        else:
            return False

    def checkUserExist(username):
        data = User.query.filter_by(username=username).first()
        if data is not None:
            return True
        else:
            return False
    
class UserTestLog(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String)
    test_type = db.Column(db.String)
    level_type = db.Column(db.String)
    test_time = db.Column(db.Datetime)
        

class Questions(BaseModel, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        question_sn = db.Column(db.String)
        question_text = db.Column(db.String)
        option_a = db.Column(db.String)
        option_b = db.Column(db.String)
        option_c = db.Column(db.String)
        option_d = db.Column(db.String)
        level_type = db.Column(db.String)


class FailureQuestions(BaseModel, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        question_sn = db.Column(db.String)
        failure_count = db.Column(db.Integer, default = 0)
        user_name = db.Column (db.String)                      
        level_type = db.Column(db.String)

class Papers (BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level_type = db.Column(db.String)
    user_name = db.Column (db.String)
    paper_sn = db.Column (db.String)
    paper_question_sn = db.Column (db.Integer)
    
    question_sn = db.Column (db.String)
    question_text = db.Column (db.String)
    question_a = db.Column (db.String)
    question_b = db.Column (db.String)
    question_c = db.Column (db.String)
    question_d = db.Column (db.String)
    question_right_option = db.Column (db.Integer)
    option_choice = db.Column (db.Integer)

class PaperTestResult (BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level_type = db.Column(db.String)
    user_id = db.Column (db.Integer)
    
    paper_sn = db.Column (db.Integer)
    paper_point = db.Column (db.Integer)
    
