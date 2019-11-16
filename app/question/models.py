import datetime
import random
from django.utils import timezone
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import User
from exam.models import Exam


class Question(models.Model):
	exam = models.ForeignKey(Exam, on_delete=models.DO_NOTHING, related_name='questions')
	explanation = models.TextField(blank=True)
	text = models.TextField()
	category = models.CharField(max_length=254, blank=True)
	sub_category = models.CharField(max_length=254, blank=True)

	def __str__(self):
		return self.text

	def shuffled_answers(self):
		answers = list(self.answers.all())
		random.shuffle(answers)
		return answers


class Answer(models.Model):
	question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
	text = models.TextField()
	correct = models.BooleanField(default=False)

	def __str__(self):
		return self.text


class ExamUserSession(models.Model):
	""" Class for storing user exam session info.
	"""
	exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	n_questions = models.PositiveIntegerField(default=5, editable=False)
	started = models.DateTimeField(blank=True, null=True)
	finished = models.DateTimeField(blank=True, null=True)
	active_question = models.ForeignKey(Question, null=True, on_delete=models.CASCADE)

	@property
	def stop_time(self):
		if self.started and self.exam.time_limit:
			return self.started + datetime.timedelta(seconds=self.exam.time_limit)
		return None

	@property
	def time_left(self):
		if not self.exam.time_limit or not self.started:
			return None
		time_passed = (timezone.now() - self.started).seconds
		time_left = self.exam.time_limit - time_passed
		return time_left

	@property
	def no_time_left(self):
		if self.time_left and self.time_left <= 0:
			self.stop_test()
			return True
		return False

	@property
	def get_score(self):
		formula = self.get_session_answers().filter(answer__correct=True).count() / self.n_questions * 100
		return round(formula, 2)

	@property
	def count_correct_answers(self):
		return ExamUserAnswer.objects.filter(session=self, answer__correct=True).count()

	def save(self, *args, **kwargs):
		if self.pk is None:
			self.n_questions = self.exam.n_questions
		super().save(*args, **kwargs)

	def start_test(self):
		self.started = timezone.now()
		self.save()

	def stop_test(self):
		if not self.finished:
			self.finished = timezone.now()
			self.save()

	def get_session_answers(self):
		return ExamUserAnswer.objects.filter(session=self)



class ExamUserAnswer(models.Model):
	session = models.ForeignKey(ExamUserSession, on_delete=models.CASCADE)
	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
