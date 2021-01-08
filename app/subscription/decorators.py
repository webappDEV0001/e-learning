from django.http import HttpResponseRedirect
from subscription.models import Subscription

def payment_required(function):
    """
    Return the user to payment page if subscription is not active
    """
    def wrapper(request, *args, **kw):
        user=request.user  
        subscription = Subscription.objects.filter(user=user, status="active")
        if not subscription:
            return HttpResponseRedirect('/payment/')
        else:
            return function(request, *args, **kw)
    return wrapper

def payment_done(function):
    """
    Return the user to Dashboard if subscription is active
    """
    def wrapper(request, *args, **kw):
        user=request.user
        subscription = Subscription.objects.filter(user=user, status="active")
        if subscription:
            return HttpResponseRedirect('/list/')
        else:
            return function(request, *args, **kw)
    return wrapper