from apps.site_settings.context_processors import get_active_dashboard_role
from apps.accounts.utils import fleet_access_required, fleet_user_ids, log_activity
from apps.accounts.models import ActivityLog
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import Vehicle, VehicleImage, VehicleDocument


@fleet_access_required
def vehicle_list(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    type_filter = request.GET.get('type', '').strip()

    fleet_vehicles = Vehicle.objects.filter(created_by__in=fleet_user_ids(request.user))
    vehicles = fleet_vehicles
    if query:
        vehicles = vehicles.filter(
            Q(title__icontains=query) |
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(registration_number__icontains=query) |
            Q(color__icontains=query)
        )
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)
    if type_filter:
        vehicles = vehicles.filter(vehicle_type=type_filter)

    vehicle_counts = fleet_vehicles.aggregate(
        total=Count('pk'),
        available=Count('pk', filter=Q(status=Vehicle.Status.AVAILABLE)),
        rented=Count('pk', filter=Q(status=Vehicle.Status.RENTED)),
        maintenance=Count('pk', filter=Q(status=Vehicle.Status.MAINTENANCE)),
    )

    context = {
        'vehicles': vehicles,
        'query': query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'total_count': vehicle_counts['total'],
        'available_count': vehicle_counts['available'],
        'rented_count': vehicle_counts['rented'],
        'maintenance_count': vehicle_counts['maintenance'],
        'vehicle_types': Vehicle.VehicleType.choices,
        'status_choices': Vehicle.Status.choices,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'vehicles/list.html', context)


@fleet_access_required
def vehicle_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        brand = request.POST.get('brand', '').strip()
        model_name = request.POST.get('model', '').strip()
        year = request.POST.get('year', '').strip()
        color = request.POST.get('color', '').strip()
        registration_number = request.POST.get('registration_number', '').strip().upper()
        vehicle_type = request.POST.get('vehicle_type', Vehicle.VehicleType.RENT)
        status = request.POST.get('status', Vehicle.Status.AVAILABLE)
        description = request.POST.get('description', '').strip()
        cover_image = request.FILES.get('cover_image')

        if not title or not brand or not model_name or not registration_number or not year:
            messages.error(request, 'Please fill in all mandatory fields: Title, Brand, Model, Year, and Registration Plate.')
        else:
            try:
                year_value = int(year)
            except ValueError:
                year_value = None

            if year_value is None or year_value < 1886 or year_value > timezone.now().year + 1:
                messages.error(request, 'Please enter a valid vehicle year.')
            elif vehicle_type not in Vehicle.VehicleType.values or status not in Vehicle.Status.values:
                messages.error(request, 'Please select a valid vehicle type and status.')
            else:
                vehicle = Vehicle.objects.create(
                    created_by=request.user,
                    title=title,
                    brand=brand,
                    model=model_name,
                    year=year_value,
                    color=color,
                    registration_number=registration_number,
                    vehicle_type=vehicle_type,
                    status=status,
                    description=description,
                    cover_image=cover_image
                )
                messages.success(request, f'Vehicle "{vehicle.title}" added to garage successfully!')
                log_activity(
                    request,
                    ActivityLog.ActionType.CREATE,
                    ActivityLog.Module.VEHICLES,
                    f"Added vehicle '{vehicle.title}' ({vehicle.registration_number}) to fleet garage"
                )
                return redirect('vehicles:list')

    context = {
        'vehicle_types': Vehicle.VehicleType.choices,
        'status_choices': Vehicle.Status.choices,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'vehicles/create.html', context)


@fleet_access_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(
        Vehicle.objects.filter(created_by__in=fleet_user_ids(request.user)),
        pk=pk,
    )
    context = {
        'vehicle': vehicle,
        'agreements': vehicle.agreements.all(),
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'vehicles/detail.html', context)
