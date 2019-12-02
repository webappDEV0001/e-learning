from django.contrib import admin
from django.http import HttpResponse
from import_export.admin import ImportExportModelAdmin
from django.urls import path
import pandas
from elearning.forms import ElearningForm
from exam.models import Exam
from elearning.views import ElearningImportView
from .models import *
from question.models import Question, Answer

@admin.register(ELearning)
class AdminElearning(admin.ModelAdmin):
	form = ElearningForm
	change_list_template = "elearning/admin_changelist.html"

	def get_urls(self):
		urls = super(AdminElearning, self).get_urls()
		my_urls = [
			path('import-csv/', self.admin_site.admin_view(ElearningImportView.as_view()),
				 name="import-csv"),
			path('export-csv/', self.export_csv),
		]
		return my_urls + urls

	def export_csv(self, request):

		question_objects = Question.objects.all().values()
		df = pandas.DataFrame()
		for q in question_objects:
			a = Answer.objects.filter(question=q['id']).values()
			exam = Exam.objects.filter(id=q['exam_id']).values()
			count_answer = 1
			for i in range(0, 3):
				if a[i]['correct']:
					df['correct'] = a[i]
				else:
					key = 'answer' + str(count_answer)
					df[key] = a[i]
					count_answer += 1

			df['id'] = q['id']
			df['quiz'] = exam[0]['name']
			df['category'] = q['category']
			df['sub_category'] = q['sub_category']
			df['figure'] = 'n'
			df['content'] = q['text']
			df['explanation'] = q['explanation']

		response = HttpResponse(df, content_type='application/vnd.ms-excel')
		response['Content-Disposition'] = 'attachment; filename="db_exam.xlsx"'
		df.to_csv(path_or_buf=response, sep=';', float_format='%.2f', index=False, decimal=",")
		return response

admin.site.register(Slide)
admin.site.register(ELearningSession)
admin.site.register(ELearningUserSession)
admin.site.register(ELearningUserAnswer)
admin.site.register(ELearningCorrection)
admin.site.register(ELearningRepetition)