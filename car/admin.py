from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.
class UserModel(UserAdmin):
    list_display = [ 'username', 'user_type' ]

admin.site.register(CustomUser,UserModel)
admin.site.register(vehicle)
admin.site.register(vehicle_m)
admin.site.register(Fuel)
admin.site.register(daily_report)
admin.site.register(Bill)
admin.site.register(VehicleDetail)