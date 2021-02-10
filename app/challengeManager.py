from model import db
from model.db_models import Most_point_challenge
from sqlalchemy import exc,desc,asc,and_, or_, not_
from threading import Thread
from datetime import datetime, timedelta
import time

class ChallengeManager:

	def __init__(self):
		print("Creating the thread for Most Point Challenge....")
		worker = Thread(target=self.manageMostPointChallenge)
		worker.setDaemon(True)
		worker.start()

	# For each most point challenge in STARTED state:
	#	- Check if the challenge has finished ( got to the end time )
	# For each most point challenge in INITIAL state:
	#   - Check if it has been in this state for more than 24h. If so, then the request will expire and the challenge set to state DISCARDED
	def manageMostPointChallenge(self):

		while True:

			currentTime = datetime.now()

			# This call is important so the session is recreated and sync with the main app
			db.session.close()

			challenges = db.session.query(Most_point_challenge).filter(
							or_(
								Most_point_challenge.state == 'STARTED',
								Most_point_challenge.state == 'INITIAL'
							)
						).all()

			for i in challenges:
				print(i.to_dict())

			for challenge in challenges:
				if challenge.state == 'STARTED':
					if challenge.end_time > currentTime:
						challenge.state = 'FINISHED'
						print('Change the challenge to FINISHED')

				elif challenge.state == 'INITIAL':					
					timediff = currentTime - challenge.creation_time
					if timediff >= timedelta(minutes=1):
						challenge.state = 'DISCARDED'
						print('Change the challenge to DISCARDED')

			db.session.commit()

			time.sleep(10)



