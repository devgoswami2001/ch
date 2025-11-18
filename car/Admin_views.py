import os
import logging
from django.shortcuts import render, redirect, Http404,get_object_or_404
from django.contrib import messages
from .models import *
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from .views import *
from django.db.models import Sum
from collections import defaultdict
from datetime import datetime
from django.db.models.functions import Cast
import re
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import get_user_model
User = get_user_model()
import requests
from threading import Thread
def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type == '1':  # Check if the user is an admin (user_type = 1)
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "You are not authorized to perform this task.")
            return redirect('Login')  # Redirect to some appropriate page for unauthorized users
    return _wrapped_view

@login_required(login_url='/')
@admin_required
def AdminHome(request):
    # Get the current month
    current_month = datetime.now().month

    # Calculate the total trips (number of vehicle details) for the current month
    total_trips = VehicleDetail.objects.filter(date__month=current_month).count()

    # Calculate the total kilometers (sum of km and ekm) with casting to integer for the current month
    total_km = VehicleDetail.objects.filter(date__month=current_month).aggregate(
        total_km=Sum(Cast('km', output_field=models.IntegerField()))
    )['total_km'] or 0

    total_ekm = VehicleDetail.objects.filter(date__month=current_month).aggregate(
        total_ekm=Sum(Cast('Ekm', output_field=models.IntegerField()))
    )['total_ekm'] or 0

    t = total_km + total_ekm

    # Calculate the total bill amount for the current month
    total_bill = VehicleDetail.objects.filter(date__month=current_month).aggregate(
        total_bill=Sum(Cast('total', output_field=models.FloatField()))
    )['total_bill'] or 0.0

    # Calculate the total fuel consumed for the current month
    total_fuel = Fuel.objects.filter(date__month=current_month).aggregate(
        total_fuel=Sum('fuel_consumed')
    )['total_fuel'] or 0

    total_fuel_C = Fuel.objects.filter(date__month=current_month).aggregate(
        total_fuel=Sum('amount')
    )['total_fuel'] or 0

    # Retrieve monthly and all vehicle data (current month only)
    monthly_data_raw = VehicleDetail.objects.filter(date__month=current_month).select_related('bill')
    all_data_raw = VehicleDetail.objects.select_related('bill')

    # Normalize vehicle numbers: remove extra spaces and convert to uppercase
    def normalize_vehicle_number(vehicle_number):
        return re.sub(r'\s+', '', vehicle_number).upper()

    # Group data by normalized vehicle number
    def group_data(data_queryset):
        grouped_data = defaultdict(lambda: {"trips": 0, "running": 0, "amount": 0})
        for record in data_queryset:
            normalized_v = normalize_vehicle_number(record.v)
            grouped_data[normalized_v]["trips"] += 1
            # Sum km and Ekm for running total
            grouped_data[normalized_v]["running"] += float(record.km or 0) + float(record.Ekm or 0)
            # Sum up the billed amount
            grouped_data[normalized_v]["amount"] += float(record.total or 0)
        return grouped_data

    monthly_data = group_data(monthly_data_raw)
    all_data = group_data(all_data_raw)

    # Prepare summaries for rendering
    monthly_summary = [
        {"id": idx + 1, "v": v, **values} for idx, (v, values) in enumerate(monthly_data.items())
    ]
    all_summary = [
        {"id": idx + 1, "v": v, **values} for idx, (v, values) in enumerate(all_data.items())
    ]

    context = {
        'total_trips': total_trips,
        'total_bill': total_bill,
        'total_fuel': total_fuel,
        't': t,
        'total_fuel_C': total_fuel_C,
        'monthly_data': monthly_summary,
        'all_data': all_summary,
    }

    return render(request, 'Admin/home.html', context)




