from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address, UserActivity, Newsletter


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
    'username', 'email', 'phone_number', 'first_name', 'last_name', 'is_staff', 'date_joined', 'last_visit')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'phone_number', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('اطلاعات تکمیلی', {'fields': ('phone_number', 'national_id', 'birth_date')}),
        ('تنظیمات اطلاع‌رسانی', {'fields': ('receive_sms', 'receive_email')}),
        ('فعالیت', {'fields': ('last_visit',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('اطلاعات تکمیلی', {'fields': ('email', 'phone_number')}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'province', 'city', 'is_default', 'created_at')
    list_filter = ('province', 'is_default', 'created_at')
    search_fields = ('user__username', 'receiver_full_name', 'city', 'full_address')
    raw_id_fields = ('user',)
    list_editable = ('is_default',)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('user', 'activity_type', 'ip_address', 'user_agent', 'timestamp', 'details')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email', 'user__username')
    raw_id_fields = ('user',)
    list_editable = ('is_active',)