from functools import wraps
import json
from flask_mail import Message
from secrets import compare_digest
import requests, random, os
from flask import render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from devapp import app
from devapp.models import db, User, Level, Topic, Donate
from devapp.forms import DpForm
from devapp import mail

def get_user_by_id(uid):
    deets = db.session.query(User).get(uid)
    return deets


def login_required(func):
    @wraps(func)
    def check_login(*args, **kwargs):
        if session.get('useronline') is not None:
            return func(*args, **kwargs)
        else:
            flash('You must be logged to access this page.', 'error')
            return redirect('/login/')

    return check_login


@app.route('/')
def home():
    uid = session.get('useronline')
    userid = get_user_by_id(uid)
    topics = db.session.query(Topic).filter(Topic.topic_status=='1').all()
    try:
        response = requests.get('http://127.0.0.1:3000/api/v1/listall/')
        hotels = response.json()
    except:
        hotels = None
    return render_template("user/index.html", hotels=hotels, topics=topics, userid=userid)

@app.route('/dashboard/')
@login_required
def dashboard():
    uid = session.get('useronline')
    userid = get_user_by_id(uid)
    return render_template('user/dashboard.html', userid=userid)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('user/register.html')
    else:
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        password = request.form.get('pwd')
        hashed_value = generate_password_hash(password)
        user = User(user_fname=fname, user_lname=lname, user_email=email, user_password=hashed_value)
        db.session.add(user)
        db.session.commit()
        userid = user.user_id
        session['useronline'] = userid
        return redirect('/dashboard/')


@app.route('/login/', methods=['GET', 'POST'])
def user_login():
    if request.method == 'GET':
        return render_template('user/loginpage.html')
    else:
        email = request.form.get('email')
        password = request.form.get('pwd')
        if email == '' or compare_digest(password, ''):
            flash('Both fields are required', category='error')
            return redirect('/login/')
        else:
            user = db.session.query(User).filter(User.user_email == email).first()
            if user is not None:
                pw_hashed = user.user_password
                chk_pwd = check_password_hash(pw_hashed, password)
                if chk_pwd is True:
                    session['useronline'] = user.user_id
                    return redirect('/dashboard/')
                else:
                    flash("Invalid Password", "error")
            else:
                flash("Invalid Username", "error")
            return redirect('/login/')


@app.route('/profile/', methods=['GET', 'POST'])
@login_required
def profile():
    uid = session.get('useronline')
    userid = get_user_by_id(uid)
    levels = db.session.query(Level).all()
    if request.method == 'GET':
        return render_template('user/profile.html', userid=userid, levels=levels)
    else:
        # Retrieve data from the form
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        phone = request.form.get('phone')
        level = request.form.get('level')

        # Update the user data using ORM
        if level:
            user_det = db.session.query(User).get(uid)
            user_det.user_fname = fname
            user_det.user_lname = lname
            user_det.user_phone = phone
            user_det.user_levelid = level
            db.session.commit()
            flash('Profile Updated Successfully.', 'success')
        else:
            flash('Please select a category', 'error')
        return redirect('/profile/')


@app.route('/logout/')
def logout():
    if session.get('useronline'):
        session.pop('useronline')
    return redirect('/login/')


@app.route("/check/username/", methods=['GET', 'POST'])
def check_username():
    email = request.form.get('useremail')
    email_list = db.session.query(User).filter(User.user_email == email).first()
    if email_list:
        return f"<span class='text-success'>Email is available.</span>"
    else:
        return f"<span class='text-success'>Email is already registered.</span>"


@app.route('/changedp/', methods=['GET', 'POST'])
@login_required
def change_dp():
    uid = session.get('useronline')
    userid = get_user_by_id(uid)
    dpform = DpForm()
    if request.method == 'GET':
        return render_template('user/changedp.html', dpform=dpform, userid=userid)
    else:
        if dpform.validate_on_submit():
            fileobj = request.files.get('dp')
            actual_name = fileobj.filename

            # method 1
            ext = actual_name[-4:]
            # end of method 1

            # method 2
            # name, ext = os.path.splitext(actual_name)
            # end of method 2

            new_name = str(random.randint(1, 1000000000) + 1000000) + ext
            fileobj.save('devapp/static/uploads/'+new_name)
            userid.user_pix = new_name
            db.session.commit()

            flash("Profile picture successfully uploaded.")
            return redirect('/dashboard/')
        else:
            return render_template("user/changedp.html", dpform=dpform)