@login_required(login_url='/')
@admin_required
def Add_vehicle(request):
    if request.method == 'POST':
        try:
            # Get data from the POST request
            Vtype = request.POST['Vtype']
            registration_no = request.POST['registration_no']
            owner = request.POST['owner']
            meter_reading = request.POST['meter_reading']
            rc = request.FILES.get('rc')

            # Check if a vehicle with the same number already exists
            if vehicle.objects.filter(registration_no=registration_no).exists():
                messages.warning(request, 'A vehicle with this number already exists')
            else:
                # Create a new vehicle object and save it
                v = vehicle(
                    type=Vtype,
                    registration_no=registration_no,
                    owner=owner,
                    meter_reading=meter_reading,
                    rc=rc,
                )
                v.save()
                messages.success(request, f"The vehicle No. {v.registration_no} was created successfully")

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

        return redirect('Add_vehicle')  # Redirect to the 'Add_vehicle' page

    return render(request, 'Admin/vehicle.html')# view_vehicle.html

@login_required(login_url='/')
@admin_required
def view_vehicle(request):
    id = request.GET.get('id')
    V = vehicle.objects.all()
    SS = None
    if id:
        SS = V.filter(id=id)
    context = {
        'V': V,
        'SS':SS,
    }
    return render(request, 'Admin/view_vehicle.html' , context)


@login_required(login_url='/')
@admin_required
def view_details_vechile(request,id):
    v = vehicle.objects.get(id=id)
    vv = vehicle_m.objects.filter(v=v)
    select = None
    context = {
        'v' : v,
        'select' : select,
        'vv' : vv,
    }
    return render(request, 'Admin/view_vehicle_details.html' , context)

@login_required(login_url='/')
@admin_required
def vehcile_mm(request):
    vv = vehicle.objects.all()
    if request.method == 'POST':
        number = request.POST['number']
        session = request.POST['session']
        category = request.POST['category']
        date = request.POST['date']
        work = request.POST['work']
        vendor = request.POST['vendor']
        amount = request.POST['amount']
        status = request.POST['status']
        remarks = request.POST['remarks']
        image = request.FILES.get('image')
        vii = vehicle.objects.get(id=number)
        vi = vehicle_m(
            v=vii,
            session=session,
            category=category,
            date=date,
            work=work,
            vendor=vendor,
            amount=amount,
            status=status,
            remarks=remarks,
            image = image,
        )
        vi.save()
        messages.success(request,"Information Added sucessfully")
    context = {
            'vv':vv,
        }
    return render(request, "Admin/info_v.html", context)



