from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.accounts.models import CustomUser
from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver, DriverHistory, DriverRating
from apps.agreements.models import Agreement
from apps.billing.models import Subscription, ManualPayment, Plan
from django.db.models import Avg, Count, Q, Sum


def dashboard_router(request):
    """Smart router: routes user to their appropriate dashboard based on their role."""
    user = request.user

    # 1. Authenticated user's real role takes strict priority
    if user.is_authenticated:
        if getattr(user, 'role', '') == CustomUser.Role.DRIVER:
            request.session['active_dashboard_role'] = 'driver'
            request.session.modified = True
            return redirect('dashboard:driver')
        elif getattr(user, 'role', '') in [CustomUser.Role.COMPANY, CustomUser.Role.ADMIN, CustomUser.Role.INDIVIDUAL]:
            request.session['active_dashboard_role'] = 'admin'
            request.session.modified = True
            return redirect('dashboard:admin')
        elif user.is_superuser or getattr(user, 'role', '') == CustomUser.Role.SUPERADMIN:
            role_param = request.GET.get('role', '').strip().lower()
            if role_param == 'admin':
                return redirect('dashboard:admin')
            elif role_param == 'driver':
                return redirect('dashboard:driver')
            request.session['active_dashboard_role'] = 'superadmin'
            request.session.modified = True
            return redirect('dashboard:superadmin')

    # 2. Unauthenticated / guest preview
    active_role = request.session.get('active_dashboard_role')
    if active_role == 'driver':
        return redirect('dashboard:driver')
    elif active_role == 'superadmin':
        return redirect('dashboard:superadmin')
    return redirect('dashboard:admin')


def superadmin_dashboard(request):
    """1. Super Admin Master Dashboard"""
    # Strict Guard: Must be authenticated and superadmin
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    if not (request.user.is_superuser or getattr(request.user, 'role', '') == CustomUser.Role.SUPERADMIN):
        if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
            return redirect('dashboard:driver')
        return redirect('dashboard:admin')

    request.session['active_dashboard_role'] = 'superadmin'
    request.session.modified = True
    display_user = request.user

    # Subscriber Metrics
    total_subscribers = CustomUser.objects.filter(
        role__in=[CustomUser.Role.INDIVIDUAL, CustomUser.Role.COMPANY]
    ).count()
    subscription_counts = Subscription.objects.aggregate(
        active_subscribers=Count(
            'user',
            distinct=True,
            filter=Q(status=Subscription.Status.ACTIVE),
        ),
        pending=Count('pk', filter=Q(status=Subscription.Status.PENDING)),
        one_time_orders=Count('pk', filter=Q(plan__interval=Plan.Interval.ONCE)),
    )
    payment_metrics = ManualPayment.objects.aggregate(
        pending=Count('pk', filter=Q(status=ManualPayment.Status.PENDING)),
        received=Sum('amount', filter=Q(status=ManualPayment.Status.APPROVED)),
    )
    pending_approval = subscription_counts['pending'] + payment_metrics['pending']
    active_subscribers = subscription_counts['active_subscribers']
    one_time_orders = subscription_counts['one_time_orders']

    # Platform Contracts & Revenue
    agreement_counts = Agreement.objects.aggregate(
        total=Count('pk'),
        active=Count('pk', filter=Q(status=Agreement.Status.ACTIVE)),
    )
    total_contracts = agreement_counts['total']
    active_contracts = agreement_counts['active']
    payments_received = payment_metrics['received'] or 0.00

    # Vehicles Fleet
    vehicle_counts = Vehicle.objects.aggregate(
        total=Count('pk'),
        available=Count('pk', filter=Q(status=Vehicle.Status.AVAILABLE)),
        rented=Count('pk', filter=Q(status=Vehicle.Status.RENTED)),
        leased=Count('pk', filter=Q(status=Vehicle.Status.LEASED)),
        maintenance=Count('pk', filter=Q(status=Vehicle.Status.MAINTENANCE)),
    )
    vehicles_available = vehicle_counts['available']
    vehicles_rented = vehicle_counts['rented']
    vehicles_leased = vehicle_counts['leased']
    vehicles_maintenance = vehicle_counts['maintenance']
    total_vehicles = vehicle_counts['total']

    # Drivers
    driver_counts = Driver.objects.aggregate(
        total=Count('pk'),
        busy=Count('pk', filter=Q(status=Driver.Status.BUSY)),
        available=Count('pk', filter=Q(status=Driver.Status.AVAILABLE)),
        warning=Count('pk', filter=Q(status=Driver.Status.WARNING)),
    )
    drivers_total = driver_counts['total']
    drivers_busy = driver_counts['busy']
    drivers_available = driver_counts['available']
    drivers_bad = driver_counts['warning']

    # Recent lists
    recent_agreements = Agreement.objects.select_related('vehicle', 'driver').order_by('-created_at')[:5]
    recent_drivers = Driver.objects.order_by('-created_at')[:5]
    pending_payments = ManualPayment.objects.filter(
        status=ManualPayment.Status.PENDING
    ).select_related('user', 'plan').order_by('-created_at')[:5]

    context = {
        'display_user': display_user,
        'current_dashboard': 'superadmin',
        
        # Metrics
        'total_subscribers': total_subscribers,
        'active_subscribers': active_subscribers,
        'pending_approval': pending_approval,
        'one_time_orders': one_time_orders,

        'total_contracts': total_contracts,
        'active_contracts': active_contracts,
        'payments_received': payments_received,

        'vehicles_available': vehicles_available,
        'vehicles_rented': vehicles_rented,
        'vehicles_leased': vehicles_leased,
        'vehicles_maintenance': vehicles_maintenance,
        'total_vehicles': total_vehicles,

        'drivers_total': drivers_total,
        'drivers_busy': drivers_busy,
        'drivers_available': drivers_available,
        'drivers_bad': drivers_bad,

        'recent_agreements': recent_agreements,
        'recent_drivers': recent_drivers,
        'pending_payments': pending_payments,
    }
    return render(request, 'dashboard/superadmin.html', context)


