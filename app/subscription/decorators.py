from django.http import HttpResponseRedirect
from subscription.models import Subscription

def payment_required(function):
    def wrapper(request, *args, **kw):
        user=request.user  
        subscription = Subscription.objects.filter(user=user, status="active")
        if not subscription:
            return HttpResponseRedirect('/payment/')
        else:
            return function(request, *args, **kw)
    return wrapper

def payment_done(function):
    def wrapper(request, *args, **kw):
        user=request.user
        subscription = Subscription.objects.filter(user=user, status="active")
        if subscription:
            return HttpResponseRedirect('/list/')
        else:
            return function(request, *args, **kw)
    return wrapper