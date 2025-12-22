from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'country', 'city', 'isp', 'updated_at')
    search_fields = ('user__username', 'user__email', 'ip_address', 'country', 'city')
    readonly_fields = ('updated_at',)
    list_filter = ('country', 'updated_at')
    
    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Location Data', {
            'fields': ('ip_address', 'country', 'region', 'city', 'zip_code', 'map_link')
        }),
        ('Technical Data', {
            'fields': ('lat', 'lon', 'isp', 'timezone', 'updated_at')
        }),
    )
