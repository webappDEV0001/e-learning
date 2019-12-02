from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from elearning.forms import ElearningForm
from exam.models import Exam
from .models import *

from question.models import Question, Answer
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.results import Result
from import_export.fields import Field

admin.site.register(Slide)
admin.site.register(ELearningSession)
admin.site.register(ELearningUserSession)
admin.site.register(ELearningUserAnswer)
admin.site.register(ELearningCorrection)
admin.site.register(ELearningRepetition)
  
class ELearningResource(resources.ModelResource):
	class Meta:
		model = ELearning

class ELearningAdmin(ImportExportModelAdmin):
	resource_class = ELearningResource
	form = ElearningForm

admin.site.register(ELearning, ELearningAdmin)

#e-learning import/export resource
class ELearningImportExportResource(resources.ModelResource):
	
	class Meta:
		model = ImportExportELearning

	def before_import(self, dataset, result, using_transactions, dry_run = True, **kwargs):
		session_no = 1
		if len(dataset) > 1:
			prev_exam_name = dataset[0][1]
			prev_figure = dataset[0][4]
		for row in dataset:
			exam_name = row[1]
			q_category = row[2]
			q_subcategory = row[3]
			figure = row[4]
			exam, crt = ELearning.objects.get_or_create(name=exam_name, exam_type=Exam.ELEARNING)
			if not figure == 'n' and prev_figure == 'n':
				session_no += 1
			if not prev_exam_name == exam_name:
				session_no = 1
			prev_exam_name = exam_name
			prev_figure = figure
			session, crt = ELearningSession.objects.get_or_create(elearning=exam, number=session_no)
			if not figure == 'n':
				s, crt = Slide.objects.get_or_create(elearning=exam, image=figure)
				if crt:
					session.slides.add(s)
					session.save()
			else:
				q_text = row[5]
				q_explanation = row[6]
				correct_answer_text = row[7]
				wrong_1 = row[8]
				wrong_2 = row[9]
				wrong_3 = row[10]
				q, crt = Question.objects.get_or_create(exam=exam, text=q_text)
				if crt:
					session.questions.add(q)
					session.save()
					q.explanation = q_explanation
					q.text = q_text
					q.category = q_category
					q.subcategory = q_subcategory
					q.save()
					Answer.objects.create(question=q, text=correct_answer_text, correct=True)
					Answer.objects.create(question=q, text=wrong_1)
					Answer.objects.create(question=q, text=wrong_2)
					Answer.objects.create(question=q, text=wrong_3)

		return Result()

class ELearningImportExportAdmin(ImportExportModelAdmin):
	resource_class = ELearningImportExportResource
	def save_model(self, request, obj, form, change):
		if change:
			old_object = self.model.objects.get(id=obj.id)
			old_elearning = ELearning.objects.filter(name=old_object.quiz)[0]
			old_elearning.name = obj.quiz
			old_elearning.save()
			###Slide and Question can't be switched each other, but just figure's name is able to be updated.###
			if not obj.figure == 'n': 
				s = Slide.objects.get_or_create(elearning=old_elearning, image=old_object.figure)
				s.figure = obj.figure #replace with new figure
				s.save()
			else:
				question, created = Question.objects.get_or_create(exam=old_elearning, text=old_object.content)
				question.text = obj.content
				question.explanation = obj.explanation
				question.category = obj.category
				question.sub_category = obj.sub_category
				question.save()
				
				correct_answer, created = Answer.objects.get_or_create(question=question, text=old_object.correct)
				correct_answer.text = obj.correct
				correct_answer.save()
				answer1, created = Answer.objects.get_or_create(question=question, text=old_object.answer1)
				answer1.text = obj.answer1
				answer1.save()
				answer2, created = Answer.objects.get_or_create(question=question, text=old_object.answer2)
				answer2.text = obj.answer2
				answer2.save()
				answer3, created = Answer.objects.get_or_create(question=question, text=old_object.answer3)
				answer3.text = obj.answer3
				answer3.save()
		else:
			elearning, crt = ELearning.objects.get_or_create(name=obj.quiz, exam_type=Exam.ELEARNING)
			###Slide and Question can't be switched each other, but just figure's name is able to be updated.###
			session, crt = ELearningSession.objects.get_or_create(elearning=elearning, number=1)
			if not obj.figure == 'n': 
				s, created = Slide.objects.get_or_create(elearning=elearning, image=obj.figure)
				session.slides.add(s)
				session.save()
			else:
				question, created = Question.objects.get_or_create(exam=elearning, text=obj.content)
				question.text = obj.content
				question.explanation = obj.explanation
				question.category = obj.category
				question.sub_category = obj.sub_category
				question.save()
				session.questions.add(question)
				session.save()
				
				correct_answer, created = Answer.objects.get_or_create(question=question, text=obj.correct)
				correct_answer.save()
				answer1, created = Answer.objects.get_or_create(question=question, text=obj.answer1)
				answer1.save()
				answer2, created = Answer.objects.get_or_create(question=question, text=obj.answer2)
				answer2.save()
				answer3, created = Answer.objects.get_or_create(question=question, text=obj.answer3)
				answer3.save()
		obj.user = request.user
		super().save_model(request, obj, form, change)

admin.site.register(ImportExportELearning, ELearningImportExportAdmin)

