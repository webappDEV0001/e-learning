import os

import pytz
from django.contrib import messages
from django.http import HttpResponseRedirect, FileResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import redirect, render, reverse
from django.views.generic import FormView
from django.core.mail import send_mail
from django.views.generic.base import View
from users.forms import ConatctForm
from users.models import User
from django.core.mail import EmailMessage
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from users.forms import UserImportForm
import pandas

from config.common import *
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
            send_contact_email(context_data) #send email
            messages.info(self.request, "We received your message and will contact you back soon.")
        return HttpResponseRedirect("/contact")


class DisplayPDFView(View):

    def get(self, request, *args, **kwargs):
        path =  os.path.join(MEDIA_ROOT, 'terms_conditions.pdf')
        return FileResponse(open(path, 'rb'), content_type='application/pdf')

class DisplayPDFView2(View):

    def get(self, request, *args, **kwargs):
        path =  os.path.join(MEDIA_ROOT, 'privacy_policy.pdf')
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
        from os import path
        csv_file = form.cleaned_data.get("csv_file")
        df = pandas.read_excel(csv_file)
        df.dropna(how="all", inplace=True)

        for i in range(len(df)):
            try:
                data = {
                    'username': df['username'][i],
                    'surname': df['surname'][i],
                    'email': df['email'][i],
                    'name': df['username'][i],
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