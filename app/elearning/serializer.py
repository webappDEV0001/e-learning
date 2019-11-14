from rest_framework import serializers

from .models import ElearningUserSession


class ElearningUserSessionSerializer(serializers.ModelSerializer):
	elearning = serializers.StringRelatedField()
	user = serializers.StringRelatedField()

	class Meta:
		model = ElearningUserSession
		exclude = ('id',)
