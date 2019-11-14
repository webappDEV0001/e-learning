from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import *

from question.models import Question, Answer
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.results import Result

admin.site.register(Slide)
admin.site.register(ELearningSession)
admin.site.register(ELearningUserSession)
admin.site.register(ELearningUserAnswer)
admin.site.register(ELearningCorrection)
admin.site.register(ELearningRepetition)


class ELearningResource(resources.ModelResource):
	class Meta:
		model = ELearning

	def import_data(self, dataset, dry_run=False, raise_errors=False, *args, **kwargs):		
		for row in dataset:
			exam_name = row[1]
			q_category = row[2]
			q_subcategory = row[3]
			figure = row[4]
			exam, crt = ELearning.objects.get_or_create(name=exam_name, exam_type=Exam.ELEARNING)
			session_no = row[11]
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

admin.site.register(ELearning, ELearningAdmin)
