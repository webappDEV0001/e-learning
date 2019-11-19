from django.urls import reverse
from django.utils.translation import ugettext as _
from django import forms
from allauth.account.forms import LoginForm, ChangePasswordForm, SignupForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Fieldset, Layout, Row, Column



class LoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        # Add magic stuff to redirect back.
        self.helper.layout.append(
            HTML(
                "{% if redirect_field_value %}"
                "<input type='hidden' name='{{ redirect_field_name }}'"
                " value='{{ redirect_field_value }}' />"
                "{% endif %}"
            )
        )
        # Add password reset link.
        self.helper.layout.append(
            HTML(
                "<p><a class='button secondaryAction' href={url}>{text}</a></p>".format(
                    url=reverse('account_reset_password'),
                    text=_('Forgot Password?')
                )
            )
        )
        # Add submit button like in original form.
        self.helper.layout.append(
            HTML(
                '<button class="btn btn-primary btn-block" type="submit">'
                '%s</button>' % _('Sign In')
            )
        )

        self.helper.label_class = 'col-xs-2 hide'
        self.helper.field_class = 'col-xs-8'


class ChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        # Add magic stuff to redirect back.

        # Add submit button like in original form.
        self.helper.layout.append(
            HTML(
                '<button class="btn btn-primary btn-block" type="submit">'
                '%s</button>' % _('Change Password')
            )
        )

        self.helper.label_class = 'col-xs-2 hide'
        self.helper.field_class = 'col-xs-6'



class SignUpForm(SignupForm):

    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    surname  = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Surname'}))

    def save(self, request):
        user = super(SignUpForm, self).save(request)
        user.surname = self.cleaned_data.get("surname")
        user.save()
        return user


class ConatctForm(forms.Form):
    """
    This class handle the contact form data.
    """

    name = forms.CharField(max_length=30,
                           widget=forms.TextInput(attrs={'class': 'form-control form-control-lg required',
                                                         'placeholder': 'Name'}))
    title = forms.CharField(max_length=100,
                            widget=forms.TextInput(attrs={'class': 'form-control form-control-lg  required',
                                                          'placeholder': 'Title'}))
    email = forms.EmailField(max_length=60,
                             widget=forms.TextInput(attrs={'class': 'form-control form-control-lg  required',
                                                           'placeholder': 'Email'}))

    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control form-control-lg',
                                                           'placeholder': 'Message'}), required=False)

