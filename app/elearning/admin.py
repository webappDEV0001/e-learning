from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import *

from question.models import Question, Answer
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.results import Result
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget
from import_export.widgets import CharWidget

admin.site.register(Slide)
admin.site.register(ELearningSession)
admin.site.register(ELearningUserSession)
admin.site.register(ELearningUserAnswer)
admin.site.register(ELearningCorrection)
admin.site.register(ELearningRepetition)
  
class ELearningResource(resources.ModelResource):

	name = Field(column_name='quiz')
	category = Field(attribute='category', column_name='category')
	sub_category = Field(column_name='sub_category')
	figure = Field(column_name='figure')
	content = Field(column_name='content')
	explanation = Field(column_name='explanation')
	correct = Field(column_name='correct')
	answer1 = Field(column_name='answer1')
	answer2 = Field(column_name='answer2')
	answer3 = Field(column_name='answer3')
	
	class Meta:
		model = ELearning
		fields = ('name', 'category', 'sub_category', 'figure', 'content', 'explanation', 'correct', 'answer1', 'answer2', 'answer3')

	def import_data(self, dataset, dry_run=False, raise_errors=False, *args, **kwargs):
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
				print('decided session no: ', session_no, ' with exam name is: ', exam_name)
			if not prev_exam_name == exam_name:
				session_no = 1
				print('session no is initialized as 1 with exam name: ', exam_name, 'prev name is: ', prev_exam_name)
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


class ELearningAdmin(ImportExportModelAdmin):
	resource_class = ELearningResource
	# list_display = ('quiz', 'category')

admin.site.register(ELearning, ELearningAdmin)
