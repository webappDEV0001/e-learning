import os

import pytz
from django.contrib import messages
from django.http import HttpResponseRedirect, FileResponse, HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import redirect, render, reverse
from django.views.generic import FormView
from django.core.mail import send_mail
from django.views.generic.base import View, TemplateView
from users.forms import ConatctForm
from users.models import User
from django.core.mail import EmailMessage
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from users.forms import UserImportForm, FormPayment
import pandas
import stripe
from subscription.models import SubscriptionPlan, ActivityLog, Subscription
from subscription.decorators import payment_done
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from dateutil.relativedelta import relativedelta
from config.common import *

from config.common import STRIPE_SECRET_KEY


def set_timezone(request):
    if request.method == 'POST':
        user = request.user
        user.timezone = request.POST.get('timezone', None)
        user.save()
        return redirect(reverse('set_timezone'))
    else:
        now = timezone.now()
        return render(request, 'set_timezone.html', {'timezones': pytz.common_timezones, 'now': now})


def send_contact_email(data):
    """
    Send email to the admin.
    """
    email = data.get("email")
    message = data.get("message")
    name = data.get("name")
    file = data.get("file")
    message = "My name is {0} and my email is {1} and my query is {2}".format(name, email, message)
    msg = EmailMessage(
        'Contact Email',
        message,
        "contact@4actuaries.com",
        ['contact@4actuaries.com'],
    )
    if file:
        msg.attach(file.name, file.read(), file.content_type)
    msg.send()


class ViewContact(FormView):
    form_class = ConatctForm
    template_name = "contact.html"
    success_url = reverse_lazy("contact")

    def get_form_kwargs(self):
        kwargs = FormView.get_form_kwargs(self)
        kwargs['request'] = self.request

        return kwargs

    def form_valid(self, form):
        """
        This form valid the data and send an email to admin.
        """
        context_data = {
            "email": form.cleaned_data.get("email"),
            "title": form.cleaned_data.get("title"),
            "name": form.cleaned_data.get("name"),
            "message": form.cleaned_data.get("message"),
            "file": form.cleaned_data.get("attachment")
        }
        if form.is_valid():
            send_contact_email(context_data)  # send email
            messages.info(self.request, "We received your message and will contact you back soon.")
        return HttpResponseRedirect("/contact")


class DisplayPDFView(View):

    def get(self, request, *args, **kwargs):
        path = os.path.join(MEDIA_ROOT, 'terms_conditions.pdf')
        return FileResponse(open(path, 'rb'), content_type='application/pdf')


class DisplayPDFView2(View):

    def get(self, request, *args, **kwargs):
        path = os.path.join(MEDIA_ROOT, 'privacy_policy.pdf')
        return FileResponse(open(path, 'rb'), content_type='application/pdf')


class AdminOrStaffLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is staff or admin"""

    # ---------------------------------------------------------------------------
    # dispatch
    # ---------------------------------------------------------------------------
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class UserImportView(AdminOrStaffLoginRequiredMixin, FormView):
    """
    This class handle the import data of presentation
    """

    form_class = UserImportForm
    template_name = "user_import_form.html"

    def get_success_url(self):
        success_url = reverse_lazy('admin:users_user_changelist')
        return success_url

    def form_valid(self, form):
        csv_file = form.cleaned_data.get("csv_file")
        from os import path
        df = pandas.read_excel(csv_file)
        df.dropna(how="all", inplace=True)

        for i in range(len(df)):
            try:
                data = {
                    'username': df['username'][i],
                    'surname': df['surname'][i],
                    'email': df['email'][i],
                    'name': df['username'][i],
                    'manager': df['Manager'][i],
                    'member_type': df['Member type'][i],
                }

                user, crt = User.objects.get_or_create(**data)
                user.set_password(df['password'][i])
                user.save()
            except:
                print("Skip row")
        messages.info(self.request, "your user data imported successfully.")
        return FormView.form_valid(self, form)

    def get_context_data(self, **kwargs):
        context = super(UserImportView, self).get_context_data()
        context["opts"] = User._meta
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(payment_done, name='dispatch')
class ViewPayment(View):
    """
    This class is used for payment page.
    """

    success_url = reverse_lazy("success")

    def get(self, request, *args, **kwargs):
        context = dict()
        context["plans"] = SubscriptionPlan.objects.filter(is_active=True).order_by("-id").first()

        # Applies coupon in session
        if "coupon" in self.request.session:
            context['coupon'] = self.request.session['coupon']['discounted_price']
        return render(request, "payment.html", context)


    def datetime_converter(self, datetime_val):
        """
        Return int value to datetime
        """
        import datetime
        import pytz
        return datetime.datetime.fromtimestamp(datetime_val, tz=pytz.UTC)


    def post(self, request, *args, **kwargs):
        stripe.api_key = STRIPE_SECRET_KEY
        old_card = self.request.POST.get('old_card_value_checked')
        user = User.objects.get(email=self.request.user)
        plan = SubscriptionPlan.objects.filter(is_active=True).order_by("-id").first()
        params = {"customer": user.stripe_customer, "items": [{"price": plan.plan_id}, ]}
        print(old_card)


        try:

            if Subscription.objects.filter(user=user, status="active"):
                return HttpResponseRedirect(redirect("list"))

            try:
                if "coupon" in self.request.session:
                    params['coupon'] = self.request.session['coupon']['name']


                if old_card:
                    card_id = self.request.user.card_id
                    ActivityLog.objects.create(**{
                        "event": "CUSTOMER_CARD_RENEWED",
                        "date": timezone.now(),
                        "description": user.email+" uses the previous card ("+card_id+") for renew subscription",
                        "log_detail": card_id,
                    })
                else:
                    # CREATE CARD IN STRIPE
                    token = self.request.POST.get('stripeToken')
                    if token:
                        try:
                            card = stripe.Customer.create_source(
                                user.stripe_customer,
                                source=token,
                            )
                            card_id = card.id

                            user.card_id = card_id
                            user.credit_card_number = card.last4
                            user.save()

                            # ACTIVITY LOG ENTRY FOR CARD CREATED SUCCESSFULLY
                            ActivityLog.objects.create(**{
                                "event": "CUSTOMER_CARD_CREATED",
                                "date": timezone.now(),
                                "description": "Card ("+card_id+") is created successfully of "+user.email,
                                "log_detail": card_id,
                            })
                        except Exception as e:
                            ActivityLog.objects.create(**{
                                "event": "CARD_ERROR",
                                "date": timezone.now(),
                                "description": e.__str__(),
                            })
                            messages.error(self.request, "Please enter the valid credit/debit card number.")
                            return HttpResponseRedirect("/payment")
                    else:
                        messages.error(self.request, "Please enter the valid credit/debit card number.")
                        return HttpResponseRedirect("/payment")





                try:
                    # CREATE SUBSCRIPTION IN STRIPE
                    from coupon.models import Coupon


                    if old_card:
                        subscription_modify = Subscription.objects.filter(
                            user=self.request.user).first()
                        subscription_charge = stripe.Subscription.retrieve(subscription_modify.subs_id)
                    else:
                        subscription_charge = stripe.Subscription.create(**params)

                    subscription_params = {
                        "subs_id": subscription_charge.id,
                        "user": user,
                        "plan": plan,
                        "start_date": self.datetime_converter(subscription_charge.start_date),
                        "expiration": self.datetime_converter(subscription_charge.current_period_end),
                        "cancelled": False
                    }

                    if "coupon" in self.request.session:
                        coupon = Coupon.objects.filter(name=self.request.session['coupon']['name']).first()
                        amount = self.request.session['coupon']['discounted_price']
                        subscription_params["amount_paid"] = amount
                        subscription_params["coupon"] = coupon
                    else:
                        amount = float(plan.price)
                        subscription_params["amount_paid"] = amount


                    # ENTRY OF SUBSCRIPTION CREATED SUCCESSFULLY IN MODELS (Subscription, ActivityLog)
                    if subscription_charge.status == "active":

                        subscription_params["status"] = subscription_charge.status



                        # Subscription Created
                        subscription_created,created = Subscription.objects.get_or_create(**subscription_params)

                        # Activation mail send
                        subscription_created.send_activation_subscription_email()

                        messages.success(self.request, "Subscription created successfully. Click on subscription menu and check your details")
                        return HttpResponseRedirect("/list")
                    elif subscription_charge.status in ['unpaid', 'canceled', 'past_due']:

                        subscription_charge = stripe.Subscription.create(**params)

                        subscription_modify.subs_id = subscription_charge['id']
                        subscription_modify.status = subscription_charge['status']
                        subscription_modify.amount_paid = subscription_params['amount_paid']
                        subscription_modify.start_date = self.datetime_converter(subscription_charge['current_period_start'])
                        subscription_modify.expiration = self.datetime_converter(subscription_charge['current_period_end'])
                        subscription_modify.cancelled = False

                        if "coupon" in self.request.session:
                            coupon = subscription_params['coupon']
                            subscription_modify.coupon = coupon
                        else:
                            subscription_modify.coupon = None

                        subscription_modify.save()

                        ActivityLog.objects.create(**{
                            "event": "SUBSCRIPTION_RENEWED",
                            "date": self.datetime_converter(subscription_charge['current_period_start']),
                            "end_at": self.datetime_converter(subscription_charge['current_period_end']),
                            "description": "Subscription status: " + subscription_charge['status'],
                            "log_detail": subscription_charge['id']
                        })
                        messages.success(self.request,
                                         "Subscription updated successfully. Click on subscription menu and check your details")
                        return HttpResponseRedirect("/list")

                    else:
                        ActivityLog.objects.create(**{
                            "event": "SUBSCRIPTION_ERROR",
                            "date": self.datetime_converter(subscription_charge['current_period_start']),
                            "end_at": self.datetime_converter(subscription_charge['current_period_end']),
                            "description": "Subscription status: "+subscription_charge['status'],
                            "log_detail": subscription_charge['id']
                        })
                        messages.error(self.request, "Subscription error. Please your bank account/card details.")
                        return HttpResponseRedirect("/payment")
                except Exception as e:
                    # LOG FOR SUBSCRIPTION NOT CREATED
                    ActivityLog.objects.create(**{
                        "event": "SUBSCRIPTION_ERROR",
                        "date": timezone.now(),
                        "description": e.__str__(),
                    })
                    messages.error(self.request, "Subscription error. Please your bank account/card details.")
                    return HttpResponseRedirect("/payment")
            except Exception as e:
                # LOG FOR CUSTOMER CARD ERROR
                ActivityLog.objects.create(**{
                    "event": "CARD_ERROR",
                    "date": timezone.now(),
                    "description": e.__str__(),
                })
                messages.error(self.request, "Card error. Check your card details please.")
                return HttpResponseRedirect("/payment")
        except Exception as e:
            # ERROR LOG
            ActivityLog.objects.create(**{
                "event": "SERVER_ERROR",
                "date": timezone.now(),
                "description": e.__str__(),
            })
            messages.error(self.request, "Server error. Please try after some time.")
            return HttpResponseRedirect("/payment")
