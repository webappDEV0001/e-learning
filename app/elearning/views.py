import datetime
import os
import time
from dateutil import tz
import pandas
import pdfkit
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse_lazy, reverse
from django.utils import timezone
import random
from django.views.generic.base import View, RedirectView
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from config.common import TEMP_DIR

from elearning.forms import ElearningImportForm

from elearning.forms import PresentationImportForm
from .models import ELearning, ELearningUserSession, ELearningRepetition, ELearningCorrection, ELearningSession, Slide, \
    Presentation
from exam.models import Exam
from elearning.models import ELearningUserAnswer
from question.models import Question, Answer, ExamUserSession
from question.serializers import ExamUserSessionSerializer, ELearningUserSessionSerializer

from config.common import MEDIA_ROOT


def repitiion_date_change(request):
    user_session = request.GET.get('user_session','')
    back_days_count = request.GET.get('back_days_count',0)
    repitition_objs = ELearningRepetition.objects.filter(session=user_session)

    eus = ELearningUserSession.objects.get(id=user_session)
    eus.started = eus.started - datetime.timedelta(days=int(back_days_count))
    eus.save()

    for repitition in repitition_objs:
        repitition.repeat_after = repitition.repeat_after - datetime.timedelta(days=int(back_days_count))
        repitition.save()
    return HttpResponse("Success")


class ELearningView(DetailView):
    model = ELearning
    template_name = 'exam/elearning_detail.html'


class ELearningUserSessionViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):

    queryset = ELearningUserSession.objects.all()
    serializer_class = ELearningUserSessionSerializer
    pk_url_kwarg = 'elearning.pk'

    def get_object(self):
        return self.get_queryset().filter(exam__pk=self.kwargs['pk']).first()


    def get_queryset(self):
        qs = super(ELearningUserSessionViewSet, self).get_queryset()
        # qs = qs.filter(exam_id=self.kwargs['pk'], user=self.request.user)\
        #   .filter(exam__exam_type__in=[Exam.ELEARNING, Exam.ELEARNING_NS])
        qs = qs.filter(exam_id=self.kwargs['pk'], user=self.request.user)\
        .filter(exam__exam_type__in=[Exam.ELEARNING])
        return qs

    def retrieve(self, request, pk=None,mf=None):
        """ GET: Get or create exam user session """
        # eus, crt = ELearningUserSession.objects.get_or_create(exam_id=pk, elearning_id=pk, user=request.user)
        # get_object_or_404(Exam, pk=pk, exam_type__in=[Exam.ELEARNING, Exam.ELEARNING_NS])
        eus, crt = ELearningUserSession.objects.get_or_create(exam_id=pk, elearning_id=pk, user=request.user)
        get_object_or_404(Exam, pk=pk, exam_type__in=[Exam.ELEARNING])

        if not eus.started:

            response = {
                'state': 'init',
                'session': self.serializer_class(eus).data,
                'content': render_to_string('elearning/includes/_elearning_start.html', {'object': eus.exam})
            }

        elif eus.started and not eus.finished:

            # Repetitions Phase
            user_timezone = tz.gettz(request.user.timezone)
            rep_date_from = timezone.now().astimezone(user_timezone).date()
            repetition = ELearningRepetition.objects.filter(session=eus, repeat_after__lte=rep_date_from, answered=False)

            if repetition:
                # repetition get correct answers count

                #Delete corrections from previous session
                ELearningCorrection.objects.filter(session=eus).delete()

                correct_answered_count = ELearningUserAnswer.objects.filter(session=eus,
                     question=repetition.first().question, answer__correct=True).count()


                eus.phase = 1
                eus.save()
                exam_obj = Exam.objects.get(id=pk)

                already_answered_repetition = ELearningRepetition.objects.filter(session=eus, repeat_after__lte=rep_date_from,
                                                                answered=True).count()

                already_answered = list(ELearningUserAnswer.objects.filter(
                    session=eus, session_number=eus.active_session_number, phase="new_questions").values_list(
                    'question', flat=True))

                new_questions_left_current_session = eus.active_session.questions.exclude(pk__in=already_answered)

                if not new_questions_left_current_session or len(already_answered) >= eus.n_questions:
                    if already_answered_repetition == 0:
                        ELearningCorrection.objects.filter(session=eus).delete()
                        next_session = ELearningSession.objects.filter(
                                elearning=eus.exam.elearning, number=int(eus.active_session_number + 1)).first()
                        if next_session:
                                eus.active_session = next_session
                                eus.seen_slides = 0
                                eus.save()

                    # print("session updated to",eus.active_session_number)

                context = {
                    'object': eus,
                    'question': repetition.first().question,
                    'phase': 'repetitions',
                    'left': repetition.count(),
                    'show_answers': exam_obj.show_answers,
                    'correct_answered_count':correct_answered_count
                }
                response = {
                    'state': 'question',
                    'session': self.serializer_class(eus).data,
                    'content': render_to_string('elearning/includes/_question.html', context)
                }
                return Response(response)

            # Show slides
            eus.phase = 3
            eus.save()
            slides = eus.active_session.slides

            # print("eus active session",eus.active_session_number)

            if eus.seen_slides < slides.count():
                slide_to_show = list(slides.all())
                seen_slide = eus.seen_slides + 1
                total_slides = slides.count()

                if eus.seen_slides == 0 :
                    previous_slide = 0
                else:
                    previous_slide = 1

                response = {
                    'state': 'slide',
                    'content': render_to_string('elearning/includes/_slide.html', {'slides': slide_to_show,
                                                                                   'previous_slide':previous_slide,
                                                                                   "object":eus,
                                                                                   "seen_slide":seen_slide,
                                                                                   "total_slides":total_slides})
                }
                # response = {'state':'slide','previous_slide':previous_slide}
                return Response(response)

            already_answered = list(ELearningUserAnswer.objects.filter(
                session=eus, session_number=eus.active_session_number,phase="new_questions").values_list('question', flat=True))

            # Get new questions from active session
            questions = eus.active_session.questions.exclude(pk__in=already_answered)
            # If no new questions or questions limit reached
            if not questions or len(already_answered) >= eus.n_questions:
                # Corrections Phase
                correction = ELearningCorrection.objects.filter(session=eus)

                if correction :
                    eus.phase = 0
                    eus.save()
                    exam_obj = Exam.objects.get(id=pk)
                    context = {
                        'object': eus,
                        'question': correction.first().question,
                        'phase': 'corrections',
                        'show_answers': exam_obj.show_answers,
                        'left': correction.count()
                    }
                    response = {
                        'state': 'question',
                        'session': self.serializer_class(eus).data,
                        'content': render_to_string('elearning/includes/_question.html', context)
                    }
                else:
                    next_session = ELearningSession.objects.filter(
                        elearning=eus.exam.elearning, number=int(eus.active_session_number+1)).first()
                    if next_session:
                        eus.active_session = next_session
                        eus.seen_slides = 0
                        eus.save()
                    response = {
                        'state': 'end',
                        'session': self.serializer_class(eus).data,
                        'content': render_to_string('elearning/includes/_finished.html', {'next_session': next_session,
                                                                                          'obj': eus.elearning})
                    }
                return Response(response)

            # Assign new question if not already assigned. Exclude already answered.
            if not eus.active_question:
                # if eus.elearning.random_questions:
                #     question = random.choice(questions)
                # else:
                question = questions.first()
                eus.active_question = question
                eus.save()
            else:
                question = eus.active_question


            eus.phase = 2
            eus.save()
            exam_obj = Exam.objects.get(id=pk)
            # Clean all answered repetitions
            ELearningRepetition.objects.filter(session=eus, answered=True).delete()
            context = {
                'object': eus,
                'question': question,
                'phase': 'new_questions',
                'show_answers': exam_obj.show_answers,
                'left':int(len(questions))
                # 'left': int(eus.n_questions - len(already_answered))
            }
            response = {
                    'state': 'question',
                    'session': self.serializer_class(eus).data,
                    'content': render_to_string('elearning/includes/_question.html', context)
            }
        elif eus.finished:
            # check if finish time is yesterday - if yes, level up session
            # if eus.finished.date() <= timezone.now().date():
            response = {
                'state': 'end',
                'session': self.serializer_class(eus).data,
                'content': render_to_string('elearning/includes/_finished.html')
            }
            return Response(response)

        return Response(response)

    def partial_update(self, request, pk=None):
        """ PATCH: Start exam """
        eus = self.get_object()
        if not eus.started:
            eus.start_test()
        response = {
                'state': 'start',
                'session': self.serializer_class(eus).data,
        }
        return Response(response)

    @staticmethod
    def create_repetition(session, user, question_id,answered=False):
        if session.memory_force == 'low':
            interval_dict = {
                0: 1,
                1: 2,
                2: 5,
                3: 14,
                4: 30
            }
        elif session.memory_force == 'high':
            interval_dict = {
                0: 1,
                1: 4,
                2: 10,
                3: 30,
                4: 90
            }
        else:
            interval_dict = {
                0: 1,
                1: 3,
                2: 7,
                3: 21,
                4: 60
            }

        correctly_answered = ELearningUserAnswer.objects.filter(
            user_id=user.id, question_id=question_id, answer__correct=True).count()
        interval = interval_dict[min(correctly_answered, max(0, 4))]

        user_timezone = tz.gettz(user.timezone)
        next_rep_date = (timezone.now().astimezone(user_timezone) + datetime.timedelta(days=interval)).date()
        # Create repetition
        ELearningRepetition.objects.create(session=session, repeat_after=next_rep_date, question_id=question_id)

    @staticmethod
    def create_correction(session, question_id):
        return ELearningCorrection.objects.get_or_create(session=session, question_id=question_id)

    def update(self, request, pk=None,mu=None):
        """ PUT: Answer sent by user """

        data = request.data
        eus = self.get_object()
        correct_answered_count = 0

        #Update memory force
        if data.get('memory_force',None) == 'True':
            eus.memory_force = data.get('memory_force_value').lower()
            eus.save()
            return Response("Value Updated Successfully")

        # Update seen_slides
        if data.get('slide', None) == 'seen':
            eus.seen_slides += 1
            eus.save()
            slides = eus.active_session.slides
            slide_to_show = list(slides.all())[eus.seen_slides:]
            total_count = len(slide_to_show)
            if total_count == 0:
                response = {
                    'state': 'start',
                    'session': self.serializer_class(eus).data,
                    'full_screen_mode': data.get('full_screen_mode', False)
                }
            else:
                response = {
                    'state': 'start_slide',
                    # 'session': self.serializer_class(eus).data,
                    'full_screen_mode':data.get('full_screen_mode',False)
                }
            return Response(response)

        elif data.get('slide', None) == 'previous_seen':
            eus.seen_slides -= 1
            eus.save()
            response = {
                'state': 'start_prev_slide',
                'session': self.serializer_class(eus).data,
                'full_screen_mode': data.get('full_screen_mode', False)
            }
            return Response(response)

        correct = False

        #Delete that questions from repetitions
        if data.get('forget-question',None) != None:
            question_id = int(data.get('question', None))
            ELearningRepetition.objects.filter(session=eus, question_id=question_id).delete()

            response = {
                'status':"Forget question successfully",
            }
            return Response(response)

        answer_id = int(data.get('answer', None))
        answer = get_object_or_404(Answer, pk=answer_id)
        question_id = int(data.get('question', None))
        phase = str(data.get('phase', ''))
        eua = ELearningUserAnswer.objects.filter(session=eus, question_id=question_id).first()

        # If already answered or finished - return error
        if eua and phase == 's':
            return Response(status=400)

        if phase in ['new_questions', 'repetitions']:
            eua = ELearningUserAnswer.objects.create(
                    session=eus,
                    session_number=eus.active_session_number,
                    question_id=question_id,
                    answer=answer,
                    user_id=request.user.id,
                    phase=phase
                )
            # Mark old repetition after answer
            if phase == 'repetitions':
                ELearningRepetition.objects.filter(session=eus, question_id=question_id).update(answered=True)

                correct_answered_count = ELearningUserAnswer.objects.filter(session=eus,
                                                                            question__id=question_id,
                                                                            answer__correct=True).count()

                print("correct_answered_count repititions", correct_answered_count)

            if eua.answer.correct:
                    self.create_repetition(eus, request.user, question_id)
                    correct = True
            else:
                    self.create_repetition(eus, request.user, question_id)
                    self.create_correction(eus, question_id)

        elif phase == 'corrections':
            correction = ELearningCorrection.objects.get(session=eus, question=answer.question)
            old_pk = correction.pk
            if answer.correct:
                correction.delete()
                correct = True
            else:
                correction.pk = None
                correction.save()
                ELearningCorrection.objects.get(pk=old_pk).delete()



        if correct:
            response = {
                'correct': 'true',
                'content': render_to_string('exam/includes/_correct.html'),
                'correct_answered_count':correct_answered_count
            }
        else:
            response = {
                'correct': 'false',
                'content': render_to_string('exam/includes/_false.html'),
                'correct_answered_count':correct_answered_count
            }

        if answer.question.explanation:
            response['explanation'] = answer.question.explanation

        eus.active_question = None
        eus.save()
        return Response(response)


