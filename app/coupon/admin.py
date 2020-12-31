from django.contrib import admin
from .models import Coupon, UserCoupon

admin.site.register(Coupon)
admin.site.register(UserCoupon)