@login_required(login_url='/')
@admin_required
def billing(request):
    if request.method == 'POST':
        try:
            # Bill-level details
            type = request.POST.get('type', '')
            cn = request.POST.get('cn', '')
            date = request.POST.get('date', '')
            add = request.POST.get('add', 'NA')
            email = request.POST.get('email', 'NA')
            mob = request.POST.get('mob', 'NA')
            payment = request.POST.get('payment', '0')
            wallet, cash, online = "0", "0", "0"
            gt = request.POST.get('gt', 'NA')
            tc = request.POST.get('tc', 'NA')

            print(f"Bill details: type={type}, cn={cn}, date={date}, add={add}, email={email}, mob={mob}, payment={payment}and {gt}")

            if payment == "1":
                wallet = request.POST.get('gt', '0')  # Grand total from the form
            elif payment == "2":
                cash = request.POST.get('gt', '0')
            elif payment == "3":
                online = request.POST.get('gt', '0')

            print(f"Payment method: wallet={wallet}, cash={cash}, online={online}")

            # Create the Bill object
            bill = Bill(
                type=type,
                c_n=cn,
                date=date,
                add=add,
                email=email,
                mob=mob,
                wallet=wallet,
                cash=cash,
                online=online,
                g_t=gt,
                terms_and_conditions =tc,
            )
            bill.save()
            print(f"Bill saved: {bill}")

            # Vehicle details
            vehicle_count = int(request.POST.get('vehicle_count', 1))  # Get the number of vehicles dynamically
            print(f"Vehicle count: {vehicle_count}")

            for i in range(1, vehicle_count + 1):
                v = request.POST.get(f'vc{i}', '')
                base_fare = request.POST.get(f'bf{i}', '0')
                dis = request.POST.get(f'dis{i}', '0')
                date = request.POST.get(f'date{i}', '0')
                toll = request.POST.get(f'toll{i}', '0')
                km = request.POST.get(f'km{i}', '0')
                igst = request.POST.get(f'igst{i}', '0')
                dn = request.POST.get(f'dn{i}', '')
                way = request.POST.get(f'way{i}', '')
                fr = request.POST.get(f'fr{i}', '')
                to = request.POST.get(f'to{i}', '')
                guest = request.POST.get(f'guest{i}', '')
                Ekm = request.POST.get(f'Ekm{i}', '0')
                ppk = request.POST.get(f'ppk{i}', '0')
                apk = request.POST.get(f'apk{i}', '0')
                Exh = request.POST.get(f'Exh{i}', '0')
                pph = request.POST.get(f'pph{i}', '0')
                aph = request.POST.get(f'aph{i}', '0')
                total = request.POST.get(f'total{i}', '0')

                # Print details for each vehicle
                print(f"Vehicle {i} details: v={v}, base_fare={base_fare}, dis={dis}, toll={toll}, igst={igst}, dn={dn}, way={way}, fr={fr}, to={to}, guest={guest}, total={total}")

                if v:  # Only add valid vehicles
                    VehicleDetail.objects.create(
                        bill=bill,
                        v=v,
                        base_fare=base_fare,
                        dis=dis,
                        toll=toll,
                        igst=igst,
                        d_n=dn,
                        km=km,
                        date = date,
                        way=way,
                        fr=fr,
                        to=to,
                        guest=guest,
                        Ekm=Ekm,
                        ppk=ppk,
                        apk=apk,
                        Exh=Exh,
                        pph=pph,
                        aph=aph,
                        total=total
                    )
                    print(f"Vehicle {i} saved successfully")

            messages.success(request, "Bill generated successfully")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            print(f"Error: {e}")

        return redirect('billing')

    return render(request, 'Admin/ct.html')



