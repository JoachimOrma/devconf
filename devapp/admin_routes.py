import os
from secrets import compare_digest, token_hex
from functools import wraps
from flask import render_template, request, flash, redirect, session, url_for
from werkzeug.security import check_password_hash
from devapp import app
from devapp.models import db, Admin, Level, Topic, User


def get_user_by_id(uid):
    deets = db.session.query(Admin).get(uid)
    return deets


def login_required(func):
    @wraps(func)
    def check_login(*args, **kwargs):
        if session.get('adminonline') is not None:
            return func(*args, **kwargs)
        else:
            flash('You must be logged to access this page.', 'error')
            return redirect('/login/')

    return check_login


@app.route('/admin/', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET':
        return render_template('admin/login.html/')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        if email == '' or compare_digest(password, ''):
            flash("Email and password are required", 'error')
            return redirect('/admin/')
        else:
            adm = db.session.query(Admin).filter(Admin.admin_username == email).first()
            if adm is not None:
                pw_hashed = adm.admin_pwd
                chk_pwd = check_password_hash(pw_hashed, password)
                if chk_pwd is True:
                    session['adminonline'] = adm.admin_id
                    return redirect('/admin/dashboard/')
                else:
                    flash("Invalid password!", 'error')
            else:
                flash("Invalid email!", 'error')
            return redirect(url_for('admin'))


@app.route('/admin/dashboard/')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html/')


@app.route('/admin/users/')
@login_required
def users():
    users = db.session.query(User).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/breakout/')
@login_required
def breakout():
    topics = db.session.query(Topic).all()
    return render_template('admin/breakout.html', topics=topics)


@app.route('/admin/addtopic/', methods=['GET', 'POST'])
@login_required
def add_topic():
    if request.method == 'GET':
        levels = db.session.query(Level).all()
        return render_template('admin/addtopic.html', levels=levels)
    else:
        title = request.form.get('title')
        level = request.form.get('level')
        status = request.form.get('status')

        # retrieving the file
        cover = request.files.get('topicCover')
        if cover and title:
            actual_name = cover.filename
            allowed = ['jpg', 'jpeg', 'png']

            file_deets = actual_name.split('.')
            ext = file_deets[-1]
            if ext in allowed:
                newname = token_hex(16) + '.' + ext
                cover.save('devapp/static/topics/' + newname)
                topic = Topic(topic_title=title, topic_image=newname, topic_status=status, topic_levelid=level)
                db.session.add(topic)
                db.session.commit()
                flash("Topic created successfully.", 'success')
                return redirect('/admin/breakout/')
            else:
                flash("File extension is not allowed.", 'error')
                return redirect('/admin/addtopic/')
        else:
            flash("Please select a file for upload and ensure you provide a title.", 'error')
            return redirect(url_for('add_topic'))


@app.route('/admin/edit/<int:id>/')
@login_required
def edit_topic(id):
    topic = db.session.query(Topic).filter(Topic.topic_id == id).first()
    levels = db.session.query(Level).all()
    if topic:
        return render_template('admin/topic_details.html', topic=topic, levels=levels, id=id)
    else:
        return redirect(url_for('edit_topic'))


@app.route('/admin/update-topic/', methods=['POST'])
@login_required
def update_topic():
    title = request.form.get("title")
    level = request.form.get("level")
    status = request.form.get("status")
    topicid = request.form.get("topicid")

    topic = db.session.query(Topic).get(topicid)
    topic.topic_title = title
    topic.topic_levelid = level
    topic.topic_status = status
    db.session.commit()
    flash(f"Topic {title} has been updated!", 'success')
    return redirect(url_for('breakout'))

# It is necessary to update the status of items when the user click on delete,
# instead of actually deleting it from the database.


@app.route('/admin/delete/<int:id>/')
@login_required
def delete(id):
    topic = db.session.query(Topic).get_or_404(id)
    actual_image = topic.topic_image
    db.session.delete(topic)
    db.session.commit()

    # Delete the file from the folder
    os.remove(f"devapp/static/topics/{actual_image}")

    flash("Topic deleted successfully.", 'success')
    return redirect(url_for('breakout'))


@app.route('/admin/logout/')
def admin_logout():
    if session.get('adminonline'):
        session.pop('adminonline')
    return redirect(url_for('admin'))
