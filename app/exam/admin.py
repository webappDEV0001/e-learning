from django.contrib import admin
from .models import *
from question.models import Question, Answer
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.results import Result


class ExamResource(resources.ModelResource):
	class Meta:
		model = Exam

	def import_data(self, dataset, dry_run=False, raise_errors=False, *args, **kwargs):
		for row in dataset:
			exam_name = row[0]
			q_category = row[1]
			q_subcategory = row[2]
			# skip n
			q_text = row[4]
			q_explanation = row[5]
			correct_answer_text = row[6]
			wrong_1 = row[7]
			wrong_2 = row[8]
			wrong_3 = row[9]
			exam, crt = Exam.objects.get_or_create(name=exam_name, exam_type=Exam.EXAM)
			q, crt = Question.objects.get_or_create(exam=exam, text=q_text)
			if crt:
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


class ExamAdmin(ImportExportModelAdmin):
	resource_class = ExamResource

admin.site.register(Exam, ExamAdmin)
