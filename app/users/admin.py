from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User
from django.urls import path
from users.views import UserImportView


class UserAdmin(BaseUserAdmin):
    change_list_template = "user_admin_changelist.html"

    def get_urls(self):
        urls = super(UserAdmin, self).get_urls()
        my_urls = [
            path('import-user/', self.admin_site.admin_view(UserImportView.as_view()),
                 name="import-user"),
        ]
        return my_urls + urls


    fieldsets = (
        (None, {'fields': ('email', 'password', 'name', 'last_login', 'username', 'surname', 'is_demo', "member_type", "manager")}),
        ('Permissions', {'fields': (
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        )}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'username', 'surname', 'password1', 'password2', 'is_demo')
            }
        ),
    )

    list_display = ('email','username', 'surname', 'name', 'is_staff',
                    'last_login', 'stripe_customer', "card_id", "credit_card_number")
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)


admin.site.register(User,UserAdmin)
