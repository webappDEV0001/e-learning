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
class ViewPayment(FormView):
    """
    This class is used for payment page.
    """

    form_class = FormPayment
    success_url = reverse_lazy("success")
    template_name = "payment.html"

    def get_context_data(self, **kwargs):
        """
        Return context data to template
        """
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by("-id").first()
        context = super(ViewPayment, self).get_context_data()
        context["plans"] = plans

        # Applies coupon in session
        if "coupon" in self.request.session:
            context['coupon'] = self.request.session['coupon']['discounted_price']

        return context


    def datetime_converter(self, datetime_val):
        """
        Return int value to datetime
        """
        import datetime
        import pytz
        return datetime.datetime.fromtimestamp(datetime_val, tz=pytz.UTC)


    def form_valid(self, form):
        form_data = form.cleaned_data
        stripe.api_key = STRIPE_SECRET_KEY
        token = form_data['stripeToken']
        user = User.objects.get(email=self.request.user)
        plan = SubscriptionPlan.objects.filter(is_active=True).order_by("-id").first()


        try:

            if Subscription.objects.filter(user=user, status="active"):
                return HttpResponseRedirect(redirect("list"))

            try:

                # CREATE CARD IN STRIPE
                card = stripe.Customer.create_source(
                    user.stripe_customer,
                    source=token,
                )

                # ACTIVITY LOG ENTRY FOR CARD CREATED SUCCESSFULLY
                ActivityLog.objects.create(**{
                    "event": "CUSTOMER_CARD_CREATED",
                    "date": timezone.now(),
                    "description": "Card is created successfully",
                    "log_detail": card.id,
                })

                params = {"customer": user.stripe_customer, "items": [{"price": plan.plan_id},]}

                if "coupon" in self.request.session:
                    params['coupon'] = self.request.session['coupon']['name']

                try:
                    # CREATE SUBSCRIPTION IN STRIPE
                    from coupon.models import Coupon

                    subscription_charge = stripe.Subscription.create(**params)





                    # ENTRY OF SUBSCRIPTION CREATED SUCCESSFULLY IN MODELS (Subscription, ActivityLog)
                    if subscription_charge.status == "active":

                        subscription_params = {
                            "subs_id": subscription_charge.id,
                            "user": user,
                            "plan": plan,
                            "start_date": self.datetime_converter(subscription_charge.start_date),
                            "expiration": self.datetime_converter(subscription_charge.current_period_end),
                            "status": subscription_charge.status,
                            "cancelled": False
                        }

                        if "coupon" in self.request.session:
                            coupon = Coupon.objects.filter(name=self.request.session['coupon']['name']).first()
                            amount = self.request.session['coupon']['discounted_price']
                            subscription_params["amount_paid"]=amount
                            subscription_params["coupon"]= coupon
                        else:
                            amount = float(plan.price)
                            subscription_params["amount_paid"]= amount

                        # Subscription Created
                        customer,created = Subscription.objects.get_or_create(**subscription_params)

                        # Activation mail send
                        customer.send_activation_subscription_email()

                        return render(self.request, "success.html", context={"message": "Subscription created successfully", "data":customer})
                    else:
                        ActivityLog.objects.create(**{
                            "event": "SUBSCRIPTION_ERROR",
                            "date": self.datetime_converter(subscription_charge['current_period_start']),
                            "end_at": self.datetime_converter(subscription_charge['current_period_end']),
                            "description": "Subscription status: "+subscription_charge['status'],
                            "log_detail": subscription_charge['id']
                        })
                        messages.error(self.request, "Issue cause in subscription or payment")
                        return HttpResponseRedirect("/payment")
                except Exception as e:
                    # LOG FOR SUBSCRIPTION NOT CREATED
                    ActivityLog.objects.create(**{
                        "event": "SUBSCRIPTION_ERROR",
                        "date": timezone.now(),
                        "description": e.__str__(),
                    })
                    messages.error(self.request, "Issue cause in subscription or payment")
                    return HttpResponseRedirect("/payment")
            except Exception as e:
                # LOG FOR CUSTOMER CARD ERROR
                ActivityLog.objects.create(**{
                    "event": "CARD_ERROR",
                    "date": timezone.now(),
                    "description": e.__str__(),
                })
                messages.error(self.request, "Issue cause in subscription or payment")
                return HttpResponseRedirect("/payment")
        except Exception as e:
            # ERROR LOG
            ActivityLog.objects.create(**{
                "event": "SERVER_ERROR",
                "date": timezone.now(),
                "description": e.__str__(),
            })
            messages.error(self.request, "Issue cause in subscription or payment")
            return HttpResponseRedirect("/payment")
