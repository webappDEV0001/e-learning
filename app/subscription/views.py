from django.http.response import JsonResponse, HttpResponseRedirect  # new
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.generic import TemplateView
from .decorators import payment_required
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import Subscription, ActivityLog
from config.common import STRIPE_SECRET_KEY, STRIPE_ENDPOINT_SECRET
from django.utils import timezone
from django.contrib import messages
import stripe
import pytz
import datetime


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
        sub.cancelled = True
        sub.save()
        sub.send_activation_subscription_email(cancel=True)
        messages.success(request, "Subscription cancelled successfully")
        return HttpResponseRedirect("/subscription")
    except Exception as e:
        ActivityLog.objects.create(**{
            "event": "SUBSCRIPTION_CANCELLED_ERROR",
            "date": timezone.now(),
            "description": e.__str__(),
        })
        messages.error(request, "Subscription already cancelled!")
        return HttpResponseRedirect("/subscription")


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_ENDPOINT_SECRET
        )

    except ValueError as e:
        # Invalid payload

        ActivityLog.objects.create(**{
            "event": "SERVER_ERROR",
            "date": timezone.now(),
            "description": e.__str__(),
        })

        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature

        ActivityLog.objects.create(**{
            "event": "SERVER_ERROR",
            "date": timezone.now(),
            "description": e.__str__(),
        })

        return HttpResponse(status=400)

    # Response Data
    response = event.data.object

    # Handle events
    if event.type == 'customer.created':

        ActivityLog.objects.create(**{
            "event": "CUSTOMER_CREATED",
            "date": timezone.now(),
            "description": "Customer created successfully",
            "log_detail": event.id
        })

    elif event.type == "customer.subscription.created":

        ActivityLog.objects.create(**{
            "event": "SUBSCRIPTION_CREATED",
            "date": datetime.datetime.fromtimestamp(response.current_period_start, tz=pytz.utc),
            "end_at": datetime.datetime.fromtimestamp(response.current_period_end, tz=pytz.utc),
            "description": "Subscription created and activated successfully",
            "log_detail": event.id
        })

    elif event.type == "customer.subscription.updated":

        if response.cancel_at_period_end == True:

            ActivityLog.objects.create(**{
                "event": "SUBSCRIPTION_CANCELLED",
                "date": timezone.now(),
                "description": "Subscription cancelled successfully",
                "log_detail": event.id
            })

        else:
            # Renewing Subscription

            subscription = Subscription.objects.filter(subs_id=response.id).first()
            subscription.status = "active"
            subscription.amount_paid = subscription.plan.price,
            subscription.coupon = None,
            subscription.card_id = subscription.card_id,
            subscription.start_date = datetime.datetime.fromtimestamp(response.current_period_start, tz=pytz.utc)
            subscription.expiration = datetime.datetime.fromtimestamp(response.current_period_end, tz=pytz.utc)
            subscription.cancelled = False
            subscription.save()

            try:
                renew_subscription = stripe.Customer.modify_source(
                          request.user.stripe_customer,
                          "card_1I5sbOHgNODZOvfzP9iA8o4p",
                )
            except Exception as e:
                pass


            # Renew activation mail send
            subscription.send_activation_subscription_email()

            ActivityLog.objects.create(**{
                "event": "SUBSCRIPTION_RENEWED",
                "date": timezone.now(),
                "description": "Subscription renewed successfully",
                "log_detail": event.id
            })

    elif event.type == "coupon.created":

        ActivityLog.objects.create(**{
            "event": "COUPON_CREATED",
            "date": timezone.now(),
            "description": "Coupon created successfully",
            "log_detail": event.id
        })

    elif event.type == "invoice.paid":

        ActivityLog.objects.create(**{
            "event": "PAYMENT_PAID",
            "date": timezone.now(),
            "description": "Invoice created for payment paid",
            "log_detail": event.id
        })

    elif event.type == "charge.succeeded":

        ActivityLog.objects.create(**{
            "event": "CHARGE_CREATED",
            "date": timezone.now(),
            "description": "Payment paid",
            "log_detail": event.id
        })

    elif event.type == "payment_intent.created":

        ActivityLog.objects.create(**{
            "event": "PAYMENT_CREATED",
            "date": timezone.now(),
            "description": "Payment paid",
            "log_detail": event.id
        })

    elif event.type == "invoice.finalized":

        ActivityLog.objects.create(**{
            "event": "INVOICE_FINALISED_PAYMENT",
            "date": timezone.now(),
            "description": "Invoice for finalised payment done",
            "log_detail": event.id
        })

    elif event.type == "invoice.payment_succeeded":

        ActivityLog.objects.create(**{
            "event": "PAYMENT_SUCCESSFULLY_DONE",
            "date": timezone.now(),
            "description": "Invoice created for payment done",
            "log_detail": event.id
        })

    elif event.type == "invoice.payment_failed" or event.type == "invoice.finalization_failed":

        subscription = Subscription.objects.filter(subs_id=event.subscription).first()
        subscription.status = "cancelled"
        subscription.save()
        ActivityLog.objects.create(**{
            "event": "PAYMENT_UNSUCCESSFUL",
            "date": timezone.now(),
            "description": event.type,
            "log_detail": event.id
        })

    else:

        ActivityLog.objects.create(**{
            "event": "EVENT_HANDLE_ERROR",
            "date": datetime.datetime.fromtimestamp(response.current_period_start),
            "description": event.type,
            "log_detail": event.id
        })

    return HttpResponse(status=200)
