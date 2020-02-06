from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
import pandas
from pandas import ExcelWriter
from .views import PresentationImportView
from .models import Presentation
import os



# Register your models here.
@admin.register(Presentation)
class AdminPresentation(admin.ModelAdmin):
	change_list_template = "presentation_admin_changelist.html"

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