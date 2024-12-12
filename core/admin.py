from django.contrib import admin
from apps.models import *
from django.apps import AppConfig

# Register your models here.

admin.site.site_header = "My App Administration"
admin.site.site_title = "My App Admin Portal"
admin.site.index_title = "Manage My App"

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "My Models"
    verbose_name = "Shop Dashboard"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ["username", "email"]

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    pass