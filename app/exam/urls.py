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
	path('download-files/<str:slug>/', DownloadFileView.as_view(),name='download-files'),
	path('presentation-slides/', PresentationSlideShow.as_view(),name='presentation-slides'),
	path('score-reauthentication/', ExamScoreReauthentication.as_view(),name='score-reauthentication'),
    path('api/', include(router.urls)),
]
