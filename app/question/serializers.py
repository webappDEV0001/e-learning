import pytz
import datetime
from django.utils import timezone
from rest_framework import serializers

from .models import ExamUserSession
from elearning.models import ELearningUserSession


class ExamUserSessionSerializer(serializers.ModelSerializer):
	exam = serializers.StringRelatedField()
	user = serializers.StringRelatedField()
	stop_time = serializers.DateTimeField()
	seconds_left = serializers.SerializerMethodField()

	class Meta:
		model = ExamUserSession
		fields = ['id', 'exam', 'user', 'stop_time', 'seconds_left']

	def get_seconds_left(self, obj):
		left = (datetime.datetime.now(tz=pytz.UTC) - obj.stop_time)
		return left.seconds

class ELearningUserSessionSerializer(serializers.ModelSerializer):
	exam = serializers.StringRelatedField()
	user = serializers.StringRelatedField()

	class Meta:
		model = ELearningUserSession
		fields = '__all__'