@login_required(login_url='/')
@admin_required
def billingg(request):
    if request.method == 'POST':
        try:
            # Bill-level details
            type = request.POST.get('type', '')
            cn = request.POST.get('cn', '')
            date = request.POST.get('date', '')
            add = request.POST.get('add', 'NA')
            email = request.POST.get('email', 'NA')
            mob = request.POST.get('mob', 'NA')
            payment = request.POST.get('payment', '0')
            wallet, cash, online = "0", "0", "0"
            gt = request.POST.get('gt', 'NA')
            
            print(f"Bill details: type={type}, cn={cn}, date={date}, add={add}, email={email}, mob={mob}, payment={payment}")

            if payment == "1":
                wallet = request.POST.get('gt', '0')  # Grand total from the form
            elif payment == "2":
                cash = request.POST.get('gt', '0')
            elif payment == "3":
                online = request.POST.get('gt', '0')

            print(f"Payment method: wallet={wallet}, cash={cash}, online={online}")

            # Create the Bill object
            bill = Bill(
                type=type,
                c_n=cn,
                date=date,
                add=add,
                email=email,
                mob=mob,
                wallet=wallet,
                cash=cash,
                online=online,
                g_t=gt,
            )
            bill.save()
            print(f"Bill saved: {bill}")

            # Vehicle details
            vehicle_count = int(request.POST.get('vehicle_count', 1))  # Get the number of vehicles dynamically
            print(f"Vehicle count: {vehicle_count}")

            for i in range(1, vehicle_count + 1):
                v = request.POST.get(f'vc{i}', '')
                base_fare = request.POST.get(f'bf{i}', '0')
                dis = request.POST.get(f'dis{i}', '0')
                date = request.POST.get(f'date{i}', '0')
                km = request.POST.get(f'km{i}', '0')
                toll = request.POST.get(f'toll{i}', '0')
                igst = request.POST.get(f'igst{i}', '0')
                dn = request.POST.get(f'dn{i}', '')
                way = request.POST.get(f'way{i}', '')
                fr = request.POST.get(f'fr{i}', '')
                to = request.POST.get(f'to{i}', '')
                guest = request.POST.get(f'guest{i}', '')
                Ekm = request.POST.get(f'Ekm{i}', '0')
                ppk = request.POST.get(f'ppk{i}', '0')
                apk = request.POST.get(f'apk{i}', '0')
                Exh = request.POST.get(f'Exh{i}', '0')
                pph = request.POST.get(f'pph{i}', '0')
                aph = request.POST.get(f'aph{i}', '0')
                total = request.POST.get(f'total{i}', '0')

                # Print details for each vehicle
                print(f"Vehicle {i} details: v={v}, base_fare={base_fare}, dis={dis}, toll={toll}, igst={igst}, dn={dn}, way={way}, fr={fr}, to={to}, guest={guest}, total={total}")

                if v:  # Only add valid vehicles
                    VehicleDetail.objects.create(
                        bill=bill,
                        v=v,
                        base_fare=base_fare,
                        dis=dis,
                        toll=toll,
                        igst=igst,
                        d_n=dn,
                        date = date,
                        way=way,
                        fr=fr,
                        to=to,
                        km=km,
                        guest=guest,
                        Ekm=Ekm,
                        ppk=ppk,
                        apk=apk,
                        Exh=Exh,
                        pph=pph,
                        aph=aph,
                        total=total
                    )
                    print(f"Vehicle {i} saved successfully")

            messages.success(request, "Bill generated successfully")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            print(f"Error: {e}")

        return redirect('billingg')

    return render(request, 'Admin/pv.html')# view_vehicle.html





@login_required(login_url='/')
@admin_required
def fuel(request):
    V = vehicle.objects.all()
    if request.method == 'POST':
        try:
            # Retrieve form data
            vehicle_id = request.POST.get('id')
            cmr = int(request.POST.get('cmr', 0))  # Default to 0 if missing
            fuel = float(request.POST.get('fuel', 0))  # Default to 0 if missing
            avg = float(request.POST.get('avg', 0))  # Default to 0 if missing
            date = request.POST.get('date')
            pre = float(request.POST.get('pre', 0))  # Default to 0 if missing

            # Calculate amount (ensure valid multiplication)
            a = fuel * pre

            # Ensure vehicle is selected
            if not vehicle_id:
                messages.error(request, "Vehicle selection is required.")
                return redirect('fuel')

            # Retrieve the vehicle instance
            vehicle_instance = get_object_or_404(vehicle, id=vehicle_id)

            # Create the fuel entry
            Fuel.objects.create(
                v=vehicle_instance,
                km=cmr,
                fuel_consumed=fuel,
                avg=avg,
                date=date,
                amount=a,
                price=pre,
            )
            messages.success(request, 'Fuel entry added successfully.')
            return redirect('fuel')

        except ValueError as e:
            # Handle invalid input cases
            messages.error(request, f"Invalid input: {str(e)}")
            return redirect('fuel')
        except Exception as e:
            # Handle any unexpected errors
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('fuel')

    context = {'V': V}
    return render(request, 'Admin/fuel.html', context)


@login_required(login_url='/')
@admin_required
def get_last_meter_reading(request, id):
    try:
        last_entry = Fuel.objects.filter(v_id=id).order_by('-id').first()
        if last_entry:
            return JsonResponse({'last_meter': last_entry.km})
        else:
            return JsonResponse({'last_meter': 0})
    except Fuel.DoesNotExist:
        return JsonResponse({'last_meter': 0})