class ELearningProgressListView(LoginRequiredMixin, ListView):
    model = ELearningUserSession
    template_name = 'elearning/elearning_progress.html'

    def get_queryset(self):
        qs = super(ELearningProgressListView, self).get_queryset().filter(user=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['elearning_sessions'] = ELearningUserSession.objects.filter(user=self.request.user)
        return context


class ElearningResetProgress(RedirectView):
    template_name = "elearning/elearning_progress.html"

    def get_redirect_url(self, *args, **kwargs):
        session_obj = get_object_or_404(ELearningUserSession, id=kwargs['pk'])
        session_obj.delete()
        return reverse("elearning-progress")

class DownloadCertificateView(View):
    template_name = "elearning/download-certificate.html"

    # -------------------------------------------------------------------------------
    # confirm_dir_exists
    # -------------------------------------------------------------------------------
    def confirm_dir_exists(self, dir_path):
        """
        Makes sure whether the directory path given exists. If it does not,
        then it creates one and returns the path.
        """
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        return dir_path

    def confirm_file_exists(self, file_path):
        """
        Makes sure whether the file path given exists. If it does not, then it
        creates one and returns the path.
        """

        if not os.path.exists(file_path):
            with open(file_path, "w+") as f:
                f.write('')

        return file_path

    def get_temp_path(self, filename_initials):
        self.confirm_dir_exists(TEMP_DIR)

        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d-%H%M%S')
        temp_file_path = os.path.join(TEMP_DIR, '%s-%s.pdf' % (filename_initials, timestamp))

        self.confirm_file_exists(temp_file_path)

        return temp_file_path

    def create_pdf(self, context, template, filename_initials, request):
        options = {
            'page-size': 'A4',
            'margin-top': '0in',
            'margin-right': '0in',
            'margin-bottom': '0in',
            'margin-left': '0in',
            'encoding': "UTF-8",
            'page-height': '50in',
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
        }
        template = loader.get_template(self.template_name)
        html_string = template.render(context=context, request=request)
        file_path = self.get_temp_path(filename_initials)
        # TODO: use exception handling here. and catch in `get` method to redirect to error page in case of some error
        pdfkit.from_string(html_string, file_path,
                           options=options)

        return file_path

    # ---------------------------------------------------------------------------
    # render_to_pdf_response
    # ---------------------------------------------------------------------------
    def render_to_pdf_response(self, context, template, filename_initials, request=None):
        file = self.create_pdf(context, template, filename_initials, request=request)
        filename = os.path.basename(file)

        fs = FileSystemStorage(file)

        with fs.open(file) as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="%s"' % filename
            return response

    def get(self, request, *args, **kwargs):

        user_session = ELearningUserSession.objects.get(user=self.request.user, elearning__slug=kwargs.get('slug'))
        completed_on = timezone.now().date().strftime("%m.%d.%y")
        try:
            total_hours: int = int((timezone.now() - user_session.started).total_seconds()//3600)
        except:
            total_hours = 4

        context = {
            "username": user_session.user.username,
            "surname": user_session.user.surname,
            "training_name": kwargs.get('slug'),
            "number": user_session.elearning.certificate_count,
            "completed_on": completed_on,  #TODO: user_session.finished.date().strftime("%m.%d.%y")
            "total_hours": total_hours,
        }
        user_session.elearning.certificate_count += 1
        user_session.elearning.save()
        return self.render_to_pdf_response(context, self.template_name, kwargs.get('slug'))

class AdminOrStaffLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is staff or admin"""

    # ---------------------------------------------------------------------------
    # dispatch
    # ---------------------------------------------------------------------------
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

class ElearningImportView(AdminOrStaffLoginRequiredMixin, FormView):
    """
    This class handle the import data of elearning
    """

    form_class = ElearningImportForm
    template_name = "elearning/elearning_import_form.html"

    def get_success_url(self):
        success_url = reverse_lazy('admin:elearning_elearning_changelist')
        return success_url

    def form_valid(self, form):
        from os import path
        csv_file = form.cleaned_data.get("csv_file")
        df = pandas.read_excel(csv_file)
        df.dropna(how="all", inplace=True)
        check_dict = {}
        session_list = []
        check_dict2 = {}
        session_list2 = []
        previous_session = 0
        previous_elearning = 0

        for i in range(len(df)):

            try:
                if df['quiz'][i] in check_dict.keys():
                    check_dict[df['quiz'][i]] = session_list
                else:
                    session_list.clear()
                    check_dict.clear()
                    check_dict[df['quiz'][i]] = session_list

                if df['quiz'][i] in check_dict2.keys():
                    check_dict2[df['quiz'][i]] = session_list2
                else:
                    session_list2.clear()
                    check_dict2.clear()
                    check_dict2[df['quiz'][i]] = session_list2

                exam_name = df['quiz'][i]
                q_category = df['category'][i]
                q_subcategory = df['sub_category'][i]
                q_figure = df['figure'][i]

                #elearning object creating....
                if df['session'][i] in check_dict[df['quiz'][i]]:
                    # session already exist
                    elearn = ELearning.objects.get(id=previous_elearning,name=exam_name, exam_type="elearning")
                else:
                    try:
                        elearn = ELearning.objects.filter(name=exam_name, exam_type="elearning").order_by('-id')[0]
                    except:
                        elearn = ELearning.objects.create(name=exam_name, exam_type="elearning")
                    previous_elearning = elearn.id
                    session_list.append(df['session'][i])
                    # session_id_list.append()

                q_text = df['content'][i]
                q_explanation = df['explanation'][i]
                correct_answer_text = df['correct'][i]
                wrong_1 = df['answer1'][i]
                wrong_2 = df['answer2'][i]
                wrong_3 = df['answer3'][i]

                #slides object creating....
                slide_path = os.path.join(MEDIA_ROOT, q_figure.strip())
                if path.exists(slide_path):
                    slide_obj,crt = Slide.objects.get_or_create(elearning=elearn, image=q_figure.strip())

                #Questions object creating....
                if q_text != "n" and correct_answer_text!= "n" and str(q_text)!= "nan" and q_text!= " ":
                    q, crt = Question.objects.get_or_create(exam=elearn, text=q_text)
                    if crt:
                        q.explanation = q_explanation
                        q.text = q_text
                        q.category = q_category
                        q.subcategory = q_subcategory
                        q.save()

                    #Answer object creating....
                    Answer.objects.get_or_create(question=q, text=correct_answer_text, correct=True)
                    Answer.objects.get_or_create(question=q, text=wrong_1)
                    Answer.objects.get_or_create(question=q, text=wrong_2)
                    Answer.objects.get_or_create(question=q, text=wrong_3)


                try:
                    slides = Slide.objects.filter(id=slide_obj.id)
                    slides = list(slides)
                except:
                    print("Skip slide")
                    slides = []
                if q_text != "n" and correct_answer_text != "n" and str(q_text) != "nan" and q_text != " ":
                    question = Question.objects.filter(exam=elearn,id=q.id)
                    question = list(question)

                # elearning object creating....
                if df['session'][i] in check_dict2[df['quiz'][i]]:
                    # session already exist
                    elearn_session = ELearningSession.objects.get(id=previous_session,elearning=elearn)
                else:
                    elearn_session = ELearningSession.objects.filter(elearning=elearn,number=df['session'][i]).order_by("-id")
                    if len(elearn_session) == 0:
                        # complete new_session start
                        elearn_session = ELearningSession.objects.create(elearning=elearn,number=df['session'][i])
                    else:
                        previous_session = elearn_session[0].id + 1
                        #new session start here
                        elearn_session,crt = ELearningSession.objects.get_or_create(id=previous_session,elearning=elearn,number=df['session'][i])

                elearn_session.save()

                previous_slides_list = list(elearn_session.slides.all())
                previous_slides_list += slides
                if q_text != "n" and correct_answer_text != "n" and str(q_text) != "nan" and q_text != " ":
                    previous_questions = list(elearn_session.questions.all())
                    previous_questions += question
                    elearn_session.questions.add(*previous_questions)
                elearn_session.slides.add(*previous_slides_list)

                previous_session = elearn_session.id
                session_list2.append(df['session'][i])

            except:
                print("Skip row")
        messages.info(self.request, "your elearning data imported successfully.")
        return FormView.form_valid(self, form)

    def get_context_data(self, **kwargs):

        context = super(ElearningImportView, self).get_context_data()
        context["opts"] = ELearning._meta
        return context


class PresentationImportView(AdminOrStaffLoginRequiredMixin, FormView):
    """
    This class handle the import data of presentation
    """

    form_class = PresentationImportForm
    template_name = "elearning/presentation_import_form.html"

    def get_success_url(self):
        success_url = reverse_lazy('admin:elearning_presentation_changelist')
        return success_url

    def form_valid(self, form):
        from os import path
        csv_file = form.cleaned_data.get("csv_file")
        df = pandas.read_excel(csv_file)
        df.dropna(how="all", inplace=True)

        for i in range(len(df)):
            try:
                presentation_name = df['presentation_name'][i]
                topic = df['topic'][i]
                slide = df['slide'][i]
                presentation, crt = Presentation.objects.get_or_create(elearning=presentation_name, topic=topic,slide=slide)
            except:
                print("Skip row")
        messages.info(self.request, "your presentation data imported successfully.")
        return FormView.form_valid(self, form)

    def get_context_data(self, **kwargs):

        context = super(PresentationImportView, self).get_context_data()
        context["opts"] = Presentation._meta
        return context