import uuid
import datetime
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from users.models import User


class Exam(models.Model):
	""" Elearning (light version).
		The idea is as follows: the HR person will start the exam for the candidate. The exam will show N random
		questions. When the exam is finished, the score should be saved in the “Exam history of the user”.

		`n_questions`: number of questions per exam user session.

	"""
	EXAM = 'exam'
	ELEARNING = 'elearning'
	# ELEARNING_NS = 'elearning_ns'

	TYPES = [
		(EXAM, 'Exam'),
		(ELEARNING, 'E-learning')
		# (ELEARNING_NS, 'E-learning (no slides)')
	]

	name = models.CharField(max_length=255)
	slug = models.SlugField(max_length=255, default='', editable=False)
	author = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, blank=True, null=True)
	time_limit = models.IntegerField(default=30)
	n_questions = models.PositiveIntegerField(default=5)
	public = models.BooleanField(default=False)
	description = models.TextField(blank=True)
	exam_type = models.CharField(max_length=15, default=EXAM, choices=TYPES)
	show_answers = models.BooleanField(default=True)

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		kwargs = {
			'pk': self.id,
			'slug': self.slug
		}
		return reverse('exam', kwargs=kwargs)

	def save(self, *args, **kwargs):
		self.slug = slugify(self.name, allow_unicode=True)
		super().save(*args, **kwargs)

class ImportExportExam(models.Model):
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