# -*- coding: utf-8 -*-


"""Flask Login Example and instagram fallowing find"""

from flask import Flask, url_for, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from flask_nav import Nav
from flask_nav.elements import Navbar, View
from wtforms import  BooleanField, StringField, PasswordField, validators, TextField, HiddenField, TextAreaField, validators as v

from flask_login import LoginManager, login_user, logout_user, current_user, login_required
import os
from models import *
import uuid
from wtforms.ext.i18n.form import Form
from sqlalchemy import text


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 7200
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 120
Bootstrap(app)
nav = Nav()

nav.init_app(app)
@nav.navigation()
def mynavbar():
    return Navbar(
        'BD7MMF',
        View('主页', 'home'),
        View('模拟考试', 'testing'),

    )

        
@app.route('/', methods=['GET', 'POST'])
def home():
    """ Session control"""
    user_name = session.get('username')
    if not session.get('logged_in'):

        print('user name', user_name)
        return render_template('index.html', user_name = user_name)
    else:
        if request.method == 'POST':
            username = getname(request.form['username'])
            return render_template('index.html', data=getfollowedby(username))
        return render_template('index.html', user_name = user_name)
    
class BaseForm(Form):
    LANGUAGES = ['zh']

class LoginForm(BaseForm):
    username = TextField('用户名', [validators.Length(min=3, max=20)])
    password = PasswordField('密码', [
        validators.Required()
        ])


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    
    if request.method == 'POST' and form.validate():

        name = request.form['username']
        passw = request.form['password']
        print("username：%s Pass: %s" % (name,passw))
        if User.checkUserExist(form.username.data) is False:
                flash('用户名不存在!', 'danger');
                return redirect(url_for('login'))

        if User.auth(name, passw):
            session['logged_in'] = True
            session['username'] = name
            return redirect(url_for('home'))
        else:
            flash('登录失败!', 'danger');
            return redirect(url_for('login'))
            
    return render_template('login.html', form=form)

class RegistrationForm(BaseForm):
    username = TextField('用户名', validators=[v.Length(min=3, max=20)])
    password = PasswordField('密码', validators=[
        v.Required(),
        v.EqualTo('confirm', message='密码不匹配')
    ])
    confirm = PasswordField('确认密码')

    

@app.route('/register', methods=['GET', 'POST'])
def register():
        form = RegistrationForm(request.form)
        if request.method == 'POST' and form.validate():
            if User.checkUserExist(form.username.data):
                flash('用户名已存在!', 'danger');
                return redirect(url_for('login'))
            user = User(form.username.data, 
                    form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('感谢注册！', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', form=form)
    
@app.route("/logout")
def logout():
	session['logged_in'] = False
	return redirect(url_for('home'))

class QuestionForm(Form):
        question_text = StringField('question_text')
        
@app.route("/testing")
def testing():
        if not session.get('logged_in'):
                return render_template('index.html')
        else:
            return render_template('select_level.html')

@app.route("/select_level", methods=['GET', 'POST'])
def select_level():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        testing_level = request.form.get('testing_level')
        if testing_level is not None:
            print('testing_level=', testing_level)
            if testing_level == 'option1':
                session['testing_level'] = 'A'
                return render_template('choose_testing.html', data = "A类题库")
            else:
                session['testing_level'] = 'B'
                return render_template('choose_testing.html', data = "B类题库")
        return render_template('select_testing.html')

@app.route("/testing_sheet")
def testing_sheet():
        if not session.get('logged_in'):
                return render_template('index.html')
        else:
                questionForm = QuestionForm()
                q = Questions.query.get(1)
                questionForm.question_text = q.question_text
        return render_template('testing.html', questionForm=questionForm)


@app.route("/handle_testing_type", methods=['GET', 'POST'])
def handle_testing_type():
    testing_type = request.form.get('testing_type')
    print('testing_type=', testing_type)

    if testing_type == 'option1':

        return render_template('handle_testing_seq.html', data = session["testing_level"] + "类题库")
    else:
        return render_template('select_random_testing.html')


    
@app.route("/go_next_question", methods=['GET', 'POST'])
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
        print("paper_question_sn=", paper_question_sn)
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
@app.route("/confirm_paper", methods=['GET', 'POST'])
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
    
@app.route("/show_seq_test", methods=['GET', 'POST'])
def show_seq_test():
    begin_sn = int (request.form ['testing_begin_sn']) - 1
    question_count = int (request.form ['testing_question_count'])
    session['current_question_sn'] = 0
    username = session['username']
    Papers.query.filter(Papers.user_name == username).delete()
    db.session.commit()
    testing_level = session['testing_level']
    sn = createPaperSeq(username, begin_sn, question_count, testing_level)
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


@app.route("/handle_random_test", methods=['GET', 'POST'])
def handle_random_test():
    username = session['username']
    testing_level = session['testing_level']
    session['current_question_sn'] = 0
    username = session['username']

    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        question_count = int(request.form.get('testing_question_count'))
        
        if question_count is not None:
            session['current_question_sn'] = 0
            username = session['username']
            Papers.query.filter(Papers.user_name == username).delete()
            db.session.commit()

            sn =  createPaperRandom(username, testing_level, question_count)
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
        return render_template('select_random_testing.html')

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

def createPaperRandom(username, testing_level, question_count):
    paper_sn = str (uuid.uuid1 ())
    paper_question_sn = 0
    
    sql = text("select question_sn from questions where level_type = '%s'" % testing_level)
    result = db.engine.execute(sql)
    data = []
    for row in result:
        print(row)
        data.append(row)
    shuffle(data)

    for row in data[0:question_count]:
        question_sn = row[0]   
        sql = text("select option_a, option_b, option_c, option_d from questions where level_type = '%s' and question_sn = '%s'" % ( testing_level, question_sn))
        x = db.engine.execute(sql)
        d = []
        for r in x:
            d.append(r)
        
        question_options = []
        question_options.append(d[0][0])
        question_options.append(d[0][1])
        question_options.append(d[0][2])
        question_options.append(d[0][3])
        question_options, right_option = shuffler_option (question_options)
        paper = Papers()
        paper.paper_sn = paper_sn
        paper.question_sn = question_sn
        paper.question_text = getQuestionTextBySn (paper.question_sn)
        paper.question_a = question_options [0]
        paper.question_b = question_options [1]
        paper.question_c = question_options [2]
        paper.question_d = question_options [3]
        paper.question_right_option = right_option
        paper.paper_question_sn = paper_question_sn
        paper_question_sn += 1
        paper.user_name = username
        db.session.add(paper)

    db.session.commit()
    return paper_sn


def createPaperSeq (username, begin_sn, question_count, testing_level):
    paper_sn = str (uuid.uuid1 ())
    start_sn_str = getSnStr(begin_sn)
    paper_question_sn = 0

    query = Questions.query.filter ((Questions.question_sn > start_sn_str) & (Questions.level_type == testing_level)).order_by (Questions.question_sn).limit(question_count)

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

def before_request():
    app.jinja_env.cache = {}
        
db.init_app(app)

app.before_request(before_request)
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
if __name__ == '__main__':
    app.run(host='0.0.0.0')

        


        
