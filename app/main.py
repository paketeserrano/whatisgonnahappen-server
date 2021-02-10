from model import app,db
from model.db_models import Playlist,Video, Question,Answer,Tag,Response, User, Most_point_challenge
from argparse import ArgumentParser
from flask import json, jsonify,request,session
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import exists
import sys
from sqlalchemy import exc,desc,asc,and_, or_, not_
from  sqlalchemy.sql.expression import func
from datetime import datetime, timedelta
from challengeManager import ChallengeManager


challengeManager = ChallengeManager()

def initDB():
	db.create_all()
	db.session.commit()

def recreateDB():
	db.drop_all()
	initDB()


@app.route("/")
def home():
    return "Soccer Fans"

###################################" Login service ####################################

@app.route('/login', methods=['GET', 'POST'])
def login():
	data_received=json.loads(request.data)
	
	email = data_received['email']
	password = data_received['password']

	print('email: ', email)

	'''
	if current_user.is_authenticated:
		print('current user id: ' + str(current_user.id))
		print('username: ' + current_user.username)
		print('email: ' + current_user.email)
		user = User.query.filter_by(email=email).first()
		return jsonify(user.to_dict())
	'''
	if True: # This should contain the fields validations
		user = User.query.filter_by(email=email).first()
		if user is None:
			print("No user found")
			if not user.check_password(password):
				print("Password is not correct")
		if user is None or not user.check_password(password):
			return jsonify('{"id":-1}')
		login_user(user, True)
		return jsonify(user.to_dict())
	return jsonify('{"id":-1}')

###################################" Login service ####################################

@app.route('/logout')
def logout():
	logout_user()
	return jsonify('{"id":-1}')

# ##################################" Login service ####################################
@app.route('/register', methods=['GET', 'POST'])
def register():
	data_received=json.loads(request.data)

	name = data_received['name']
	email = data_received['email']
	password = data_received['password']

	user = User(username=name,email=email)
	user.set_password(password)
	db.session.add(user)
	try:
		db.session.commit()
	except IntegrityError as e:
		return jsonify('{"id":-1}')

	return jsonify(user.to_dict())

# ##################################" Get the list of channels(tournaments) ####################################
@app.route('/getChannels', methods=['GET'])
@login_required
def getChannels():
	channels = Channel.query.all()
	return jsonify(channels=[i.to_dict() for i in channels])

# ################################## Get the list of playlists for a certain channel (A playlist is a list of videos with a certain topic, like league round 1) ####################################
@app.route('/getPlaylists', methods=['GET'])
@login_required
def getPlaylists():
	playlistId = int(request.args.get('plid'))
	if playlistId == -1:
		playlists = Playlist.query.all()
	else:
		playlists = Playlist.query.filter_by(id=playlistId).all()

	return jsonify(playlists=[i.to_dict() for i in playlists])

# ################################## Get the list of videos for a certain playlist (A playlist is a list of videos with a certain topic, like league round 1)   ####################################
@app.route('/getVideos', methods=['GET'])
@login_required
def getVideos():	
	playlistId = request.args.get('plid')
	videos = Video.query.filter(Video.playlists.any(id=playlistId)).all()
	#for video in videos:
	#	question = Response.query.filter_by(user_id=current_user.id)
		
	return jsonify(videos=[i.to_dict() for i in videos])

# ################################## Get a random video  ####################################
@app.route('/getRandomVideo', methods=['GET'])
#@login_required
def getRandomVideo():
	# This query will return a random video
	video = db.session.query(Video).order_by(func.rand()).first() #Answer.query.order_by(func.rand()).first() #asc(Answer.id)).all()
	return jsonify(video=video.to_dict())

# ################################## Post the response to a question  ####################################
# Assigns a response to question by a user
# It never returns anything because the video in the client will continue. If it fails I might need some retry mechanism depending on the failure
# TODO: Implement constraint in db to allow only one response per question and user
# 
@app.route('/postQuestionResponse', methods=['POST'])
@login_required
def postResponse():
	data_received = json.loads(request.data)
	questionId = int(data_received['questionId'])
	answerId = int(data_received['answerId'])
	question = Question.query.filter_by(id=questionId).first()	
	points = 10
	if question.official_answer_id == answerId:
		points = 20

	try:
		user = User.query.filter_by(id=current_user.id).first()
		user.score += points

		# Check if user already answered this question with the same answer
		# response = Response.query.filter_by(user_id=current_user.id, question_id=questionId, answer_id=answerId).first()
		responseExists = db.session.query(Response.query.filter(Response.user_id == current_user.id,Response.question_id==questionId,Response.answer_id==answerId).exists()).scalar()
		response = None
		if responseExists:
			# If response exists then increment counter
			response = Response.query.filter(Response.user_id == current_user.id,Response.question_id==questionId,Response.answer_id==answerId).first()
			response.counter += 1
		else:
			# Create new response
			response = Response(user_id=current_user.id, question_id=questionId, answer_id=answerId)
			
		db.session.add(response)		
	except exc.IntegrityError:
		print("This most likely happened because of an integrity error when the user answers the same question more than once")
		return jsonify(score=user.score, status='500')

	db.session.commit()
	return jsonify(score=user.score, status='200')

@app.route('/updateVideos', methods=['POST'])
@login_required
def updateVideo():
	data_received = json.loads(request.data)
	updatedVideosJson = json.loads(data_received['videos'])
	for updatedVideo in updatedVideosJson:
		video = Video.query.filter_by(id=updatedVideo['id']).first()
		video.name = updatedVideo['name']
		video.youtube_id = updatedVideo['youtubeId']
		video.published = bool(updatedVideo['published'])
		video.thumbnail = updatedVideo['thumbnail']	
	db.session.commit()

	return {}

