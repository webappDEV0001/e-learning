from django.conf import settings  # new
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse, HttpResponseRedirect  # new
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.generic import TemplateView
from .decorators import payment_required
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import Subscription, ActivityLog
from config.common import STRIPE_SECRET_KEY
from django.utils import timezone
from django.contrib import messages
import stripe
import json


@method_decorator(login_required, name='dispatch')
@method_decorator(payment_required, name='dispatch')
class SubscriptionView(TemplateView):
    """
    Subscription View Page
    """
    template_name = "subscription.html"

    def get_context_data(self, **kwargs):
        context = super(SubscriptionView, self).get_context_data()
        context["data"] = Subscription.objects.get(status="active", user=self.request.user)
        return context


@login_required
@payment_required
def cancelsubscription(request):
    stripe.api_key = STRIPE_SECRET_KEY
    sub = Subscription.objects.get(status="active", user=request.user)
    try:
        subscription = stripe.Subscription.modify(
            sub.subs_id,
            cancel_at_period_end=True,
        )
        ActivityLog.objects.create(**{
            "user": request.user,
            "event": "SUBSCRIPTION_CANCELLED",
            "date": timezone.now(),
            "description": "Subscription cancelled successfully",
            "log_detail": subscription['id']
        })
        sub.cancelled = True
        sub.save()
        sub.send_activation_subscription_email(cancel=True)
        messages.success("Subscription cancelled successfully")
        return HttpResponseRedirect("/subscription")
    except Exception as e:
        ActivityLog.objects.create(**{
            "user": request.user,
            "event": "SUBSCRIPTION_CANCELLED_ERROR",
            "date": timezone.now(),
            "description": e.__str__(),
        })
        messages.error(request, "Subscription already cancelled!")
        return HttpResponseRedirect("/subscription")

@csrf_exempt
def stripe_webhook(request):
    if request.method == "POST":
        stripe.api_key = settings.STRIPE_SECRET_KEY
        endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        event = None
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        print("Event ====== ", event)

        if event['type'] == "customer.subscription.deleted":
            print("========================> ", "customer.subscription.deleted")
            subscription_id = None
            print(event['data']['object']['items']['data'][0]['subscription'])

        if event['type'] == "customer.subscription.created":
            print("========================> ","customer.subscription.created")
            subscription_id = None
            print(event['data']['object']['items']['data'][0]['subscription'])

        return HttpResponse(status=200)
    else:
        print("Method not allowed")
        return HttpResponse(status=200)
