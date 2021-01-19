from django.urls import path
from .views import *

urlpatterns = [
    path('', SubscriptionView.as_view(), name="subscription"),
    path('cancelsubscription/', cancelsubscription, name="cancelsubscription"),
    path('downloadinvoice/', downloadinvoice, name='downloadinvoice'),
]