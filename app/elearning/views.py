import datetime
from django.utils import timezone
import random
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, mixins
from rest_framework.response import Response

from .models import ELearning, ELearningUserSession, ELearningRepetition, ELearningCorrection, ELearningSession
from exam.models import Exam
from elearning.models import ELearningUserAnswer
from question.models import Question, Answer, ExamUserSession
from question.serializers import ExamUserSessionSerializer, ELearningUserSessionSerializer


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

	def retrieve(self, request, pk=None):
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
			rep_date_from = timezone.now().date()
			repetition = ELearningRepetition.objects.filter(session=eus, repeat_after__lte=rep_date_from, answered=False)

			if repetition:
				eus.phase = 1
				eus.save()
				context = {
					'object': eus,
					'question': repetition.first().question,
					'phase': 'repetitions',
					'left': repetition.count()
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
			if eus.seen_slides < slides.count():
				slide_to_show = list(slides.all())[eus.seen_slides]
				response = {
					'state': 'slide',
					'content': render_to_string('elearning/includes/_slide.html', {'slide': slide_to_show})
				}
				return Response(response)


			already_answered = list(ELearningUserAnswer.objects.filter(
				session=eus, session_number=eus.active_session_number).values_list('question', flat=True))

			# Get new questions from active session
			questions = eus.active_session.questions.exclude(pk__in=already_answered)

			# If no new questions or questions limit reached
			if not questions or len(already_answered) >= eus.n_questions:

				# Corrections Phase
				correction = ELearningCorrection.objects.filter(session=eus)
				if correction:
					eus.phase = 0
					eus.save()
					context = {
						'object': eus,
						'question': correction.first().question,
						'phase': 'corrections',
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
						'content': render_to_string('elearning/includes/_finished.html', {'next_session': next_session, 'obj': eus.elearning})
					}
				return Response(response)

			# Assign new question if not already assigned. Exclude already answered.
			if not eus.active_question:

				if eus.elearning.random_questions:
					question = random.choice(questions)
				else:
					question = questions.first()
				eus.active_question = question
				eus.save()

			else:
				question = eus.active_question

			eus.phase = 2
			eus.save()
			# Clean all answered repetitions
			ELearningRepetition.objects.filter(session=eus, answered=True).delete()

			context = {
				'object': eus,
				'question': question,
				'phase': 'new_questions',
				'left': int(eus.n_questions - len(already_answered))
			}
			response = {
					'state': 'question',
					'session': self.serializer_class(eus).data,
					'content': render_to_string('elearning/includes/_question.html', context)
			}
		elif eus.finished:
			# check if finish time is yesterday - if yes, level up session
			# if eus.finished.date() <= timezone.now().date():
				# print('next session!')
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
	def create_repetition(session, user_id, question_id):
		interval_dict = {
			0: 1,
			1: 3,
			2: 7,
			3: 21,
			4: 60
		}
		correctly_answered = ELearningUserAnswer.objects.filter(
			user_id=user_id, question_id=question_id, answer__correct=True).count()
		interval = interval_dict[min(correctly_answered, max(0, 4))]
		next_rep_date = (timezone.now() + datetime.timedelta(days=interval)).date()
		# Create repetition
		ELearningRepetition.objects.create(session=session, repeat_after=next_rep_date, question_id=question_id)

	@staticmethod
	def create_correction(session, question_id):
		return ELearningCorrection.objects.get_or_create(session=session, question_id=question_id)

	def update(self, request, pk=None):
		""" PUT: Answer sent by user """

		data = request.data
		eus = self.get_object()

		# Update seen_slides
		if data.get('slide', None) == 'seen':
			eus.seen_slides += 1
			eus.save()
			response = {
				'state': 'start',
				'session': self.serializer_class(eus).data,
			}
			return Response(response)

		correct = False
		answer_id = int(data.get('answer', None))
		answer = get_object_or_404(Answer, pk=answer_id)
		question_id = int(data.get('question', None))
		phase = str(data.get('phase', ''))
		eua = ELearningUserAnswer.objects.filter(session=eus, question_id=question_id).first()

		# If already answered or finished - return error
		if eua and phase == 'new_questions':
			return Response(status=400)

		if phase in ['new_questions', 'repetitions']:
			eua = ELearningUserAnswer.objects.create(
				session=eus,
				session_number=eus.active_session_number,
				question_id=question_id,
				answer=answer,
				user_id=request.user.id
			)
			# Mark old repetition after answer
			if phase == 'repetitions':
				ELearningRepetition.objects.filter(session=eus, question_id=question_id).update(answered=True)

			if eua.answer.correct:
				self.create_repetition(eus, request.user.id, question_id)
				correct = True
			else:
				self.create_repetition(eus, request.user.id, question_id)
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
				'content': render_to_string('exam/includes/_correct.html')
			}
		else:
			response = {
				'correct': 'false',
				'content': render_to_string('exam/includes/_false.html')
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