from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import UserCoupon, Coupon
from django.db.models import Q
from subscription.models import SubscriptionPlan
from django.views import View


class CouponApplyView(View):
    """
    This is the coupon apply ajax view
    """
    content_type = 'application/javascript'

    def get(self, request):
        coupon = Coupon.objects.filter(name=self.request.GET.get("coupon"), active=True).first()
        context = {}
        if coupon and ("coupon" not in request.session):
            if UserCoupon.objects.filter(Q(user=request.user) & Q(coupon=coupon)):
                context['message'] = "coupon expired/used"
            else:
                plan = SubscriptionPlan.objects.filter(is_active=True).order_by("-id").first()
                user_coupon = UserCoupon(user=request.user, coupon=coupon, plan=plan)
                user_coupon.save()
                discounted_price = plan.price - (plan.price * coupon.percent / 100)

                # This is the coupon session
                request.session['coupon'] = {"name": coupon.name, "percent": coupon.percent,
                                             "discounted_price": discounted_price}
                context['message'] =  "success"
                context['coupon'] = discounted_price
        else:
            context['message'] = "Invalid Coupon"
            try:
                del request.session['coupon']
            except Exception as e:
                pass
        return JsonResponse(context, safe=False)
