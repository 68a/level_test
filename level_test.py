# -*- coding: utf-8 -*-


"""Flask Login Example and instagram fallowing find"""

from flask import Flask, url_for, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from wtforms import Form, BooleanField, StringField, PasswordField, validators, TextField, HiddenField, TextAreaField
from wtforms.validators import Required, EqualTo, Optional, Length, Email
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
import os
from models import *
import uuid
from frontend import frontend


application = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
#db = SQLAlchemy(app)

application.config.from_object(os.environ['APP_SETTINGS'])
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap(application)
nav = Nav()

nav.init_app(application)
@nav.navigation()
def mynavbar():
    return Navbar(
        'BD7MMF',
        View('主页', 'home'),
        View('考试题库', 'testing'),
        View('模拟考试', 'testing'),
        View('杂七杂八', 'login'),
        View('请先登录', 'login'),
    )

        
@application.route('/', methods=['GET', 'POST'])
def home():
    """ Session control"""

    if not session.get('logged_in'):

        return render_template('index.html' )
    else:
        if request.method == 'POST':
            username = getname(request.form['username'])
            return render_template('index.html', data=getfollowedby(username))
        return render_template('index.html')



@application.route('/login', methods=['GET', 'POST'])
def login():
	"""Login Form"""
	if request.method == 'GET':
		return render_template('login.html')
	else:
		name = request.form['username']
		passw = request.form['password']
		try:
			data = User.query.filter_by(username=name, password=passw).first()
			if data is not None:
                            session['logged_in'] = True
                            session['username'] = name
                            return redirect(url_for('home'))
			else:
				return 'Dont Login'
		except:
			return "Dont Login"

@application.route('/register/', methods=['GET', 'POST'])
def register():
	"""Register Form"""
	if request.method == 'POST':
		new_user = User(username=request.form['username'], password=request.form['password'])
		db.session.add(new_user)
		db.session.commit()
		return render_template('login.html')
	return render_template('register.html')

@application.route("/logout")
def logout():
	"""Logout Form"""
	session['logged_in'] = False
	return redirect(url_for('home'))

class QuestionForm(Form):
        question_text = StringField('question_text')
        
@application.route("/testing")
def testing():
        """ Session control"""
        if not session.get('logged_in'):
                return render_template('index.html')
        else:
            return render_template('choose_testing.html')

@application.route("/testing_sheet")
def testing_sheet():
        """ Session control"""
        if not session.get('logged_in'):
                return render_template('index.html')
        else:
                questionForm = QuestionForm()
                q = Questions.query.get(1)
                questionForm.question_text = q.question_text
        return render_template('testing.html', questionForm=questionForm)

@application.route("/handle_testing_type", methods=['GET', 'POST'])
def handle_testing_type():
    testing_type = request.form.get('testing_type')
    print('testing_type=', testing_type)
    return render_template('handle_testing_type.html')


@application.route("/go_next_question", methods=['GET', 'POST'])
def go_next_question(): 
    action_type = request.form.get('submit')
    paper_sn = session['paper_sn']
    paper_question_sn = session['current_question_sn']
    question_count = Papers.query.filter(Papers.paper_sn == paper_sn).count()
    if paper_question_sn >= question_count:
        return redirect(url_for('confirm_paper'))

    print('action_type=', action_type)
    if action_type == 'confirm':
        return redirect(url_for('confirm_paper'))
    elif action_type == 'next':
        option_a = request.form.get('option1')
        option_b = request.form.get('option2')
        option_c = request.form.get('option3')
        option_d = request.form.get('option4')
        print('option_a=', option_a)
        if option_a == 'a':
            option_choice = 0
        elif option_a == 'b':
            option_choice = 1
        elif option_a == 'c':
            option_choice = 2
        elif option_a == 'd':
            option_choice = 3
        else:
            option_choice = -1
    

        paper = Papers.query.filter((Papers.paper_sn == paper_sn) & (Papers.paper_question_sn == paper_question_sn)).first()
        paper.option_choice = option_choice
        db.session.commit()

        session['current_question_sn'] += 1
        return redirect(url_for('go_next_question'))
    else:

        paper_sn = session['paper_sn']

        paper_question_sn = session['current_question_sn']
        print("paper_sn=", paper_sn)
        print("question_sn=", paper_question_sn)
        query = Papers.query.filter((Papers.paper_sn == paper_sn) & (Papers.paper_question_sn == paper_question_sn)).first()
        question_sn = query.question_sn
        question_text = query.question_text
        question_a = query.question_a
        question_b = query.question_b
        question_c = query.question_c
        question_d = query.question_d

        return render_template('go_next_question.html',
                               paper_question_sn = paper_question_sn + 1, 
                               question_sn = question_sn,
                               question_text = question_text,
                               question_a = question_a,
                               question_b = question_b,
                               question_c = question_c,
                               question_d = question_d,


        )
