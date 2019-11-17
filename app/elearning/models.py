import datetime
from django.db import models
from users.models import User
from exam.models import Exam
from question.models import Question, Answer, ExamUserSession
from django.db.models import Count


class ELearning(Exam):
	""" The idea is as follows: (optionally) the user get’s each day a
		portion of slides. New questions are about the content presented
		on the slides or just on main elearning topic.
	"""
	slides = models.BooleanField(default=False)
	random_questions = models.BooleanField(default=True)


class Slide(models.Model):
	elearning = models.ForeignKey(ELearning, on_delete=models.DO_NOTHING)
	image = models.ImageField(upload_to='slides/')


class ELearningSession(models.Model):
	elearning = models.ForeignKey(ELearning, on_delete=models.DO_NOTHING, related_name='sessions')
	number = models.PositiveIntegerField(default=0)
	slides = models.ManyToManyField(Slide, blank=True)
	questions = models.ManyToManyField(Question, blank=True)


class ELearningUserSession(ExamUserSession):
	PHASES = (
		(0, 'Corrections'),
		(1, 'Repetitions'),
		(2, 'New Questions'),
		(3, 'Slides'),
	)
	elearning = models.ForeignKey(ELearning, on_delete=models.CASCADE)
	active_session = models.ForeignKey(ELearningSession, on_delete=models.CASCADE, null=True)
	seen_slides = models.PositiveIntegerField(default=0)
	phase = models.IntegerField(choices=PHASES, default=2)

	def save(self, *args, **kwargs):
		if self.pk is None:
			# Get session number 1 for start
			self.active_session = self.elearning.sessions.get(number=1)
		super().save(*args, **kwargs)

	@property
	def active_session_number(self):
		return self.active_session.number

	@property
	def user_progress(self):
		q_dict = {}
		no_of_all_questions = self.exam.questions.count()
		all_correct_answers = self.answers.filter(answer__correct=True).values('question').annotate(qcount=Count('question'))
		for q in all_correct_answers:
			q_dict.setdefault(q['qcount'],[]).append(q['question'])

		formula = 10 * self.answers.count() / no_of_all_questions
		#formula = formula + 0.25 * q_dict.get(2, 0) / no_of_all_questions
		#formula = formula + 0.15 * q_dict.get(3, 0) / no_of_all_questions
		#formula = formula + 0.05 * q_dict.get(4, 0) / no_of_all_questions
		#formula = formula + 0.05 * q_dict.get(5, 0) / no_of_all_questions
		progress = min(formula, 1)
		return round(progress * 100,2)

class ELearningUserAnswer(models.Model):
	session = models.ForeignKey(ELearningUserSession, on_delete=models.CASCADE, related_name='answers')
	session_number = models.PositiveIntegerField(default=0) # number of active session when answer is commited
	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)


class ELearningRepetition(models.Model):
	created = models.DateTimeField(auto_now_add=True)
	session = models.ForeignKey(ELearningUserSession, on_delete=models.CASCADE)
	repeat_after = models.DateField()
	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	answered = models.BooleanField(default=False)


class ELearningCorrection(models.Model):
	created = models.DateTimeField(auto_now_add=True)
	session = models.ForeignKey(ELearningUserSession, on_delete=models.CASCADE)
	question = models.ForeignKey(Question, on_delete=models.CASCADE)

class ImportExportELearning(models.Model):
	""" 
	This model is for only use Import/Export
	"""
	quiz = models.CharField(max_length=254, blank=False)
	category = models.CharField(max_length=254, blank=False)
	sub_category = models.CharField(max_length=254, blank=False)
	figure = models.CharField(max_length=254, blank=False, default='n')
	content = models.CharField(max_length=254, blank=True)
	explanation = models.CharField(max_length=254, blank=True)
	correct = models.CharField(max_length=254, blank=True)
	answer1 = models.CharField(max_length=254, blank=True)
	answer2 = models.CharField(max_length=254, blank=True)
	answer3 = models.CharField(max_length=254, blank=True)	

	def __str__(self):
		return "%s(%d)" % (self.quiz, self.id)