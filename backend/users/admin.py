from django.contrib import admin

from .models import Follow, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Class to customize users display in admin panel."""

    list_display = [
        'pk', 'username', 'email', 'first_name', 'last_name',
        'is_staff', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    list_filter = ['username', 'email', 'is_staff', 'date_joined']
    empty_value_display = '-пусто-'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    empty_value_display = '-пусто-'
