import random

from django.contrib import messages
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets
from rest_framework.response import Response
import pandas
from exam.forms import ExamImportForm

from question.models import Answer
from .models import Exam
from elearning.models import ELearningUserSession,ELearning
from question.models import Question, ExamUserSession, ExamUserAnswer
from question.serializers import ExamUserSessionSerializer
from django.contrib.auth.mixins import AccessMixin
import os
from config.common import *


def about(request):
    return render(request, 'about.html')

def solutions(request):
    return render(request, 'solutions.html')

def contact(request):
    return render(request, 'contact.html')

def careers(request):
    return render(request, 'careers.html')

class OurBaseView(TemplateView):
    template_name = "exam/ifrs-17-e-learning.html"

class ExamView(DetailView):
    model = Exam


class ExamUserSessionViewSet(viewsets.GenericViewSet):
    """ Viewset for managing movie objects with details from omdbapi.com.
        Results are saved in database for limiting external API requests.
    """
    queryset = ExamUserSession.objects.all()
    serializer_class = ExamUserSessionSerializer
    pk_url_kwarg = 'exam.pk'

    def get_object(self):
        return self.get_queryset().filter(exam__pk=self.kwargs['pk'], finished=None).first()

    def get_queryset(self):
        qs = super(ExamUserSessionViewSet, self).get_queryset()
        qs.filter(user=self.request.user, exam__exam_type=Exam.EXAM)
        return qs

    def retrieve(self, request, pk=None):
        """ GET: Get active exam user session """
        exam = get_object_or_404(Exam, pk=pk, exam_type=Exam.EXAM)
        eus = ExamUserSession.objects.filter(exam_id=pk, finished=None)
        exam_obj = Exam.objects.get(id=pk)

        if not eus.exists():
            response = {
                'state': 'init',
                'content': render_to_string('exam/includes/_exam_start.html', {'object': exam})
            }
            return Response(response)

        eus = eus.first()
        if not eus.finished and eus.no_time_left:
            eus.stop_test()
            response = {
                'state': 'no_time_left',
                'session': self.serializer_class(eus).data,
                'content': render_to_string('exam/includes/_exam_time_passed.html')
            }

        else:
            # Assign new question if not already assigned. Exclude already answered.
            if not eus.active_question:

                already_answered = list(ExamUserAnswer.objects.filter(session=eus)\
                    .values_list('question', flat=True))

                questions = Question.objects.filter(exam=eus.exam).exclude(pk__in=already_answered)

                # If no questions left or questions limit reached - end exam
                if not questions or len(already_answered) >= eus.n_questions:
                    eus.stop_test()
                    response = {
                        'state': 'end',
                        'session': self.serializer_class(eus).data,
                        'content': render_to_string('exam/includes/_exam_end.html')
                    }
                    return Response(response)

                # Get random question
                question = random.choice(questions)
                eus.active_question = question
                eus.save()
            else:
                question = eus.active_question

            context = {
                'object': eus,
                'show_answers': exam_obj.show_answers,
                'question': question
            }
            response = {
                'state': 'question',
                'session': self.serializer_class(eus).data,
                'content': render_to_string('exam/includes/_question.html', context)
            }
        return Response(response)

    def partial_update(self, request, pk=None):
        """ PATCH: Start exam """
        exam = get_object_or_404(Exam, pk=pk)
        eus, crt = ExamUserSession.objects.get_or_create(exam=exam, user=request.user, finished=None)
        if crt:
            eus.start_test()
            response = {
                'state': 'start',
                'session': self.serializer_class(eus).data,
            }
            return Response(response)
        return Response(status=400)

    def update(self, request, pk=None):
        """ PUT: Answer sent by user """

        data = request.data
        eus = self.get_object()
        answer_id = int(data.get('answer', None))
        question_id = int(data.get('question', None))

        eua = ExamUserAnswer.objects.filter(session=eus, question_id=question_id, session__finished=None).first()

        # If already answered, finished or no time left - return error
        if eua or eus.finished or eus.no_time_left:
            return Response(status=400)

        eua = ExamUserAnswer.objects.create(
            session=eus,
            question_id=question_id,
            answer_id=answer_id,
            user_id=request.user.id
        )
        eus.active_question = None
        eus.save()
        if eua.answer.correct:
            response = {
                'correct': 'true',
                'content': render_to_string('exam/includes/_correct.html')
            }
        else:
            response = {
                'correct': 'false',
                'content': render_to_string('exam/includes/_false.html')
            }
        if eua.answer.question.explanation:
            response['explanation'] = eua.answer.question.explanation
        return Response(response)


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exam/exam_list.html'


    def get_queryset(self):
        if self.request.user.is_demo:
            qs = super(ExamListView, self).get_queryset().filter(demo=True)
        else:
            qs = super(ExamListView, self).get_queryset()
        return qs

    def get_material_list(self):

        path = os.path.join(STATICFILES_DIRS[0],"materials")  # insert the path to your directory
        files = os.listdir(path)
        return files

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exams'] = self.get_queryset().filter(exam_type=Exam.EXAM)
        context['e_user_sessions'] = list(ELearningUserSession.objects.filter(user=self.request.user) \
            .values_list('elearning', flat=True))

        memory_force = ELearningUserSession.objects.filter(user=self.request.user) \
                                          .values_list('exam__name','memory_force')

        context['memory_force'] =  dict(memory_force)

        context['material_files'] = self.get_material_list()

        if self.request.user.is_demo:
            context['elearnings'] = ELearning.objects.filter(demo=True, exam_type="elearning")
        else:
            context['elearnings'] = ELearning.objects.filter(exam_type="elearning")
        # context['memory_force'] = ELearningUserSession.objects.filter(user=self.request.user)
        # context['elearnings_ns'] = self.get_queryset().filter(exam_type=Exam.ELEARNING_NS)
        return context



