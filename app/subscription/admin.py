from django.contrib import admin
from subscription.models import SubscriptionPlan, Subscription, ActivityLog

class SubscriptionPlanAdminView(admin.ModelAdmin):
    list_display = ('id','title', 'price', 'duration', 'interval', 'currency', 'is_active', 'created_on', 'updated_on')
    search_fields = ('title', 'price')
    ordering = ('created_on', 'updated_on')


class ActivityLogAdminView(admin.ModelAdmin):
    list_display = ('event', 'date', "log_detail", "created_on", "updated_on")
    search_fields = ('event', 'date', 'log_detail')
    ordering = ('-created_on', '-updated_on')


class SubscriptionAdminView(admin.ModelAdmin):
    list_display = ('subs_id', "user", "status", "cancelled", "created_on", "updated_on")
    search_fields = ('subs_id', 'user', 'status')
    ordering = ('created_on', 'updated_on')

admin.site.register(SubscriptionPlan, SubscriptionPlanAdminView)
admin.site.register(Subscription, SubscriptionAdminView)
admin.site.register(ActivityLog, ActivityLogAdminView)