@application.route("/confirm_paper", methods=['GET', 'POST'])
def confirm_paper():
    paper_sn = session['paper_sn']

    print("paper_sn=", paper_sn)
    total_questions = Papers.query.filter(Papers.paper_sn == paper_sn).count()
                                                  
    answered_questions = Papers.query.filter((Papers.paper_sn == paper_sn) &(Papers.option_choice != None)).count()
    
    paper = Papers.query.filter((Papers.paper_sn == paper_sn ) &
                                (Papers.question_right_option != Papers.option_choice)).order_by(Papers.paper_sn)

    
    wrong_answers = paper.count()
    
    correct_answers = answered_questions - wrong_answers
    correct_rate = "%.1f" % (float(correct_answers) / total_questions * 100.0)
    
    result_dict = [u.__dict__ for u in paper]
    paper_result = []

    for x in result_dict:
        failure_question = FailureQuestions()
        failure_question.question_sn = x['question_sn']
        failure_question.user_name = session['username']
        q = FailureQuestions.query.filter((FailureQuestions.question_sn == x['question_sn']) & (FailureQuestions.user_name == session['username']) ).first()
        if q:
            q.failure_count += 1
        else:
            failure_question.failure_count = 1
            db.session.add(failure_question)
            
            

        if x['question_right_option'] == 0:
            x['right_option'] = 'A'
        elif x['question_right_option'] == 1:
            x['right_option'] = 'B'
        elif x['question_right_option'] == 2:
            x['right_option'] = 'C'
        elif x['question_right_option'] == 3:
            x['right_option'] = 'D'
        if x['option_choice'] == 0:
            x['answer'] = 'A'
        elif x['option_choice'] == 1:
            x['answer'] = 'B'
        elif x['option_choice'] == 2:
            x['answer'] = 'C'
        elif x['option_choice'] == 3:
            x['answer'] = 'D'

        paper_result.append(x)
        
    db.session.commit()            
    return render_template('confirm_paper.html',
                           total_questions = total_questions,
                           answered_questions = answered_questions,
                           wrong_answers = wrong_answers,
                           correct_answers = correct_answers,
                           correct_rate = correct_rate,
                           paper = paper_result)
    
@application.route("/show_seq_test", methods=['GET', 'POST'])
def show_seq_test():
    begin_sn = int (request.form ['testing_begin_sn']) - 1
    question_count = int (request.form ['testing_question_count'])
    session['current_question_sn'] = 0
    username = session['username']
    Papers.query.filter(Papers.user_name == username).delete()
    db.session.commit()
    sn = createPaperSeq(username, begin_sn, question_count)
    session['paper_sn'] = sn
    query = Papers.query.filter(Papers.paper_sn == sn).first()
    question_sn = query.question_sn
    question_text = query.question_text
    question_a = query.question_a
    question_b = query.question_b
    question_c = query.question_c
    question_d = query.question_d
    right_option = int(query.question_right_option) + 1
    return render_template('go_next_question.html',
                           paper_question_sn = 1,
                           question_sn = question_sn,
                           question_text = question_text,
                           question_a = question_a,
                           question_b = question_b,
                           question_c = question_c,
                           question_d = question_d,
    )


@application.route("/handle_random_test", methods=['GET', 'POST'])
def handle_random_test():
    return redirect(url_for('testting_sheet'))

#
# in:
# question_options = [ question_a, question_b, question_c, question_d ]
# index_list = [ 2, 0, 1 3]
# i = 0
# for x in index_list:
#   q_o[i] = qustion_options[x]
#   i = i + 1
# right_option = index_list.index(0)
#
#
from random import shuffle
def shuffler_option(question_options):
    option_count = 4
    index_list = [i for i in range(option_count)]
    shuffle(index_list)

    q_o = []
    for x in index_list:
        q_o.append(question_options[x])

    right_option = index_list.index(0)
    return q_o, right_option

def getQuestionTextBySn(question_sn):
    query = Questions.query.filter(Questions.question_sn == question_sn).first ()
    return query.question_text

def getSnStr(sn):
    zero_str = ''
    if sn < 10:
        zero_str = '00'
    elif sn >= 10 and sn <= 100:
        zero_str = '0'
    
    sn_str = 'LK0' + zero_str + str (sn)
    return sn_str

def createPaperSeq (username, begin_sn, question_count):
    paper_sn = str (uuid.uuid1 ())
    paper_question_sn = 0

    start_sn_str = getSnStr(begin_sn)

    query = Questions.query.filter (Questions.question_sn > start_sn_str).order_by (Questions.question_sn).limit(question_count)

    l = [u.__dict__ for u in query ]
    for x in l:
        question_options = []
        question_options.append(x['option_a'])
        question_options.append(x['option_b'])
        question_options.append(x['option_c'])
        question_options.append(x['option_d'])

        
        question_options, right_option = shuffler_option (question_options)
        paper = Papers()
        paper.paper_sn = paper_sn
        paper.question_sn = x ['question_sn']
        paper.question_text = getQuestionTextBySn (paper.question_sn)
        paper.question_a = question_options [0]
        paper.question_b = question_options [1]
        paper.question_c = question_options [2]
        paper.question_d = question_options [3]
        paper.question_right_option = right_option
        paper.paper_question_sn = paper_question_sn
        paper_question_sn = paper_question_sn + 1
        paper.user_name = username
        
        db.session.add(paper)
    db.session.commit()
    return paper_sn
        
db.init_app(application)    
if __name__ == '__main__':
    application.run(host='0.0.0.0')

        


        
