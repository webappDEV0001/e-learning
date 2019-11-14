from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'examusersession', ExamUserSessionViewSet, basename='examusersession')

urlpatterns = [
	path('<int:pk>-<str:slug>/', ExamView.as_view() , name='exam'),
	path('scores/', ExamScoresListView.as_view() , name='exam-scores'),
	path('scores/<int:pk>/', ExamScoreView.as_view() , name='exam-score'),
    path('api/', include(router.urls)),
]
