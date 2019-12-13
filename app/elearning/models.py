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
	certificate_count = models.PositiveSmallIntegerField(default=369)

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

	MEMORY_FORCE_CHOICES = [
		('low', 'Low'),
		('medium', 'Medium'),
		('high', 'High'),
	]
	elearning = models.ForeignKey(ELearning, on_delete=models.CASCADE)
	active_session = models.ForeignKey(ELearningSession, on_delete=models.CASCADE, null=True)
	seen_slides = models.PositiveIntegerField(default=0)
	phase = models.IntegerField(choices=PHASES, default=2)
	memory_force = models.CharField(
		max_length=100,
		choices=MEMORY_FORCE_CHOICES,
		default='medium',
	)

	def save(self, *args, **kwargs):
		if self.pk is None:
			# Get session number 1 for start
			self.active_session = self.elearning.sessions.get(number=1)
		super().save(*args, **kwargs)

	@property
	def active_session_number(self):
		return self.active_session.number

	@property
	def memory_force_value(self):
		return self.memory_force

	@property
	def user_progress(self):
		"""
		Please do it so that it is calculated as follows:
		formula = 0
		formula = formula + 0.50 * correct_1 / no_of_all_questions
		formula = formula + 0.65 * correct_2 / no_of_all_questions
		formula = formula + 0.80 * correct_3 / no_of_all_questions
		formula = formula + 0.95 * correct_4 / no_of_all_questions
		formula = formula + 1.00 * correct_5 / no_of_all_questions

		progress = min(formula, 1)

		return round(progress * 100,2)

		correct_1: means number of questions in the particular elearning that were answered correctly 1 time by the user
		correct_2: means number of questions in the particular elearning that were answered correctly 2 times by the user
		"""
		no_of_all_questions = self.exam.questions.count()
		from_rep=1
		#all_correct_answers = self.answers.filter(answer__correct=True).values('question').annotate(qcount=Count('question'))

		# Read correct answers from repitions and add 1 in each count as it comes in repitition after answered correctly first
		all_correct_answers = ELearningRepetition.objects.filter(answered=True).values('question').annotate(qcount=Count('question'))
		if len(all_correct_answers) == 0:
			from_rep = 0
			all_correct_answers = self.answers.filter(answer__correct=True).values('question').annotate(qcount=Count('question'))


		correct_1,correct_2,correct_3,correct_4,correct_5=0,0,0,0,0
		formula = 0
		# print(all_correct_answers)

		for all_ques_dict in all_correct_answers:
			# It's counting 0 as 1, 1 as 2 and so on
			# because need to add 1 in each count as it comes in repitition after answered correctly first
			if all_ques_dict['qcount'] == 0 and from_rep:
				correct_1 += 1
			if all_ques_dict['qcount'] == 1 and from_rep:
				correct_2 += 1
			if all_ques_dict['qcount'] == 2 and from_rep:
				correct_3 += 1
			if all_ques_dict['qcount'] == 3 and from_rep:
				correct_4 += 1
			if all_ques_dict['qcount'] == 4 and from_rep:
				correct_5 += 1
			#if not from repititions no need to count 0 as 1.
			if all_ques_dict['qcount'] == 1 and not from_rep:
				correct_1 += 1
			if all_ques_dict['qcount'] == 2 and not from_rep:
				correct_2 += 1
			if all_ques_dict['qcount'] == 3 and not from_rep:
				correct_3 += 1
			if all_ques_dict['qcount'] == 4 and not from_rep:
				correct_4 += 1
			if all_ques_dict['qcount'] == 5 and not from_rep:
				correct_5 += 1


		try:
			formula = formula + 0.50 * correct_1 / no_of_all_questions
			# print(formula,"1")
			formula = formula + 0.65 * correct_2 / no_of_all_questions
			# print(formula, "2")
			formula = formula + 0.80 * correct_3 / no_of_all_questions
			# print(formula, "3")
			formula = formula + 0.95 * correct_4 / no_of_all_questions
			# print(formula, "4")
			formula = formula + 1.00 * correct_5 / no_of_all_questions
			# print(formula, "5")

			progress = min(formula, 1)
			# print(progress,"progress")
		except:
			progress = 0

		return round(progress * 100, 2)


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
	content = models.TextField(blank=True)
	explanation = models.TextField(blank=True)
	correct = models.TextField(blank=True)
	answer1 = models.TextField(blank=True)
	answer2 = models.TextField(blank=True)
	answer3 = models.TextField(blank=True)	

	def __str__(self):
		return "%s(%d)" % (self.quiz, self.id)


class Presentation(models.Model):
	"""
	This model used to store the presentation data.
	"""

	elearning = models.ForeignKey(ELearning, on_delete=models.CASCADE)
	topic = models.CharField(max_length=500, help_text="topic of the presentation")
	slide = models.CharField(max_length=1000, help_text="name of the slide")

	def __str__(self):
		return "%s - %s" % (self.title, self.elearning.name)