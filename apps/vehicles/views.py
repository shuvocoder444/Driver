from apps.site_settings.context_processors import get_active_dashboard_role
from apps.accounts.utils import log_activity
from apps.accounts.models import ActivityLog
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from .models import Vehicle, VehicleImage, VehicleDocument
from apps.accounts.models import CustomUser


def vehicle_list(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    type_filter = request.GET.get('type', '').strip()

    vehicles = Vehicle.objects.all()
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

    vehicle_counts = Vehicle.objects.aggregate(
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
            creator = request.user if request.user.is_authenticated else CustomUser.objects.filter(role__in=['superadmin', 'admin', 'company']).first()
            if not creator:
                creator = CustomUser.objects.first()

            vehicle = Vehicle.objects.create(
                created_by=creator,
                title=title,
                brand=brand,
                model=model_name,
                year=int(year),
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


def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    context = {
        'vehicle': vehicle,
        'agreements': vehicle.agreements.all(),
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'vehicles/detail.html', context)
