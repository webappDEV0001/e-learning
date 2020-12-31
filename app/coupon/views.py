from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import UserCoupon, Coupon
from django.db.models import Q
from subscription.models import SubscriptionPlan

def couponApply(request):
    if request.method == "GET":
        coupon = Coupon.objects.filter(name=request.GET.get("coupon"), active=True).first()


        if coupon and ("coupon" not in request.session):
            if UserCoupon.objects.filter(Q(user=request.user) & Q(coupon=coupon)):
                return HttpResponse("coupon expired/used")
            else:
                plan = SubscriptionPlan.objects.filter(is_active=True).order_by("-id").first()
                usercoupon = UserCoupon(user=request.user, coupon=coupon, plan=plan)
                usercoupon.save()
                request.session['coupon'] = {"name": coupon.name}
            return HttpResponse("success")
        else:
            try:
                del request.session['coupon']
            except:
                pass
            return HttpResponse("Invalid Coupon")
