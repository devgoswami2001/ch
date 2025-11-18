from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views, Admin_views
urlpatterns = [
    path('',views.Login,name='Login'),
    path('doLogin',views.doLogin,name='doLogin'),
    path('doLogout',views.doLogout,name='doLogout'),


    path('Admin/Home',Admin_views.AdminHome,name='AdminHome'),

    path('Admin/Add/Vehicle',Admin_views.Add_vehicle,name='Add_vehicle'),
    path('Admin/View/Vehicle',Admin_views.view_vehicle,name='view_vehicle'),
    path('Admin/Details/Vehicle/<int:id>',Admin_views.view_details_vechile,name='view_details_vechile'),
    path('Admin/Details/Vehicle/M',Admin_views.vehcile_mm,name='vehcile_mm'),
    path('Delete/Vehicle/<int:id>',Admin_views.delete_vehicle,name='delete_vehicle'),

    path('Our/Bill/Book',Admin_views.billbook,name='billbook'),
    path('Vendor/Bill/Book',Admin_views.vendor_bill,name='vendor_bill'),
    path('Adv/booking',Admin_views.adv_book,name='adv_book'),


    path('Admin/Chaudhary/billing',Admin_views.billing,name='billing'),
    path('Admin/Parvez/billing',Admin_views.billingg,name='billingg'),
    path('View/billing',Admin_views.vbill,name='vbill'),
    path('customer-suggestions/', Admin_views.customer_suggestions, name='customer_suggestions'),
    path('View/billing/details/<int:id>',Admin_views.view_details_bill,name='view_details_bill'),
    path('View/bill/details/<int:id>',Admin_views.view_details_billl,name='view_details_billl'),
    path('Update/Billing',Admin_views.update_billing,name='update_billing'),
    path('Delete/Bill/<int:id>',Admin_views.delete_bill,name='delete_bill'),

    #path('Admin/updateI',Admin_views.updateI,name='updateI'),
    #path('Admin/updatePP',Admin_views.updatePP,name='updatePP'),
    #path('Admin/updateF',Admin_views.updateF,name='updateF'),
    path('Admin/fuel',Admin_views.fuel,name='fuel'),
    path('Admin/view/fuel',Admin_views.vfuel,name='vfuel'),
    path('Delete/Fuel/<int:id>',Admin_views.delete_fuel,name='delete_fuel'),
    path('Admin/Daily/Entry',Admin_views.Daily_entry,name='Daily_entry'),
    path('Admin/Daily/Entry/Others',Admin_views.Daily_entryo,name='Daily_entryo'),
    path('Admin/View/Daily/Entry',Admin_views.vDaily_entry,name='vDaily_entry'),
    path('Admin/View/Daily/Entry/Others',Admin_views.vDaily_entryo,name='vDaily_entryo'),
    path('Delete/daily/report/<int:id>',Admin_views.delete_daily_report,name='delete_daily_report'),

    path('Admin/get-last-meter-reading/<int:id>/', Admin_views.get_last_meter_reading, name='get_last_meter_reading'),
    # Other URL patterns
    path('advance-booking/', Admin_views.adv_book, name='adv_book'),

    # Edit booking
    path('advance-booking/edit/', Admin_views.edit_adv_booking, name='edit_adv_booking'),

    # Delete booking
    path('advance-booking/delete/<int:booking_id>/', Admin_views.delete_adv_booking, name='delete_adv_booking'),
    
]+ static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)
