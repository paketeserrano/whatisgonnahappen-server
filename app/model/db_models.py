from flask_sqlalchemy  import SQLAlchemy
from flask import Flask
from . import db, login
from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

user_video_completion = db.Table('user_video_completion',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('video_id', db.Integer, db.ForeignKey('video.id'))
)

class User(UserMixin, db.Model,SerializerMixin):
	serialize_only = ('id', 'username', 'email', 'role','score')

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	role = db.Column(db.String(128),default='admin')
	completed_videos = db.relationship("Video", secondary=user_video_completion,backref=db.backref('completed_by_user'))
	responses = db.relationship('Response', backref='user', lazy=True) # Collection of responses from this user
	score = db.Column(db.Integer,default=0)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

playlist_video_map = db.Table('playlist_video_map',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id',ondelete="cascade")),
    db.Column('video_id', db.Integer, db.ForeignKey('video.id', ondelete="cascade"))
)

playlist_tag_map = db.Table('playlist_tag_map',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

video_tag_map = db.Table('video_tag_map',
    db.Column('video_id', db.Integer, db.ForeignKey('video.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

question_tag_map = db.Table('question_tag_map',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

question_answer_map = db.Table('question_answer_map',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id', ondelete="cascade")),
    db.Column('answer_id', db.Integer, db.ForeignKey('answer.id', ondelete="cascade"))
)

response_answer_map = db.Table('response_answer_map',
    db.Column('response_id', db.Integer, db.ForeignKey('response.id', ondelete="cascade")),
    db.Column('answer_id', db.Integer, db.ForeignKey('answer.id', ondelete="cascade"))
)

class Playlist(db.Model,SerializerMixin):
	serialize_only = ('id', 'name', 'published')

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), nullable=False, unique=True)
	published = db.Column(db.Boolean, default=True, nullable=False)
	videos = db.relationship("Video", secondary=playlist_video_map,backref=db.backref('playlists'))
	tags = db.relationship("Tag", secondary=playlist_tag_map,backref=db.backref('playlists'))

class Video(db.Model,SerializerMixin):
	serialize_only = ('id', 'name', 'youtube_id', 'published','questions', 'channel_id')

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), nullable=False)
	youtube_id = db.Column(db.String(120), unique=True, nullable=False)
	published = db.Column(db.Boolean, default=True, nullable=False) 
	thumbnail = db.Column(db.String(120))
	questions = db.relationship('Question', backref='video', lazy=True)
	tags = db.relationship("Tag", secondary=video_tag_map,backref=db.backref('videos'))
	channel_id = db.Column(db.String(120))
	not_embeddable = db.Column(db.Boolean, default=False, nullable=False)
	is_age_restricted = db.Column(db.Boolean, default=False, nullable=False)

class Question(db.Model, SerializerMixin):
	serialize_only = ('id', 'video_id','official_answer_id','statement','time_to_show','time_to_stop','answers','time_to_start', 'time_to_end','likes','no_likes')

	id = db.Column(db.Integer, primary_key=True)
	video_id = db.Column(db.Integer, db.ForeignKey('video.id', ondelete="cascade"))
	official_answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
	statement = db.Column(db.String(300), nullable=False)
	time_to_start = db.Column(db.Integer, nullable=False) # video second where the section for the question starts
	time_to_end = db.Column(db.Integer, nullable=False)   # video second where the section for the question end
	time_to_show = db.Column(db.Integer, nullable=False)  #Video second where this question is asked
	time_to_stop = db.Column(db.Integer, nullable=False)  #Video second where the video stops so user answer the question
	answers = db.relationship('Answer', secondary=question_answer_map,backref=db.backref('questions'))  # Options presented to user as answers
	responses = db.relationship('Response', backref='question', lazy=True) # Collection of responses to this question from the users	
	tags = db.relationship("Tag", secondary=question_tag_map,backref=db.backref('questions'))
	likes = db.Column(db.Integer, default=0) 
	no_likes = db.Column(db.Integer, default=0) 

class Answer(db.Model, SerializerMixin):
	serialize_only = ('id','statement')

	id = db.Column(db.Integer, primary_key=True)
	responses = db.relationship('Response', backref='answer', lazy=True) # Collection of responses that contain this answer item as the answer
	official_answer_for_questions = db.relationship('Question',  backref='official_answer', lazy=True) # Official answer ( actual call in the game) list for certain questions
	statement = db.Column(db.String(300), unique=True, nullable=False)

class Tag(db.Model, SerializerMixin):

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), nullable=False, unique=True)	

class Response(db.Model, SerializerMixin):

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # User that answered this question
	question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
	answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))  # This is the answer the user selected in his/her response
	counter = db.Column(db.Integer, default=1) # Number of times a user responds a certain question with the same answer
	is_right = db.Column(db.Boolean, default=False, nullable=False)

	#__table_args__ = (
	#	db.UniqueConstraint('user_id', 'question_id', name='unique_response'),
	#)
	
class Most_point_challenge(db.Model, SerializerMixin):
	serialize_only = ('id', 'challenger_id', 'challenged_id', 'challenged','challenger','challenger_points', 'challenged_points', 'start_time', 'end_time', 'creation_time', 'duration', 'state')
	id = db.Column(db.Integer, primary_key=True)
	challenger_id = db.Column(db.Integer, db.ForeignKey('user.id')) 	
	challenged_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
	challenged = db.relationship("User", foreign_keys=[challenged_id])
	challenger = db.relationship("User", foreign_keys=[challenger_id])
	challenger_points = db.Column(db.Integer, default=0)
	challenged_points = db.Column(db.Integer, default=0)
	duration = db.Column(db.Integer, default=1)   # In hours
	start_time = db.Column(db.DateTime)
	end_time = db.Column(db.DateTime)
	creation_time = db.Column(db.DateTime)
	state = db.Column(db.String(100), nullable=False)




