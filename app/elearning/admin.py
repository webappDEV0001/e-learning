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
from pandas import ExcelWriter
import os

from .views import PresentationImportView


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
		elearning_session = ELearningSession.objects.all()

		field_names = ['id', 'quiz','session', 'category', 'sub_category','figure','content', 'explanation', 'correct', 'answer1',
					   'answer2', 'answer3']

		id_list = []
		elearning_name_list = []
		session_list=[]
		category = []
		sub_category = []
		figure_list=[]
		content = []
		explanation_list = []
		correct = []
		answer1 = []
		answer2 = []
		answer3 = []
		count=1
		for q in elearning_session:

			try:
				for slide in q.slides.all().values():
					# if q.elearning in elearning_name_list:
					# 	session_list.append(q.number)
					# else:
					# 	count = 1
					session_list.append(q.number)
					id_list.append(count)
					elearning_name_list.append(q.elearning)
					category.append("n")
					sub_category.append("n")
					figure_list.append(slide['image'])
					content.append("n")
					explanation_list.append("n")
					correct.append("n")
					answer1.append("n")
					answer2.append("n")
					answer3.append("n")

				for question in q.questions.all().values():
					id_list.append(count)
					# if q.elearning in elearning_name_list:
					# 	session_list.append(count)
					# else:
					# 	count = 1
					session_list.append(q.number)
					elearning_name_list.append(q.elearning)
					category.append(question['category'])
					sub_category.append(question['sub_category'])
					figure_list.append("n")
					content.append(question['text'])
					explanation_list.append(question['explanation'])
					correct_answer = Answer.objects.filter(question=question['id'], correct=True).values_list('text')
					other_answers = Answer.objects.filter(question=question['id'], correct=False).values_list('text')
					correct.append(correct_answer[0][0])
					try:
						answer1.append(other_answers[0][0])
					except:
						answer1.append("")
					try:
						answer2.append(other_answers[1][0])
					except:
						answer2.append("")
					try:
						answer3.append(other_answers[2][0])
					except:
						answer3.append("")
			except:
				continue
			else:
				count += 1


		data = {'id': id_list, 'quiz': elearning_name_list,'session':session_list,
				'category': category, 'sub_category': sub_category,'figure':figure_list,
				'content': content, 'explanation': explanation_list, 'correct': correct, 'answer1': answer1,
				'answer2': answer2, 'answer3': answer3}
		df = pandas.DataFrame(data, columns=field_names)

		df = df.dropna()

		writer = ExcelWriter('Elearning-db.xlsx')
		df.to_excel(writer, 'Elearning', index=False)
		writer.save()

		path = "Elearning-db.xlsx"

		if os.path.exists(path):
			with open(path, "rb") as excel:
				data = excel.read()

			response = HttpResponse(data,
									content_type='application/vnd.ms-excel')
			response['Content-Disposition'] = 'attachment; filename="db_elearning.xlsx"'
		return response


@admin.register(Presentation)
class AdminPresentation(admin.ModelAdmin):
	change_list_template = "elearning/presentation_admin_changelist.html"

	def get_urls(self):
		urls = super(AdminPresentation, self).get_urls()
		my_urls = [
			path('import-presentation/', self.admin_site.admin_view(PresentationImportView.as_view()),
				 name="import-presentation"),
			path('export-presentation/', self.export_csv),
		]
		return my_urls + urls


	def export_csv(self, request):
		field_names=["id","presentation_name","topic","slide"]
		id_list=[]
		presentation_name_list = []
		topic_list = []
		slide_list = []

		presentation_obj = Presentation.objects.all()

		count = 1
		for presentation in presentation_obj:
			id_list.append(count)
			presentation_name_list.append(presentation.elearning)
			topic_list.append(presentation.topic)
			slide_list.append(presentation.slide)
			count += 1

		data = {"id":id_list,"presentation_name":presentation_name_list,"topic":topic_list,"slide":slide_list}
		df = pandas.DataFrame(data, columns=field_names)

		df = df.dropna()

		writer = ExcelWriter('Presentation-db.xlsx')
		df.to_excel(writer, 'Presentation', index=False)
		writer.save()

		path = "Presentation-db.xlsx"

		if os.path.exists(path):
			with open(path, "rb") as excel:
				data = excel.read()

			response = HttpResponse(data,
									content_type='application/vnd.ms-excel')
			response['Content-Disposition'] = 'attachment; filename="db_presentation.xlsx"'
		return response
		return HttpResponse("Success")






admin.site.register(Slide)
admin.site.register(ELearningSession)
admin.site.register(ELearningUserSession)
admin.site.register(ELearningUserAnswer)
admin.site.register(ELearningCorrection)
admin.site.register(ELearningRepetition)