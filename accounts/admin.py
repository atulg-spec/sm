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

# Inline for RecentlyViewed
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from store.models import RecentlyViewed

class RecentlyViewedInline(admin.TabularInline):
    model = RecentlyViewed
    extra = 0
    readonly_fields = ('product', 'viewed_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

# Unregister and Re-register User
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (RecentlyViewedInline,)
