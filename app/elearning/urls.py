from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'elearningsession', ELearningUserSessionViewSet, basename='elearningsession')

urlpatterns = [
	path('<int:pk>-<str:slug>/', ELearningView.as_view() , name='elearning'),
	path('progress/', ELearningProgressListView.as_view() , name='elearning-progress'),
	path('generate-certificate/<str:slug>/', DownloadCertificateView.as_view(),name='generate-certificate'),
	path('reset-progress/<int:pk>/', ElearningResetProgress.as_view(),name='reset-progress'),
	path('', include(router.urls)),
]
