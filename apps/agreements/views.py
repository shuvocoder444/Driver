from apps.site_settings.context_processors import get_active_dashboard_role
from apps.accounts.utils import log_activity
from apps.accounts.models import ActivityLog
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from .models import Agreement, AgreementMedia, AgreementDocument
from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver
from django.utils import timezone
import datetime


def agreement_list(request):
    status_filter = request.GET.get('status', 'all').lower()
    search_query = request.GET.get('search', '').strip()
    contract_type = request.GET.get('type', '')

    agreements = Agreement.objects.select_related('vehicle', 'driver', 'created_by').all()

    if status_filter != 'all':
        agreements = agreements.filter(status__iexact=status_filter)

    if search_query:
        agreements = agreements.filter(
            contract_number__icontains=search_query
        ) | agreements.filter(
            client_name__icontains=search_query
        ) | agreements.filter(
            company_name__icontains=search_query
        )

    if contract_type:
        agreements = agreements.filter(contract_type=contract_type)

    agreement_counts = Agreement.objects.aggregate(
        all=Count('pk'),
        active=Count('pk', filter=Q(status=Agreement.Status.ACTIVE)),
        completed=Count('pk', filter=Q(status=Agreement.Status.COMPLETED)),
        problem=Count('pk', filter=Q(status=Agreement.Status.PROBLEM)),
        cancelled=Count('pk', filter=Q(status=Agreement.Status.CANCELLED)),
    )

    context = {
        'agreements': agreements,
        'counts': agreement_counts,
        'current_status': status_filter,
        'search_query': search_query,
        'current_type': contract_type,
        'contract_types': Agreement.ContractType.choices,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'agreements/list.html', context)


def agreement_create(request):
    vehicles = list(Vehicle.objects.filter(status=Vehicle.Status.AVAILABLE))
    drivers = list(Driver.objects.filter(status=Driver.Status.AVAILABLE))

    if request.method == 'POST':
        contract_type = request.POST.get('contract_type')
        company_name = request.POST.get('company_name', '').strip()
        client_name = request.POST.get('client_name', '').strip()
        vehicle_id = request.POST.get('vehicle_id')
        driver_id = request.POST.get('driver_id')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        daily_price = request.POST.get('daily_rental_price', 0)
        deposit = request.POST.get('deposit', 0)
        terms = request.POST.get('terms_conditions', '')
        comments = request.POST.get('comments', '')

        if client_name and vehicle_id and driver_id:
            vehicle = get_object_or_404(Vehicle, id=vehicle_id)
            driver = get_object_or_404(Driver, id=driver_id)
            
            # Create agreement
            start_date = timezone.now()
            end_date = start_date + datetime.timedelta(days=14)

            agreement = Agreement.objects.create(
                created_by=request.user if request.user.is_authenticated else vehicle.created_by,
                contract_type=contract_type or Agreement.ContractType.SHORT_TERM,
                company_name=company_name or 'Smart Motors Ltd.',
                client_name=client_name,
                vehicle=vehicle,
                driver=driver,
                start_date=start_date,
                end_date=end_date,
                daily_rental_price=daily_price or 34.00,
                deposit=deposit or 2465.00,
                terms_conditions=terms,
                comments=comments,
                status=Agreement.Status.ACTIVE
            )

            # Update statuses
            vehicle.status = Vehicle.Status.RENTED
            vehicle.save()
            driver.status = Driver.Status.BUSY
            driver.save()

            messages.success(request, f'Agreement {agreement.contract_number} created successfully!')
            log_activity(
                request,
                ActivityLog.ActionType.CREATE,
                ActivityLog.Module.AGREEMENTS,
                f"Created rental agreement #{agreement.contract_number} for client {agreement.client_name} (Vehicle: {vehicle.title})"
            )
            return redirect('agreements:list')
        else:
            messages.error(request, 'Please fill in all required fields.')

    context = {
        'vehicles': vehicles or list(Vehicle.objects.all()[:5]),
        'drivers': drivers or list(Driver.objects.all()[:5]),
        'contract_types': Agreement.ContractType.choices,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'agreements/create.html', context)
