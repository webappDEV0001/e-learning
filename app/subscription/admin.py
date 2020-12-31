from django.contrib import admin
from subscription.models import SubscriptionPlan, Subscription, ActivityLog

class SubscriptionPlanAdminView(admin.ModelAdmin):
    list_display = ('id','title', 'price', 'duration', 'interval', 'currency', 'is_active', 'created_on', 'updated_on')
    search_fields = ('title', 'price')
    ordering = ('created_on', 'updated_on')


admin.site.register(SubscriptionPlan, SubscriptionPlanAdminView)
admin.site.register(Subscription)
admin.site.register(ActivityLog)