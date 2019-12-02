from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path
from question.models import Question, Answer
from exam.models import Exam
import pandas
from django import forms
from exam.forms import ExamImportForm
from exam.views import ExamImportView


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    change_list_template = "exam/examadmin_changelist.html"

    def get_urls(self):
        urls =  super(ExamAdmin, self).get_urls()
        my_urls = [
            path('import-csv/', self.admin_site.admin_view(ExamImportView.as_view()),
                 name="import-csv"),
            # path('import-csvs/', self.import_csv),
            path('export-csv/', self.export_csv),
        ]
        return my_urls + urls


    def export_csv(self, request):
        question_objects = Question.objects.all().values()
        # meta = self.model._meta
        # field_names = ['id','quiz','category','subcategory','figure','content','explanation','correct','answer1',
                       # 'answer2','answer3']

        df=pandas.DataFrame()

        #
        # response = HttpResponse(content_type='text/csv')
        # response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        # writer = csv.writer(response)
        #
        #
        # writer.writerow(field_names)


        for q in question_objects:
            a=Answer.objects.filter(question=q['id']).values()
            exam = Exam.objects.filter(id=q['exam_id']).values()
            count_answer=1
            for i in range(0,3):
                if a[i]['correct']:
                    df['correct']=a[i]
                else:
                    key='answer'+str(count_answer)
                    df[key]=a[i]
                    count_answer += 1

            df['id'] = q['id']
            df['quiz'] = exam[0]['name']
            df['category'] = q['category']
            df['sub_category'] = q['sub_category']
            df['figure'] = 'n'
            df['content'] = q['text']
            df['explanation'] = q['explanation']
            # df['correct']
            # df['answer1']
            # df['answer2']
            # df['answer3']

        response = HttpResponse(df, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="db_exam.csv"'
        df.to_csv(path_or_buf=response, sep=';', float_format='%.2f', index=False, decimal=",")
        return response
            # row = writer.writerow([getattr(obj[field], field) for field in field_names])