@app.route('/donation/', methods=['GET', 'POST'])
def donation():
    uid = session.get('useronline')
    userid = get_user_by_id(uid)
    if request.method == 'GET':
        topics = db.session.query(Topic).filter(Topic.topic_status=='1').all()
        return render_template('user/donations.html', topics=topics, userid=userid)
    else:
        fullname = request.form.get('fullname')
        amt = request.form.get('amt')
        email = request.form.get('email')
        
        if float(amt) > 0:
            
            # generate payment refrence
            ref = "DEV_"+ str(random.randint(1000, 7777777) + 23000)
            
            # create a session to keep track of the ongoing payment
            session['payref'] = ref
            
            don = Donate(donate_amt=amt, donate_userid=userid, donate_status='pending',
                         donate_donor=fullname, donate_email=email, donate_ref=ref)
            db.session.add(don)
            db.session.commit()
            return redirect(url_for('payconfirm'))
        else:
            flash("The amount must be more than 0 naira", 'error')
        return redirect(url_for('donation'))


# Consuming paystack api for payment ingeration
@app.route('/pay/landing/')
def payment_landig_page():
    ref = session.get('payref')
    paystackref = request.args.get('reference')
    if ref == paystackref:
        url = "https://api.paystack.co/transaction/verify/"+ref
        headers = headers = {"ContentType": "application/json",
                             "Authorization": "Bearer sk_test_a2d0c7ea61fb4871d77101b996cc58955eea4e40"}
        response = requests.get(url, headers=headers)
        response_json = response.json()
        don = Donate.query.filter(Donate.donate_ref==ref).first()
        
        if response_json['status'] is True:
            # ip = response_json['data']['ip_address']
            don.donate_status == 'paid'
        else:
            don.donate_status == 'failed'
        db.session.commit()
        return "Success"
        # return redirect(url_for('payment_report'))
    else:
        flash("Invalid reference", 'error')
    return "Thank you, your payment was successful."


@app.route('/payconfirm/', methods=['GET', 'POST'])
def payconfirm():
    """ This route fetches the details of the donation submitted by user so they can confrim if they want togo ahead or edit """
    ref = session.get('payref')
    if ref:
        donation_deets = Donate.query.filter(Donate.donate_ref==ref).first()
        return render_template('user/confirm.html', donation_deets=donation_deets)
    else:
        flash("Please complete the donation form", 'error')
        return redirect(url_for('donation'))
    
    
@app.route('/paystack/initialize', methods=['GET', 'POST'])
def paystack_initialize():
    ref = session.get('payref')
    if ref:
        paydeets = Donate.query.filter(Donate.donate_ref==ref).first()
        amount = paydeets.donate_amt * 100
        email = paydeets.donate_email
        callback_url = 'http://127.0.0.1:5000/pay/landing/'
        
        headers = {"ContentType": "application/json",
                   "Authorization": "Bearer sk_test_a2d0c7ea61fb4871d77101b996cc58955eea4e40"}
        url = "https://api.paystack.co/transaction/initialize"
        data = {"email": email, "amount": amount, "reference": ref, "callback_url": callback_url}
        
        try:
            response = requests.post(url, headers=headers,data=json.dumps(data))
            response_json = response.json()
            if response_json and response_json['status'] is True:
                checkoutpage = response_json['data']['authorization_url']
                return redirect(checkoutpage)
            else:
                flash(f"{response_json['message']}", 'error')
                return redirect(url_for('donation'))
        except:
            flash("We could not connect to paystack", 'error')
            return redirect(url_for('donation'))
    else:
        flash("Please complete the form", 'error')
        return "PASS"


@app.route('/reports/')
def payment_reports():
    return 'pass'


@app.route('/conversations/')
@login_required
def conversations():
    uid = session.get('useronline')
    userid = get_user_by_id(uid)
    return render_template('user/conversations.html', userid=userid)


@app.route('/sendmail/', methods=['GET', 'POST'])
@login_required
def sendmail():
    uid = session.get('useronline')
    userid = get_user_by_id(uid)
    
    email = request.form.get('email')
    message = request.form.get('message')
    
    sender = ('DevConfApp', 'admin@devconf.com')
    subject = "Thank you for your response"
    msg = Message(subject=subject, sender=sender, recipients=[email])
    msg.body = f"Thank you, your message was received as follows: {message}"
    mail.send(msg)
    return f"Thank you, {email}"
