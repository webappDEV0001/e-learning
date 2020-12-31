from django.db import models
from users.models import User
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


class SubscriptionPlan(models.Model):
    """
    This model store the data of bar plans.
    """

    CURRENCIES_TYPES = (('usd', 'USD'), ("eur", 'EUR'))
    INTERVAL_CHOICES = (('day', 'Day'), ('month', 'Month'), ('year', 'Year'))

    title = models.CharField(max_length=255, help_text="Title of the plan")

    price = models.FloatField(help_text="Specify one time price of the price (per interval). "
                                                  "If plan is monthly provide 1 month price, if it's "
                                                  "yearly provide 1 year or 12 month price")

    description = models.TextField(null=True, blank=True)

    duration = models.PositiveIntegerField(help_text="Duration")

    interval = models.CharField(max_length=100, choices=INTERVAL_CHOICES,
                                default=INTERVAL_CHOICES[1][0])

    currency = models.CharField(choices=CURRENCIES_TYPES, max_length=20,
                                help_text="In which currency you want to pay.")

    plan_id = models.CharField(max_length=150, help_text="Enter the stripe plan id", blank=False, null=False)

    is_active = models.BooleanField(default=True,
                                    help_text="Admin toggle to display/hide "
                                              "the plan from the user")
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, blank=True, null=True)

    # -------------------------------------------------------------------------
    # Meta
    # -------------------------------------------------------------------------
    class Meta:
        verbose_name = "Subscription_Plan"
        verbose_name_plural = "Subscription_Plans"

    # ---------------------------------------------------------------------------
    # __str__
    # ---------------------------------------------------------------------------
    def __str__(self):
        """
        Returns the string representation of the bar plan object.
        """

        return self.title


        # logger.info(('{0} subscription Created for user {1}'.format(self.title, user)))
        #
        # # send payment acknowledgement email to user.
        # logger.info(
        #     ('sending subscription email to the user {0} for subscription {1}'.format(user, self.title)))



class Subscription(models.Model):
    """
        This model store the data of bar subscription.
        """
    STATUS_TYPES = (('active', 'ACTIVE'), ("cancelled", 'CANCELLED'), ("halted", 'HALTED'), ("inactive", 'INACTIVE'))

    subs_id = models.CharField(max_length=250, blank=True, null=True, help_text="Subscription id of stripe")
    user = models.ForeignKey(User,
                             on_delete=models.SET_NULL, null=True,
                             help_text="User related to subscription")

    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL,
                             null=True, related_name="subscriptions")

    start_date = models.DateField(blank=True, null=True)
    expiration = models.DateField()

    status = models.CharField(max_length=150, choices=STATUS_TYPES,default=STATUS_TYPES[3][0],
                                 help_text="The status subscription of the user")

    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)

    cancelled = models.BooleanField(default=False,
                                 help_text="Subscription cancelled")

    # -------------------------------------------------------------------------
    # Meta
    # -------------------------------------------------------------------------
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"


    # ---------------------------------------------------------------------------
    # __str__
    # ---------------------------------------------------------------------------
    def __str__(self):
        """
        Returns the string representation of the bar subscription object.
        """
        if self.user:
            return "Plan:{0}, Taken by: {1}".format(self.plan.title, self.user.email)
        else:
            return self.plan

    

    # ---------------------------------------------------------------------------
    # send_verification_email
    # ---------------------------------------------------------------------------
    def send_activation_subscription_email(self, cancel=False):
        """
        Sends the activation subscription mail to the user.
        """

        if cancel:
            subject = "Your Subscription has been Cancelled"
            context_data = {"user": self.user,
                            "plan": self.plan,
                            "cancellation_date": timezone.now(),
                            "expiration": self.expiration
                            }

            html_template_path = "emails/subscription_cancel-email.html"
            text_template_path = 'emails/subscription_cancel-email.txt'
        else:
            subject = "Your Subscription has been Activated"
            context_data = {"user": self.user,
                            "plan": self.plan,
                            "start_date": self.start_date,
                            "expiration": self.expiration
                            }

            html_template_path = "emails/subscription-email.html"
            text_template_path = 'emails/subscription-email.txt'

        html_content = render_to_string(html_template_path, context_data)

        msg = EmailMultiAlternatives(subject, text_template_path, settings.DEFAULT_FROM_EMAIL, [self.user.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()



class ActivityLog(models.Model):
    """
    Activity Log Model
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.CharField(help_text="Events Log Activity", null=True, blank=True, max_length=100)
    date = models.DateTimeField(null=True, blank=True, help_text="Date")
    end_at = models.DateTimeField(null=True, blank=True, help_text="End Date")
    description = models.TextField(help_text="Description Log")
    log_detail = models.CharField(max_length=150, help_text="Response Detail" ,blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "ActivityLog"
        verbose_name_plural = "ActivityLogs"


    # ---------------------------------------------------------------------------
    # __str__
    # ---------------------------------------------------------------------------
    def __str__(self):
        """
        Returns the string representation of the bar subscription object.
        """
        return str(self.event)