@login_required(login_url='/')
@admin_required
def vfuel(request):
    # Fetch all vehicles for the dropdown
    V = vehicle.objects.all()

    # Initialize filtered results and total amount
    SS = Fuel.objects.none()
    total_amount = 0

    # Only process filtering if any filter is provided
    if request.method == "POST":
        # Retrieve filter values from the POST parameters
        vehicle_id = request.POST.get('id')  # Selected vehicle ID
        from_date = request.POST.get('fr')  # 'From' date
        to_date = request.POST.get('to')  # 'To' date

        # Define the filter dictionary to dynamically apply filters
        filters = {}

        # Apply the vehicle filter if a specific vehicle is selected
        if vehicle_id:
            filters['v_id'] = vehicle_id  # Match the `v` ForeignKey field in `Fuel`

        # Apply the date range filter if both dates are provided
        if from_date and to_date:
            filters['date__range'] = [from_date, to_date]

        # Query the Fuel model with the applied filters and order by date descending
        SS = Fuel.objects.filter(**filters).select_related('v').order_by('-date')

        # Calculate the total amount for the filtered entries
        total_amount = SS.aggregate(total=Sum('amount'))['total'] or 0

    # Pass vehicles, filtered results, and the total amount to the template
    context = {
        'V': V,  # All vehicles
        'SS': SS,  # Filtered fuel entries
        'total_amount': total_amount,  # Total sum of 'amount' field for filtered entries
    }

    # Render the template with the context
    return render(request, 'Admin/v_fuel.html', context)

@login_required(login_url='/')
@admin_required
def delete_fuel(request, id):
    # Get the report by ID or return a 404 error if not found
    report = get_object_or_404(Fuel, id=id)

    # Delete the daily report
    report.delete()

    # Redirect to another page after deletion, e.g., a list of reports
    messages.success(request, f"Fuel Entry deleted ")
    return redirect('vfuel')



@login_required(login_url='/')
@admin_required
def Daily_entry(request):
    V = vehicle.objects.all()
    if request.method == 'POST':
            # Get the form data
        vehicle_id = request.POST.get('id')
        date = request.POST.get('date')
        out = request.POST.get('out')
        inn = request.POST.get('inn')
        pn = request.POST.get('pn')
        add = request.POST.get('add')
        vehicle_instance = get_object_or_404(vehicle, id=vehicle_id)
        a = int(inn) - int(out)
        daily_report.objects.create(
            v=vehicle_instance,
            date=date,
            in_km=inn,
            out_km=out,
            name=pn,
            add=add,
            total_r=a
        )
        messages.success(request, 'Daily entry added successfully.')
        return redirect('Daily_entry')
    context = {
        'V':V,
    }
    return render(request, 'Admin/entry.html', context)

@login_required(login_url='/')
@admin_required
def vDaily_entry(request):
    # Fetch all vehicles
    V = vehicle.objects.all()
    
    # Get query parameters
    date_from = request.GET.get('from_date', None)
    date_to = request.GET.get('to_date', None)
    vehicle_id = request.GET.get('id', None)

    # Filter daily reports based on query parameters
    if date_from or date_to or vehicle_id:
        SS = daily_report.objects.all()
    else:
        SS = None    

    if date_from:
        SS = SS.filter(date__gte=date_from)
    if date_to:
        SS = SS.filter(date__lte=date_to)
    if vehicle_id:
        SS = SS.filter(v_id=vehicle_id)

    context = {
        'SS': SS ,  # Return None only if no records exist
        'V': V,  # List of vehicles
    }
    messages
    return render(request, 'Admin/ventry.html', context)

@login_required(login_url='/')
@admin_required
def delete_daily_report(request, id):
    # Get the report by ID or return a 404 error if not found
    report = get_object_or_404(daily_report, id=id)

    # Delete the daily report
    report.delete()

    # Redirect to another page after deletion, e.g., a list of reports
    messages.success(request, f"Daily Report deleted ")
    return redirect('vDaily_entry')

