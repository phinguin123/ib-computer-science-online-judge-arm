from django.contrib import admin
from .models import User, UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    # This defines the columns you see in the list
    list_display = ('username', 'total_score', 'tier', 'submission_number', 'accepted_number')
    
    # This allows you to search by username
    search_fields = ('user__username', 'real_name')
    
    # This allows you to filter by Tier on the right sidebar
    list_filter = ('tier',)

    def username(self, obj):
        return obj.user.username

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(User)