class ExamScoresListView(LoginRequiredMixin, ListView):
    model = ExamUserSession
    template_name = 'exam/exam_score_list.html'

    def get_queryset(self):
        qs = super(ExamScoresListView, self).get_queryset().filter(
            finished__isnull=False,
            user=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam_sessions'] = self.get_queryset().filter(exam__exam_type=Exam.EXAM)
        context['elearning_sessions'] = ELearningUserSession.objects.filter(user=self.request.user)
        return context


class ExamScoreView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        eus = get_object_or_404(ExamUserSession, pk=kwargs['pk'])
        response = render(request, 'exam/includes/_score.html', {
            'session': ExamUserSessionSerializer(eus).data,
            'score': eus.get_score,
            'questions': eus.n_questions,
            'correct': eus.count_correct_answers
        })
        return response



class AdminOrStaffLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is staff or admin"""

    # ---------------------------------------------------------------------------
    # dispatch
    # ---------------------------------------------------------------------------
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class ExamImportView(AdminOrStaffLoginRequiredMixin, FormView):
    """
    This class handle the import data of exam
    """

    form_class = ExamImportForm
    template_name = "exam/exam_import_form.html"

    def get_success_url(self):
        success_url = reverse_lazy('admin:exam_exam_changelist')
        return success_url

    def form_valid(self, form):
        csv_file = form.cleaned_data.get("csv_file")
        df = pandas.read_excel(csv_file)
        df.dropna(how="all", inplace=True)
        print(df)

        for i in range(len(df)):
            try:
                exam_name = df['quiz'][i]
                q_category = df['category'][i]
                q_subcategory = df['sub_category'][i]
                exam, crt = Exam.objects.get_or_create(name=exam_name, exam_type=Exam.EXAM)
                q_text = df['content'][i]
                q_explanation = df['explanation'][i]
                correct_answer_text = df['correct'][i]
                wrong_1 = df['answer1'][i]
                wrong_2 = df['answer2'][i]
                wrong_3 = df['answer3'][i]
                if q_text != "n" and correct_answer_text != "n" and str(q_text) != "nan" and q_text != " ":
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
            except:
                print("Skip row" + i)
        messages.info(self.request, "your exam data imported successfully.")
        return FormView.form_valid(self, form)

    def get_context_data(self, **kwargs):

        context = super(ExamImportView, self).get_context_data()
        context["opts"] = Exam._meta
        return context



class DownloadFileView(View):
    template_name = "exam/exam_list.html"

    def get(self, request, *args, **kwargs):

        # path = "assets/materials"
        path = os.path.join(STATICFILES_DIRS[0],"materials")
        file_path = os.path.join(path,kwargs.get('slug'))
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
        raise Http404






