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

    elif event.type == "customer.deleted":
        from users.models import User

        user = User.objects.filter(stripe_customer = response.id).first()

        if user is not None:
            user.delete()

        ActivityLog.objects.create(**{
            "event": "CUSTOMER_DELETED",
            "date": datetime.datetime.fromtimestamp(response.created, tz=pytz.utc),
            "description": "Customer deleted successfully with email: "+response.email,
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

    elif event.type == "customer.subscription.deleted":
        subscription = Subscription.objects.filter(subs_id=response.id).first()

        if subscription is not None:
            subscription.status = response.status
            subscription.save()

        ActivityLog.objects.create(**{
            "event": "SUBSCRIPTION_DELETED",
            "date": datetime.datetime.fromtimestamp(response.current_period_start, tz=pytz.utc),
            "end_at": datetime.datetime.fromtimestamp(response.current_period_end, tz=pytz.utc),
            "description": "Subscription has been cancelled/deleted.",
            "log_detail": event.id
        })


    elif event.type == "customer.subscription.updated":

        if response.cancel_at_period_end == True:

            ActivityLog.objects.create(**{
                "event": "SUBSCRIPTION_CANCELLED_FOR_PERIOD_END",
                "date": timezone.now(),
                "description": "Subscription cancelled successfully. No new payments get reducted from"
                               " account from next time",
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

        if subscription is not None:
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


def render_to_pdf(template_src, context_dict={}):
    from xhtml2pdf import pisa
    from io import BytesIO
    from django.template.loader import get_template

    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("cp1252")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

@login_required
@payment_required
def downloadinvoice(request):
    import random

    invoice_data=Subscription.objects.get(user=request.user)
    print(invoice_data)

    context={}
    context['tax_date']=invoice_data.start_date
    context['invoice_number']=invoice_data.id
    context['user_name']=request.user.name
    context['user_surname']=request.user.surname
    context['net_price_percent']=float(invoice_data.amount_paid-(invoice_data.amount_paid*77/100))
    context['vat_price_percent']=float(invoice_data.amount_paid-(invoice_data.amount_paid*23/100))
    context['total_price']=invoice_data.amount_paid
    context['currency']=invoice_data.plan.currency


    pdf = render_to_pdf('invoice.html', context)
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = 'Invoice_{}.pdf'.format(str(random.randint(10000, 99999)))
    content = "attachment; filename={}".format(filename)
    response['Content-Disposition'] = content
    return response

