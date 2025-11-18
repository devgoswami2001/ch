from django.db import models
from django.contrib.auth.models import AbstractUser
import qrcode
import base64
from io import BytesIO
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum

# Create your models here.
class CustomUser(AbstractUser):
    USER = (
        (1,'Admin'),
        (2,'Manager'),
        (3,'Driver'),
    )
    user_type = models.CharField(choices=USER, max_length=50,default=1)


class vehicle(models.Model):
    type = models.CharField(max_length=100)
    registration_no = models.CharField(max_length=100)
    owner = models.CharField(max_length=100)
    avg_fuel = models.PositiveBigIntegerField(null=True, default=0)
    meter_reading = models.PositiveBigIntegerField(null=True)
    rc = models.ImageField(upload_to='media/rc')

    def __str__(self):
        return f"{self.id} {self.registration_no} {self.type}"
    
class vehicle_m(models.Model):
    v = models.ForeignKey(vehicle, on_delete=models.DO_NOTHING)
    session = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    date = models.DateField()
    work = models.CharField(max_length=500)
    vendor = models.CharField(max_length=200)
    amount = models.PositiveBigIntegerField()
    status = models.CharField(max_length=100)
    remarks = models.CharField(max_length=500)
    image = models.ImageField(upload_to='media/maintinance')

    def __str__(self):
        return f"{self.id} {self.v.registration_no} {self.category}"
    
class Fuel(models.Model):
    v = models.ForeignKey(vehicle, on_delete=models.DO_NOTHING, related_name='fuel_entries')  # Specify a unique related_name
    km = models.PositiveBigIntegerField()  # Distance traveled since last refuel
    date = models.DateField()
    fuel_consumed = models.PositiveBigIntegerField()
    price = models.FloatField(null=True)
    amount = models.FloatField(null=True)   # Fuel refilled (in liters)
    avg = models.FloatField(null=True)
      # Mileage (km/liter)

    def __str__(self):
        return f"{self.id} {self.v.registration_no} {self.km}"

# Signal to update avg_fuel
@receiver(post_save, sender=Fuel)
def update_avg_fuel(sender, instance, **kwargs):
    # Get the related vehicle
    vehicle = instance.v
    
    # Get all fuel entries for the vehicle
    fuel_entries = Fuel.objects.filter(v=vehicle)

    if fuel_entries.count() < 2:
        # If less than 2 entries, set avg_fuel to 0
        vehicle.avg_fuel = 0
    else:
        # Calculate total distance traveled and total fuel consumed
        total_distance = fuel_entries.aggregate(total_km=Sum('km'))['total_km'] or 0
        total_fuel = fuel_entries.aggregate(total_fuel=Sum('fuel_consumed'))['total_fuel'] or 0

        # Calculate average mileage (km per liter)
        avg_mileage = total_distance / total_fuel if total_fuel > 0 else 0
        vehicle.avg_fuel = avg_mileage

    vehicle.save()
    
class daily_report(models.Model):
    v = models.ForeignKey(vehicle, on_delete=models.DO_NOTHING)
    date = models.CharField(max_length=200)
    in_km = models.CharField(max_length=100)
    out_km = models.CharField(max_length=100)
    total_r = models.CharField(max_length=100)
    name = models.CharField(max_length=100, default="NA")
    add = models.CharField(max_length=100, default="NA")
    def __str__(self):
        return f"{self.v} {self.in_km} {self.out_km}"

class Bill(models.Model):
    type = models.CharField(max_length=200)
    invoice_no = models.CharField(max_length=200, unique=True, blank=True, null=True)
    c_n = models.CharField(max_length=200, default="NA")
    date = models.CharField(max_length=200, default="NA")
    add = models.CharField(max_length=200, default="NA")
    email = models.CharField(max_length=200, default="NA")
    mob = models.CharField(max_length=200, default="NA")
    wallet = models.CharField(max_length=200, default="NA")
    cash = models.CharField(max_length=200, default="NA")
    online = models.CharField(max_length=200, default="NA")
    g_t = models.CharField(max_length=200, default="NA")
    qr_code = models.TextField(blank=True, null=True)
    terms_and_conditions = models.TextField(null=True)
    def save(self, *args, **kwargs):
        # Generate invoice_no if not already set
        if not self.invoice_no:
            prefix = "CHU" if self.type == "1" else "PRV" if self.type == "2" else "GEN"
            last_invoice = Bill.objects.filter(invoice_no__startswith=prefix).order_by('-id').first()
            last_number = int(last_invoice.invoice_no[len(prefix):]) if last_invoice and last_invoice.invoice_no else 0
            self.invoice_no = f"{prefix}{last_number + 1:06d}"
        
        # Generate QR code before saving
        self.qr_code = self.generate_qr_code()
        
        super().save(*args, **kwargs)

    def generate_qr_code(self):
        # Generate QR code data
        qr_data = f"Pass id: {self.invoice_no}"
        
        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Save the image as a base64 string
        img = qr.make_image(fill='black', back_color='white')
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return img_str

    def __str__(self):
        return f"{self.invoice_no} {self.date}"


class VehicleDetail(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="vehicles")
    v = models.CharField(max_length=200)  # Vehicle number
    base_fare = models.CharField(max_length=200, default="0")
    dis = models.CharField(max_length=200, default="0")
    toll = models.CharField(max_length=200, default="0")
    igst = models.CharField(max_length=200, default="0")
    date = models.DateField()
    km = models.CharField(max_length=200, default="0")
    Ekm = models.CharField(max_length=200, default="0")
    ppk = models.CharField(max_length=200, default="0")
    apk = models.CharField(max_length=200, default="0")
    Exh = models.CharField(max_length=200, default="0")
    pph = models.CharField(max_length=200, default="0")
    aph = models.CharField(max_length=200, default="0")
    d_n = models.CharField(max_length=200)
    way = models.CharField(max_length=200)
    fr = models.CharField(max_length=200)
    to = models.CharField(max_length=200)
    guest = models.CharField(max_length=500)
    total = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.v} - {self.bill.invoice_no}"


class Bill_Book(models.Model):
    v = models.ForeignKey(vehicle, on_delete=models.DO_NOTHING, related_name='Bill_Book')
    image = models.ImageField(upload_to='media/BillBook')
    cust = models.CharField(max_length=300)
    date = models.CharField(max_length=200)
    invoice = models.CharField(max_length=300)
    amount = models.PositiveBigIntegerField()

    def __str__(self):
        return f"{self.v} - {self.invoice}"
    

class Vendor_bill(models.Model):
    v = models.CharField(max_length=300)
    image = models.ImageField(upload_to='media/vendorbill')
    vendor = models.CharField(max_length=300)
    date = models.CharField(max_length=200)
    invoice = models.CharField(max_length=300)
    amount = models.PositiveBigIntegerField()

    def __str__(self):
        return f"{self.v} - {self.invoice}"



class Adv_book(models.Model):
    cust = models.CharField(max_length=100)
    fr = models.CharField(max_length=100)
    to = models.CharField(max_length=100)
    Date = models.DateField()
    time = models.TimeField(null=True, blank=True)  # <-- ADD THIS
    number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.v} - {self.cust}"