@login_required(login_url='/')
@admin_required
def vbill(request):
    # Fetch all bills initially
    bills = Bill.objects.all()

    # Apply filters based on the request.GET parameters
    invoice_no = request.GET.get('I_O')
    customer_name = request.GET.get('c_n')
    date_from = request.GET.get('fr')
    date_to = request.GET.get('to')
    amount = request.GET.get('amt')

    if invoice_no or customer_name or date_from or date_to or amount:
     if invoice_no:
        bills = bills.filter(invoice_no__icontains=invoice_no)
     if customer_name:
        bills = bills.filter(c_n__icontains=customer_name)
     if date_from:
        bills = bills.filter(date__gte=date_from)
     if date_to:
        bills = bills.filter(date__lte=date_to)
     if amount:
        bills = bills.filter(g_t=amount)
    else:
        bills= None
    

    # Pass filtered bills to the template
    context = {'SS': bills}
    return render(request, 'Admin/vbill.html', context)

@login_required(login_url='/')
@admin_required
def customer_suggestions(request):
    if request.method == "GET":
        query = request.GET.get('q', '')
        if query:
            # Get distinct customer names that contain the query (case insensitive)
            customers = Bill.objects.filter(c_n__icontains=query).values_list('c_n', flat=True).distinct()[:10]
            suggestions = list(customers)  # Convert queryset to list
        else:
            suggestions = []
        return JsonResponse(suggestions, safe=False)

@login_required(login_url='/')
@admin_required
def view_details_bill(request, id):
    a = Bill.objects.get(id=id)
    b = VehicleDetail.objects.filter(bill=a)
    context = {
        's' : a,
        'vv' : b
    }
    return render(request, 'Admin/billdis.html', context)

@login_required(login_url='/')
@admin_required
def view_details_billl(request, id):
    a = Bill.objects.get(id=id)
    b = VehicleDetail.objects.filter(bill=a)
    context = {
        's' : a,
        'vv' : b
    }
    return render(request, 'Admin/billdis1.html', context)

