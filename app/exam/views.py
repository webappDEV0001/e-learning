import random
from django.db.models import Count
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, mixins
from rest_framework.response import Response

from .models import Exam
from elearning.models import ELearningUserSession
from question.models import Question, ExamUserSession, ExamUserAnswer
from question.serializers import ExamUserSessionSerializer
from exam.serializers import ExamSerializer


def about(request):
    return render(request, 'about.html')

def solutions(request):
    return render(request, 'solutions.html')

def contact(request):
    return render(request, 'contact.html')

def careers(request):
    return render(request, 'careers.html')
	

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
		qs = super(ExamListView, self).get_queryset()
		return qs

	def get_context_data(self, **kwargs):
	    context = super().get_context_data(**kwargs)
	    context['exams'] = self.get_queryset().filter(exam_type=Exam.EXAM)
	    context['e_user_sessions'] = list(ELearningUserSession.objects.filter(user=self.request.user) \
	    	.values_list('elearning', flat=True))
	    context['elearnings'] = self.get_queryset().filter(exam_type=Exam.ELEARNING)
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
