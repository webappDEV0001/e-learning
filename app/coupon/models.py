from django.db import models
from users.models import User
from django.utils import timezone
from subscription.models import SubscriptionPlan
from config.common import STRIPE_SECRET_KEY
import json


class Coupon(models.Model):
    """
    This model stores the data of coupon.
    """
    name = models.CharField(max_length=150, help_text="coupon name", unique=True)
    percent = models.FloatField(help_text="coupon price")
    active = models.BooleanField(default=False,help_text="Active status of current coupon")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # ---------------------------------------------------------------------------
    # __str__
    # ---------------------------------------------------------------------------
    def __str__(self):
        """
        Returns the string representation of the Coupons.
        """

        return self.name

    # -------------------------------------------------------------------------
    # Meta
    # -------------------------------------------------------------------------
    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"

    def save(self, *args, **kwargs):
        """
        Overrides default save to make sure:
        """

        # create a strip COUPON.
        import stripe
        from django.core.exceptions import ObjectDoesNotExist

        stripe.api_key = STRIPE_SECRET_KEY
        try:
            coupon = stripe.Coupon.create(
                name=self.name,
                percent_off=self.percent,
                duration="forever",
                id = self.name
            )
        except Exception as e:
            raise ObjectDoesNotExist('Error creating stripe coupon: %s', e.__str__())
        super(Coupon, self).save(*args, **kwargs)


class UserCoupon(models.Model):
    """
    This model store the data for the applied coupon user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # ---------------------------------------------------------------------------
    # __str__
    # ---------------------------------------------------------------------------
    def __str__(self):
        """
        Returns the string representation of the User Applied Coupon.
        """

        return self.user.get_name() + " has used the coupon: " + self.coupon.name


    # -------------------------------------------------------------------------
    # Meta
    # -------------------------------------------------------------------------
    class Meta:
        verbose_name = "User Coupon"
        verbose_name_plural = "User Coupons"