def admin_dashboard(request):
    """2. Rental Company / Fleet Admin Dashboard (like Team JBDIT)"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    # Guard: If logged in as driver, redirect to driver dashboard!
    if getattr(request.user, 'role', '') == CustomUser.Role.DRIVER:
        request.session['active_dashboard_role'] = 'driver'
        return redirect('dashboard:driver')

    if not (request.user.is_authenticated and getattr(request.user, 'is_superadmin', False)):
        request.session['active_dashboard_role'] = 'admin'
        request.session.modified = True
    display_user = request.user

    # Filter data for this company / fleet
    vehicles = Vehicle.objects.all()
    if display_user and not display_user.is_superadmin:
        my_vehicles = vehicles.filter(created_by=display_user)
    else:
        my_vehicles = vehicles

    fleet_counts = my_vehicles.aggregate(
        total=Count('pk'),
        available=Count('pk', filter=Q(status=Vehicle.Status.AVAILABLE)),
        rented=Count('pk', filter=Q(status=Vehicle.Status.RENTED)),
        maintenance=Count('pk', filter=Q(status=Vehicle.Status.MAINTENANCE)),
    )
    if not fleet_counts['total'] and not display_user.is_superadmin:
        my_vehicles = vehicles
        fleet_counts = my_vehicles.aggregate(
            total=Count('pk'),
            available=Count('pk', filter=Q(status=Vehicle.Status.AVAILABLE)),
            rented=Count('pk', filter=Q(status=Vehicle.Status.RENTED)),
            maintenance=Count('pk', filter=Q(status=Vehicle.Status.MAINTENANCE)),
        )
    total_fleet = fleet_counts['total']
    fleet_available = fleet_counts['available']
    fleet_rented = fleet_counts['rented']
    fleet_maintenance = fleet_counts['maintenance']

    # My Agreements
    my_agreements = Agreement.objects.select_related('vehicle', 'driver').order_by('-created_at')
    agreement_counts = my_agreements.aggregate(
        total=Count('pk'),
        active=Count('pk', filter=Q(status=Agreement.Status.ACTIVE)),
        completed=Count('pk', filter=Q(status=Agreement.Status.COMPLETED)),
    )
    active_rentals = agreement_counts['active']
    completed_rentals = agreement_counts['completed']

    # Drivers under company
    my_drivers = Driver.objects.all()
    driver_counts = my_drivers.aggregate(
        total=Count('pk'),
        available=Count('pk', filter=Q(status=Driver.Status.AVAILABLE)),
    )
    drivers_count = driver_counts['total']
    drivers_available = driver_counts['available']

    # Subscription status
    my_subscription = Subscription.objects.filter(user=display_user, status=Subscription.Status.ACTIVE).first() if display_user else None

    context = {
        'display_user': display_user,
        'current_dashboard': 'admin',
        'company_name': display_user.company_name if display_user and display_user.company_name else 'Team JBDIT Rental Ltd',

        'total_fleet': total_fleet,
        'fleet_available': fleet_available,
        'fleet_rented': fleet_rented,
        'fleet_maintenance': fleet_maintenance,

        'active_rentals': active_rentals,
        'completed_rentals': completed_rentals,
        'total_contracts': agreement_counts['total'],

        'drivers_count': drivers_count,
        'drivers_available': drivers_available,

        'my_subscription': my_subscription,
        'recent_agreements': my_agreements[:5],
        'my_vehicles': my_vehicles[:6],
    }
    return render(request, 'dashboard/admin.html', context)


def get_current_driver(request):
    """Helper to resolve driver instance for the active driver view."""
    if not request.user.is_authenticated:
        return None, None
    # Block company user from driver portal
    if not (request.user.is_superuser or getattr(request.user, 'role', '') in [CustomUser.Role.SUPERADMIN, CustomUser.Role.DRIVER]):
        return None, None
    if not getattr(request.user, 'is_superadmin', False):
        request.session['active_dashboard_role'] = 'driver'
        request.session.modified = True
    display_user = request.user

    drivers = Driver.objects.annotate(average_rating_value=Avg('ratings__rating'))
    driver = drivers.filter(user=display_user).first()
    if not driver and display_user and display_user.email:
        driver = drivers.filter(email=display_user.email).first()
    if not driver:
        driver = drivers.first()

    return display_user, driver


def driver_dashboard(request):
    """3. Driver Dedicated Portal Dashboard - Profile & Performance"""
    display_user, driver = get_current_driver(request)
    if not display_user:
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return redirect('dashboard:admin')

    # Driver statistics
    agreements = Agreement.objects.filter(driver=driver) if driver else Agreement.objects.none()
    active_agreement = agreements.filter(status=Agreement.Status.ACTIVE).first()
    history_entries = driver.history_entries.all() if driver else []
    ratings = driver.ratings.all() if driver else []

    agreement_counts = agreements.aggregate(
        total=Count('pk'),
        active=Count('pk', filter=Q(status=Agreement.Status.ACTIVE)),
        completed=Count('pk', filter=Q(status=Agreement.Status.COMPLETED)),
        problem=Count('pk', filter=Q(status=Agreement.Status.PROBLEM)),
    )
    history_count = len(history_entries)
    rating_count = len(ratings)

    context = {
        'display_user': display_user,
        'driver': driver,
        'current_dashboard': 'driver',

        'total_agreements': agreement_counts['total'],
        'active_agreements': agreement_counts['active'],
        'completed_agreements': agreement_counts['completed'],
        'problem_agreements': agreement_counts['problem'],
        'total_issues': history_count,
        'completion_rate': 100 if agreement_counts['total'] == 0 else int((agreement_counts['completed'] / agreement_counts['total']) * 100),
        'total_reviews': rating_count,
        'average_rating': driver.average_rating if driver else 4.8,

        'active_agreement': active_agreement,
        'history_entries': history_entries,
        'ratings': ratings,
    }
    return render(request, 'dashboard/driver.html', context)


def driver_vehicle_view(request):
    """Current Assigned Vehicle dedicated page for driver"""
    display_user, driver = get_current_driver(request)
    if not display_user:
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return redirect('dashboard:admin')

    agreements = Agreement.objects.filter(driver=driver) if driver else Agreement.objects.none()
    active_agreement = agreements.filter(status=Agreement.Status.ACTIVE).select_related('vehicle').first()
    vehicle = active_agreement.vehicle if active_agreement else None

    # Past assigned vehicles
    past_agreements = agreements.exclude(status=Agreement.Status.ACTIVE).select_related('vehicle')[:5]

    context = {
        'display_user': display_user,
        'driver': driver,
        'current_dashboard': 'driver',
        'active_agreement': active_agreement,
        'vehicle': vehicle,
        'past_agreements': past_agreements,
    }
    return render(request, 'dashboard/driver_vehicle.html', context)


def driver_agreements_view(request):
    """Trip Contracts & Agreements dedicated page for driver"""
    display_user, driver = get_current_driver(request)

    agreements = Agreement.objects.filter(driver=driver).select_related('vehicle').order_by('-created_at') if driver else Agreement.objects.none()

    status_filter = request.GET.get('status', 'all')
    if status_filter == 'active':
        filtered_agreements = agreements.filter(status=Agreement.Status.ACTIVE)
    elif status_filter == 'completed':
        filtered_agreements = agreements.filter(status=Agreement.Status.COMPLETED)
    elif status_filter == 'problem':
        filtered_agreements = agreements.filter(status=Agreement.Status.PROBLEM)
    else:
        filtered_agreements = agreements

    agreement_counts = agreements.aggregate(
        total=Count('pk'),
        active=Count('pk', filter=Q(status=Agreement.Status.ACTIVE)),
        completed=Count('pk', filter=Q(status=Agreement.Status.COMPLETED)),
        problem=Count('pk', filter=Q(status=Agreement.Status.PROBLEM)),
    )

    context = {
        'display_user': display_user,
        'driver': driver,
        'current_dashboard': 'driver',
        'agreements': filtered_agreements,
        'total_count': agreement_counts['total'],
        'active_count': agreement_counts['active'],
        'completed_count': agreement_counts['completed'],
        'problem_count': agreement_counts['problem'],
        'current_filter': status_filter,
    }
    return render(request, 'dashboard/driver_agreements.html', context)


def driver_history_view(request):
    """Driver Incident History & Ratings dedicated page"""
    display_user, driver = get_current_driver(request)

    history_entries = driver.history_entries.all().order_by('-incident_date') if driver else []
    ratings = driver.ratings.all().order_by('-created_at') if driver else []

    context = {
        'display_user': display_user,
        'driver': driver,
        'current_dashboard': 'driver',
        'history_entries': history_entries,
        'ratings': ratings,
        'total_issues': len(history_entries),
        'total_reviews': len(ratings),
        'average_rating': driver.average_rating if driver else 4.8,
    }
    return render(request, 'dashboard/driver_history.html', context)
