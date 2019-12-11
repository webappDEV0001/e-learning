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
from django.core.mail import EmailMessage

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
        path =  os.path.join(MEDIA_ROOT, 'terms_condition.pdf')
        return FileResponse(open(path, 'rb'), content_type='application/pdf')