################################### Add a video ####################################
@app.route('/addVideo', methods=['POST'])
@login_required
def addVideo():
	videoJson = json.loads(request.data)
	playlist = Playlist.query.filter_by(id=videoJson['playlist_id']).first()
	video = Video(name=videoJson['name'],youtube_id=videoJson['youtube_id'],published=True)
	questionsJson = videoJson['questions']
	for questionJson in questionsJson:
		question = Question(statement=questionJson['statement'], time_to_start=questionJson['time_to_start'],
					time_to_end=questionJson['time_to_end'], time_to_show=questionJson['time_to_show'], time_to_stop=questionJson['time_to_stop'])
		answersJson = questionJson['answers']
		answerIndex = 1
		for answerJson in answersJson:
			statement = answerJson
			answer = Answer.query.filter_by(statement=statement).first()

			# Answer None means it's a new answer that is not in the system
			if answer is None:
				answer = Answer(statement=statement)

			if int(questionJson['official_answer']) == answerIndex:
				question.official_answer = answer

			question.answers.append(answer)
			answerIndex = answerIndex + 1

		video.questions.append(question)

	playlist.videos.append(video)

	db.session.commit()

	return {}	

################################### Add a like to the question ####################################
@app.route('/likeQuestion', methods=['POST'])
@login_required
def likeQuestion():
	likeInfo = json.loads(request.data)
	question = Question.query.filter_by(id=likeInfo['id']).first()
	if likeInfo['type'] == 'like':
		if question.likes != None:
			question.likes += 1
		else:
			question.likes = 1
	elif likeInfo['type'] == 'no_like':
		if question.no_likes != None:
			question.no_likes += 1
		else:
			question.no_likes = 1

	db.session.commit()
	return {}

################################### Create most points challenge ####################################
@app.route('/createMostPointsChallenge', methods=['POST'])
@login_required
def createMostPointsChallenge():
	challengeInfo = json.loads(request.data)
	user = User.query.filter_by(username=challengeInfo['challenged_username']).first()
	if(user == None):
		return jsonify(code='USER_NOT_FOUND')

	print("current_user.id: " + str(current_user.id))
	print("user.id: " + str(user.id))

	#datetime.strptime(datetime.now(), '%Y-%m-%d %H:%M:%S')
	creationTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	challenge = Most_point_challenge(challenger_id=current_user.id, challenged_id=user.id, challenger_points=0,challenged_points=0,state='INITIAL', creation_time=creationTime)
	db.session.add(challenge)
	db.session.commit()
	return jsonify(code='SUCCESS')

################################### Save most points challenge ####################################
@app.route('/saveMostPointsChallenge', methods=['POST'])
@login_required
def saveMostPointsChallenge():
	challengeInfo = json.loads(request.data)
	challenge = Most_point_challenge.query.filter_by(id=challengeInfo['id']).first()
	challenge.challenger_id = challengeInfo['challenger']['id']
	challenge.challenged_id = challengeInfo['challenged']['id']
	challenge.challenger_points = challengeInfo['challenger_points']
	challenge.challenged_points = challengeInfo['challenged_points']
	challenge.duration = 1  # For now I set it to 1h by default
	challenge.start_time = datetime.strptime(challengeInfo['start_time'], '%Y-%m-%d %H:%M:%S')
	challenge.end_time = datetime.strptime(challengeInfo['end_time'], '%Y-%m-%d %H:%M:%S')
	challenge.state = challengeInfo['state']

	db.session.commit()

	return jsonify(code='SUCCESS')

################################### Accept most points challenge ####################################
@app.route('/acceptMostPointsChallenge', methods=['POST'])
@login_required
def acceptMostPointsChallenge():
	challengeInfo = json.loads(request.data)
	challenge = Most_point_challenge.query.filter_by(id=challengeInfo['id']).first()
	if challenge != None:
		print(challengeInfo)
		if challenge.challenged.id == challengeInfo['challenged']['id'] or challenge.challenger.id == challengeInfo['challenger']['id']:
			challenge.state = 'STARTED'
			now = datetime.now()
			challenge.start_time = now.strftime('%Y-%m-%d %H:%M:%S')
			increase = timedelta(seconds = 20)#hours = 1)
			end = now + increase
			challenge.end_time = end.strftime('%Y-%m-%d %H:%M:%S')
			db.session.commit()
			return jsonify(code='SUCCESS')
		else:
			return jsonify(code='WRONG_USER')		
	else:
		return jsonify(code='CHALLENGE_NOT_FOUND')

################################### Get user most point challenges that are active ####################################
@app.route('/getUserActiveMostPointChallenges', methods=['GET'])
#@login_required
def getUserActiveMostPointChallenges():
	username = request.args.get('usr')
	user = User.query.filter_by(username=username).first()
	print('userId: ' + str(user.id))
	challenges = db.session.query(Most_point_challenge).filter(
		and_( Most_point_challenge.state == 'INITIAL',
			or_(
				Most_point_challenge.challenger_id == user.id,
				Most_point_challenge.challenged_id == user.id
			)
		)
	).all()

	for i in challenges:
		print("-------------------")
		print(i.to_dict())
		print("-------------------")

	return jsonify(challenges=[i.to_dict() for i in challenges])

 ################################### Main #################################### 
if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('-db')
	args = parser.parse_args()
	dbaction = args.db
	print("dbaction: ",dbaction)
	if dbaction == 'init':
		initDB()
	elif dbaction == 'recreate':
		recreateDB()		

	app.run(debug=True)
	# Use below when testing on real phone in home network
	#app.run(debug=False, host='0.0.0.0')