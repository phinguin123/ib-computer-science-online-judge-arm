from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django import forms
from .models import User, UserProfile, AdminType

class UserProfileAdmin(admin.ModelAdmin):
    # This defines the columns you see in the list
    list_display = ('username', 'total_score', 'tier', 'submission_number', 'accepted_number')
    
    # This allows you to search by username
    search_fields = ('user__username', 'real_name')
    
    # This allows you to filter by Tier on the right sidebar
    list_filter = ('tier',)

    def username(self, obj):
        return obj.user.username

class UserChangeForm(forms.ModelForm):
    """Form for changing user password in admin"""
    class Meta:
        model = User
        fields = '__all__'

class UserAdmin(admin.ModelAdmin):
    form = UserChangeForm
    # Display fields in the list view
    list_display = ('username', 'email', 'admin_type', 'is_disabled', 'last_login', 'password_info')
    list_filter = ('admin_type', 'is_disabled', 'open_api', 'two_factor_auth')
    search_fields = ('username', 'email')
    ordering = ('username',)
    
    # Enable actions including delete
    actions = ['delete_selected']
    
    # Fields shown when editing a user
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email',)}),
        ('Permissions', {'fields': ('admin_type', 'problem_permission', 'is_disabled')}),
        ('Security', {'fields': ('two_factor_auth', 'tfa_token', 'open_api', 'open_api_appkey')}),
        ('Important dates', {'fields': ('last_login', 'create_time')}),
    )
    
    readonly_fields = ('last_login', 'create_time')
    
    def password_info(self, obj):
        """Show password hash status"""
        if obj.password:
            # Show first few chars of hash to indicate it exists
            hash_preview = obj.password[:20] + '...' if len(obj.password) > 20 else obj.password
            return format_html(
                '<span style="color: green;" title="Password is set (hashed)">✓ Set</span><br>'
                '<small style="color: #666; font-family: monospace;">{}</small>',
                hash_preview
            )
        return format_html('<span style="color: red;">✗ Not set</span>')
    password_info.short_description = 'Password Status'
    
    def save_model(self, request, obj, form, change):
        # If password field was changed and is not already hashed, hash it
        if 'password' in form.changed_data:
            password = form.cleaned_data.get('password')
            if password and not password.startswith('pbkdf2_'):
                obj.set_password(password)
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Prevent deleting yourself"""
        if obj.id == request.user.id:
            from django.contrib import messages
            messages.error(request, "You cannot delete your own account!")
            return
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """Prevent deleting yourself when using bulk delete"""
        if request.user.id in queryset.values_list('id', flat=True):
            from django.contrib import messages
            messages.error(request, "You cannot delete your own account!")
            queryset = queryset.exclude(id=request.user.id)
        super().delete_queryset(request, queryset)

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(User, UserAdmin)