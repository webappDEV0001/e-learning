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
from pandas import ExcelWriter
import os


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
        field_names = ['id','quiz','category','subcategory','content','explanation','correct','answer1',
                       'answer2','answer3']

        id_list=[]
        exam_name_list=[]
        category=[]
        sub_category=[]
        content = []
        explanation_list = []
        correct=[]
        answer1=[]
        answer2=[]
        answer3=[]
        for q in question_objects:
            try:
                correct_answer = Answer.objects.filter(question=q['id'], correct=True).values_list('text')
                other_answers = Answer.objects.filter(question=q['id'], correct=False).values_list('text')

                # print(correct_answer[0][0], "correct_answers")
                # print(other_answers[1][0], "other_answers")
                exam = Exam.objects.filter(id=q['exam_id']).values()
                # count_answer=1
                id_list.append(q['id'])
                exam_name_list.append(exam[0]['name'])
                category.append(q['category'])
                sub_category.append(q['sub_category'])
                content.append(q['text'])
                explanation_list.append(q['explanation'])
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

        data={'id':id_list,'quiz':exam_name_list,'category':category,'subcategory':sub_category,
              'content':content,'explanation':explanation_list,'correct':correct,'answer1':answer1,
              'answer2':answer2,'answer3':answer3}
        df = pandas.DataFrame(data, columns=field_names)

        df = df.dropna(axis=1, how='all')

        writer = ExcelWriter('Exam-test.xlsx')
        df.to_excel(writer, 'Exam', index=False)
        writer.save()

        path="Exam-test.xlsx"

        if os.path.exists(path):
            with open(path, "rb") as excel:
                data = excel.read()

            response = HttpResponse(data,
                                    content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="db_exam.xlsx"'
            return response


        # df.to_csv(response,sep="\t",index=False)
            # row = writer.writerow([getattr(obj[field], field) for field in field_names])

