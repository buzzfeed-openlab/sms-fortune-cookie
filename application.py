from flask import redirect, request, render_template, Response, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func
from functools import wraps
from sms_swap import create_app
from sms_swap.config import CONFIG_VARS
from sms_swap.models import Answer
from sms_swap.database import db
import twilio.twiml
from twilio.rest import TwilioRestClient


application = create_app()

@application.route("/")
def index():
    # TODO: grab some recordings to show
    return render_template('index.html')



@application.route("/respond", methods=['GET', 'POST'])
def respond():
    """Respond to incoming texts"""

    resp = twilio.twiml.Response()

    incoming_msg = request.values.get('Body', '')

    # this clears all cookies
    if(incoming_msg=='clear'):
        session['seen_intro'] = False
        session['seen_prompt'] = False
        session['gave_ans'] = False
        session['extra_msg'] = False
        resp.sms("erasing my memory of our conversation")
        return str(resp)


    # if exchange has been completed
    if session.get('extra_msg',False):
        session['extra_msg'] = False
        if incoming_msg.lower().startswith('y'):
            session['seen_prompt'] = False
            session['gave_ans'] = False
        elif incoming_msg.lower().startswith('n'):
            # TODO: ask for feedback?
            resp.sms('ok, later!')
            return str(resp)



    if not session.get('seen_prompt',False):
        if not session.get('seen_intro', False):
            resp.sms("hello, stranger! I'm a fortune cookie SMS bot.")
            session['seen_intro'] = True
        resp.sms("want a random fortune? reply by writing a fortune for someone else to crack open!")
        session['seen_prompt'] = True

    elif not session.get('gave_ans',False):
        # saving rec here
        if incoming_msg: # only if there is a msg
            new_rec = Answer(request.values.get('SmsSid'), request.values.get('From'), incoming_msg)
            db.session.add(new_rec)
            db.session.commit()

        # grabbing a fortune from a stranger
        # TODO: ensure that this is not a fortune from yourself
        random_ans = Answer.query.filter_by(is_approved=True).filter(Answer.from_number!=request.values.get('From')).order_by(func.rand()).first()

        resp.sms("excellent, I'll sneak that into someone else's fortune cookie. here's your fortune:")
        if random_ans:
            resp.sms(random_ans.answer_text.upper())

            if incoming_msg: # only if there is a msg
                random_ans.view_count = random_ans.view_count+1
                db.session.add(random_ans)
                db.session.commit()

                # alerting rec-giver when rec has been seen for the first time
                if random_ans.from_number and random_ans.view_count==1:
                    client = TwilioRestClient(
                                CONFIG_VARS['TWILIO_ACCOUNT_SID'],
                                CONFIG_VARS['TWILIO_AUTH_TOKEN']
                            )
                    msg = "your fortune (%s) was just delivered to a stranger!" %random_ans.answer_text
                    message = client.messages.create(
                                to=random_ans.from_number,
                                from_=CONFIG_VARS['TWILIO_PHONE_NO'],
                                body=msg
                            )
        else:
            resp.sms("404 FORTUNE NOT FOUND")

        session['gave_ans'] = True
    else:
        # TODO: a more elegant way of handling additional messages?
        session['extra_msg'] = True
        resp.sms("do you want to start over & exchange another fortune? \n(y/n)")


    return str(resp)


@application.route("/rollback", methods=['GET', 'POST'])
def rollback():
    # TODO: figure out what's going on???
    db.session.rollback()
    return redirect('/respond')


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == CONFIG_VARS['ADMIN_USER'] and password == CONFIG_VARS['ADMIN_PASS']

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your credentials for that url', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@application.route('/review')
@requires_auth
def review():
    review_queue = Answer.query.filter_by(is_approved=None).all()
    approved = Answer.query.filter_by(is_approved=True).all()
    return render_template('review.html', review_queue = review_queue, approved=approved)

@application.route('/reviewtrash')
@requires_auth
def reviewtrash():
    disapproved = Answer.query.filter_by(is_approved=False).all()
    return render_template('reviewtrash.html', disapproved=disapproved)


@application.route('/approve/<ans_id>')
@requires_auth
def approve(ans_id):
    ans = Answer.query.get(ans_id)
    ans.is_approved = True
    db.session.commit()
    return redirect('/review')

@application.route('/disapprove/<ans_id>')
@requires_auth
def disapprove(ans_id):
    ans = Answer.query.get(ans_id)
    ans.is_approved = False
    db.session.commit()
    return redirect('/review')


@application.route('/initialize')
@requires_auth
def initialize():
    # TODO: only do this if tables don't exist?
    db.create_all()
    return redirect('/')



if __name__ == "__main__":

    application.run(host='0.0.0.0')
