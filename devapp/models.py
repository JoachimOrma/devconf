from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

db = SQLAlchemy()


class State(db.Model):
    state_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    state_name = db.Column(db.String(100), nullable=False)
    # set relationship
    lgas = db.relationship("Lga", back_populates="state_deets")
    state_people = db.relationship("User", back_populates="mystate_deets")


class Lga(db.Model):
    lga_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    lga_name = db.Column(db.String(100), nullable=False)
    lga_stateid = db.Column(db.Integer, db.ForeignKey('state.state_id'))    
    # set relationships
    lga_people = db.relationship("User", back_populates="mylgadeets")
    state_deets = db.relationship("State", back_populates="lgas")


class User(db.Model):  
    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_fname = db.Column(db.String(100), nullable=False)
    user_lname = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    user_password = db.Column(db.String(255), nullable=True)
    user_phone = db.Column(db.String(120), nullable=True)
    user_pix = db.Column(db.String(120), nullable=True)
    user_datereg = db.Column(db.DateTime(), default=datetime.utcnow) # default date
    # set the foreign key
    user_levelid = db.Column(db.Integer, db.ForeignKey('level.level_id'))
    user_stateid = db.Column(db.Integer, db.ForeignKey('state.state_id'))
    user_lgaid = db.Column(db.Integer, db.ForeignKey('lga.lga_id'))
    # set relationships
    mystate_deets = db.relationship("State", back_populates="state_people")
    mylgadeets = db.relationship("Lga", back_populates="lga_people")
    myleveldeets = db.relationship("Level", back_populates="developers_inlevel")
    donordeets = db.relationship('Donate', back_populates='donatedby')


class Level(db.Model):
    level_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    level_name = db.Column(db.String(100), nullable=False)
    # set relationship
    developers_inlevel = db.relationship("User", back_populates="myleveldeets")
    topics = db.relationship("Topic", back_populates='leveldeets')


class Admin(db.Model):
    admin_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    admin_username = db.Column(db.String(20), nullable=True)
    admin_pwd = db.Column(db.String(200), nullable=True)


class Topic(db.Model):
    topic_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    topic_title = db.Column(db.String(255), nullable=False)
    topic_image = db.Column(db.Text, nullable=True)
    topic_date = db.Column(db.DateTime(), default=datetime.utcnow)
    topic_status = db.Column(db.Enum('1', '0'), nullable=False, server_default='0')

    # set the foreign key
    topic_levelid = db.Column(db.Integer, db.ForeignKey('level.level_id'))

    # set relationships
    leveldeets = db.relationship("Level", back_populates='topics')


class Donate(db.Model):
    donate_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    donate_amt = db.Column(db.Float, nullable=False)
    donate_date = db.Column(db.DateTime(), default=datetime.utcnow)
    donate_status = db.Column(db.Enum('pending', 'failed', 'paid'), nullable=False, server_default='0')
    donate_donor = db.Column(db.String(255), nullable=True)
    donate_email = db.Column(db.String(255), nullable=True)
    donate_ref = db.Column(db.String(255), nullable=True)
    donate_paygate = db.Column(db.String(255), nullable=True)
    donate_update = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    # set foreignkey
    donate_userid = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)

    # set relationship
    donatedby = db.relationship('User', back_populates='donordeets')