@login_required(login_url='/')
@admin_required
def update_billing(request):
    if request.method == 'POST':
        try:
            # Retrieve the Bill object to update based on the provided ID
            bill_id = request.POST.get('bill_id')  # Assuming you send bill_id as part of the form
            bill = Bill.objects.get(id=bill_id)
            
            # Update the Bill fields from the form data
            bill.c_n = request.POST.get('cn')
            bill.mob = request.POST.get('mob')
            bill.add = request.POST.get('add', '')
            bill.email = request.POST.get('email', '')
            bill.date = request.POST.get('date')
            pay = request.POST.get('pay')
            grand_total = request.POST.get('gt', '0')  # Default to '0' if not provided

            if pay == "1":
                bill.wallet = grand_total
            elif pay == "2":
                bill.cash = grand_total
            elif pay == "3":
                bill.online = grand_total

            bill.g_t = grand_total  # Update grand total in the Bill
            bill.save()

            # Now update the associated VehicleDetail entries
            # Iterate through each vehicle info and update it
            for i in range(1, len(request.POST) // 10 + 1):  # Assuming 10 fields per vehicle (adjust accordingly)
                vehicle_id = request.POST.get(f'vehicle_id_{i}')  # Assuming vehicle_id is sent in the form
                if vehicle_id:
                    vehicle = VehicleDetail.objects.get(id=vehicle_id)
                    
                    vehicle.v = request.POST.get(f'vc{i}')
                    vehicle.d_n = request.POST.get(f'dn{i}')
                    vehicle.date = request.POST.get(f'date{i}')
                    vehicle.way = request.POST.get(f'way{i}')
                    vehicle.fr = request.POST.get(f'fr{i}')
                    vehicle.to = request.POST.get(f'to{i}')
                    vehicle.guest = request.POST.get(f'guest{i}')
                    vehicle.base_fare = request.POST.get(f'bf{i}')
                    vehicle.dis = request.POST.get(f'dis{i}', 0)  # Default to 0 if no discount
                    vehicle.toll = request.POST.get(f'toll{i}')
                    vehicle.igst = request.POST.get(f'ig{i}')
                    vehicle.Ekm = request.POST.get(f'Ekm{i}')
                    vehicle.ppk = request.POST.get(f'ppk{i}')
                    vehicle.apk = request.POST.get(f'apk{i}')
                    vehicle.Exh = request.POST.get(f'Exh{i}')
                    vehicle.pph = request.POST.get(f'pph{i}')
                    vehicle.aph = request.POST.get(f'aph{i}')
                    vehicle.total = request.POST.get(f'total{i}')
                    vehicle.save()

            # After saving the bill and vehicle details, redirect to a success page
            # Correct the redirect syntax with the bill.id
            if bill.type == "1":
                return redirect('view_details_bill', id=bill.id)
            elif bill.type == "2":
                return redirect('view_details_billl', id=bill.id)
            else:
                return HttpResponse("Bill type not recognized", status=404)

        except Bill.DoesNotExist:
            return HttpResponse("Bill not found", status=404)
        except VehicleDetail.DoesNotExist:
            return HttpResponse("Vehicle details not found", status=404)
        except Exception as e:
            return HttpResponse(f"An error occurred: {e}", status=500)

    else:
        return HttpResponse("Invalid request method", status=400)
    
@login_required(login_url='/')
@admin_required
def delete_bill(request, id):
    # Get the bill object by invoice_no, or return a 404 error if not found
    bill = get_object_or_404(Bill, id=id)

    # Delete the bill instance
    bill.delete()

    # Redirect to another page (e.g., a list of bills) after deletion
    messages.success(request, f"Bill deleted ")
    return redirect('vbill')




@login_required(login_url='/')
@admin_required
def delete_vehicle(request, id):
    # Get the bill object by invoice_no, or return a 404 error if not found
    bill = get_object_or_404(vehicle, id=id)

    # Delete the bill instance
    bill.delete()

    # Redirect to another page (e.g., a list of bills) after deletion
    messages.success(request, f"Vehicle deleted ")
    return redirect('view_vehicle')



@login_required(login_url='/')
@admin_required
def Daily_entryo(request):
    V = vehicle.objects.filter(type="2")
    if request.method == 'POST':
            # Get the form data
        vehicle_id = request.POST.get('id')
        date = request.POST.get('date')
        out = request.POST.get('out')
        inn = request.POST.get('inn')
        pn = request.POST.get('pn')
        add = request.POST.get('add')
        vehicle_instance = get_object_or_404(vehicle, id=vehicle_id)
        a = int(inn) - int(out)
        daily_report.objects.create(
            v=vehicle_instance,
            date=date,
            in_km=inn,
            out_km=out,
            name=pn,
            add=add,
            total_r=a
        )
        messages.success(request, 'Daily entry added successfully.')
        return redirect('Daily_entry')
    context = {
        'V':V,
    }
    return render(request, 'Admin/entry.html', context)



@login_required(login_url='/')
@admin_required
def vDaily_entryo(request):
    # Fetch all vehicles
    V = vehicle.objects.filter(type="2")
    
    # Initialize SS as None
    SS = None
    
    # Get query parameters
    date_from = request.GET.get('from_date')
    date_to = request.GET.get('to_date')
    vehicle_id = request.GET.get('id')

    # Filter daily reports based on query parameters
    if date_from or date_to or vehicle_id:
        SS = daily_report.objects.filter(v__in=V)

        if date_from:
            try:
                SS = SS.filter(date__gte=date_from)
            except ValueError:
                messages.error(request, "Invalid 'from_date' format.")

        if date_to:
            try:
                SS = SS.filter(date__lte=date_to)
            except ValueError:
                messages.error(request, "Invalid 'to_date' format.")

        if vehicle_id:
            SS = SS.filter(v_id=vehicle_id)

    context = {
        'SS': SS,  # Return None only if no records exist
        'V': V,    # List of vehicles
    }
    return render(request, 'Admin/ventry.html', context)


@login_required(login_url='/')
@admin_required
def billbook(request):
    if request.method == 'POST':
        # Extract form data
        vehicle_id = request.POST.get('id')
        cust = request.POST.get('cust')
        date = request.POST.get('date')
        amount = request.POST.get('amt')
        image = request.FILES.get('image')
        invoice_number = request.POST.get('invoice')  # Get the invoice number from the form

        # Validate that vehicle exists if selected
        vehicle_instance = None
        if vehicle_id:
            try:
                vehicle_instance = vehicle.objects.get(id=vehicle_id)
            except vehicle.DoesNotExist:
                messages.error(request, "Selected vehicle does not exist.")
                return redirect('billbook')

        # Save the billbook entry
        bill_entry = Bill_Book(
            v=vehicle_instance,
            cust=cust,
            date=date,
            amount=amount,
            image=image,
            invoice=invoice_number
        )
        bill_entry.save()

        # Success message and redirect
        messages.success(request, "Bill entry successfully added.")
        return redirect('billbook')

    # Render the form template
    context = {
        'V': vehicle.objects.all(),  # Pass all vehicles for the dropdown
    }
    return render(request, 'our_bill.html', context)

@login_required(login_url='/')
@admin_required
def vendor_bill(request):
    if request.method == 'POST':
        # Extract form data
        vendor = request.POST.get('vendor')
        vehicle = request.POST.get('v')
        date = request.POST.get('date')
        invoice = request.POST.get('invoice')
        amount = request.POST.get('amount')
        image = request.FILES.get('image')

        # Save the vendor bill entry
        vendor_bill = Vendor_bill(
            v=vehicle,
            vendor=vendor,
            date=date,
            invoice=invoice,
            amount=amount,
            image=image
        )
        vendor_bill.save()

        # Success message and redirect
        messages.success(request, "Vendor bill successfully added.")
        return redirect('vendor_bill')

    # Render the form template
    return render(request, 'vendor_bill.html')




@login_required(login_url='/')
@admin_required
def adv_book(request):
    if request.method == 'POST':
        try:
            cust = request.POST.get('cust')
            fr = request.POST.get('fr')
            to = request.POST.get('to')
            date = request.POST.get('date')
            time = request.POST.get('time')
            number = request.POST.get('number')

            Adv_book.objects.create(
                cust=cust,
                fr=fr,
                to=to,
                Date=date,
                time=time,
                number=number
            )
            messages.success(request, "Advance booking successfully added.")
            return redirect('adv_book')

        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('adv_book')

    bookings = Adv_book.objects.all().order_by('-Date', '-time')
    return render(request, 'Admin/adv_book.html', {'bookings': bookings})


# 2. Edit Booking
@login_required(login_url='/')
@admin_required
def edit_adv_booking(request):
    bookings = Adv_book.objects.all()

    if request.method == 'POST':
        try:
            booking_id = request.POST.get('id')
            booking = get_object_or_404(Adv_book, id=booking_id)

            booking.cust = request.POST.get('cust')
            booking.fr = request.POST.get('fr')
            booking.to = request.POST.get('to')
            booking.Date = request.POST.get('date')
            booking.time = request.POST.get('time')
            booking.number = request.POST.get('number')
            booking.save()

            messages.success(request, "Booking updated successfully.")
            return redirect('adv_book')

        except Exception as e:
            messages.error(request, f"Update failed: {str(e)}")
            return redirect('edit_adv_booking')

    return render(request, 'Admin/edit_adv_book.html', {'bookings': bookings})



# 3. Delete Booking
@login_required(login_url='/')
@admin_required
def delete_adv_booking(request, booking_id):
    booking = get_object_or_404(Adv_book, id=booking_id)
    try:
        booking.delete()
        messages.success(request, "Booking deleted successfully.")
    except Exception as e:
        messages.error(request, f"Delete failed: {str(e)}")

    return redirect('edit_adv_booking')
