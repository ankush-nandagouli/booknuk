from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        'username', 'email', 'role', 'is_approved', 'mobile_number',
        'library_card', 'profile_picture_preview', 'is_staff', 'slug'
    )
    list_filter = (
        'role', 'is_approved', 'is_staff', 'is_superuser'
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {
            'fields': ('role', 'is_approved', 'mobile_number', 'library_card', 'profile_picture', 'slug'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Extra Info', {
            'fields': ('role', 'is_approved', 'slug'),
        }),
    )

    search_fields = ('username', 'email', 'library_card', 'slug')
    ordering = ('username',)
    prepopulated_fields = {'slug': ("username",)}
    # Custom function to display profile picture as a thumbnail in admin
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                "<img src='{}' width='40' height='40' style='border-radius:50%' />",
                obj.profile_picture.url
            )
        return "No image"

    profile_picture_preview.short_description = "Profile Pic"

admin.site.register(CustomUser, CustomUserAdmin)
