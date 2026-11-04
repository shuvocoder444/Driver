from apps.site_settings.context_processors import get_active_dashboard_role
from apps.accounts.utils import fleet_access_required, fleet_user_ids, log_activity
from apps.accounts.models import ActivityLog
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from django.db import transaction
from .models import Agreement, AgreementMedia, AgreementDocument
from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver
from django.utils import timezone
import datetime
from decimal import Decimal, InvalidOperation
from PIL import Image, UnidentifiedImageError


MAX_AGREEMENT_UPLOAD_SIZE = 10 * 1024 * 1024


def _is_valid_image(upload):
    if upload.size > MAX_AGREEMENT_UPLOAD_SIZE:
        return False
    try:
        with Image.open(upload) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        return False
    finally:
        upload.seek(0)
    return True


def _is_valid_pdf(upload):
    if upload.size > MAX_AGREEMENT_UPLOAD_SIZE:
        return False
    signature = upload.read(5)
    upload.seek(0)
    return signature == b'%PDF-'


@fleet_access_required
def agreement_list(request):
    status_filter = request.GET.get('status', 'all').lower()
    search_query = request.GET.get('search', '').strip()
    contract_type = request.GET.get('type', '')

    agreements = Agreement.objects.filter(
        created_by__in=fleet_user_ids(request.user)
    ).select_related('vehicle', 'driver', 'created_by')

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

    agreement_counts = Agreement.objects.filter(
        created_by__in=fleet_user_ids(request.user)
    ).aggregate(
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


@fleet_access_required
def agreement_create(request):
    fleet_users = fleet_user_ids(request.user)
    vehicles = list(Vehicle.objects.filter(
        created_by__in=fleet_users,
        status=Vehicle.Status.AVAILABLE,
    ))
    drivers = list(Driver.objects.filter(
        created_by__in=fleet_users,
        status=Driver.Status.AVAILABLE,
    ))

    if request.method == 'POST':
        contract_type = request.POST.get('contract_type')
        company_name = request.POST.get('company_name', '').strip()
        client_name = request.POST.get('client_name', '').strip()
        vehicle_id = request.POST.get('vehicle_id')
        driver_id = request.POST.get('driver_id')
        try:
            daily_price = Decimal(request.POST.get('daily_rental_price') or '34.00')
            deposit = Decimal(request.POST.get('deposit') or '2465.00')
        except InvalidOperation:
            daily_price = deposit = None
        terms = request.POST.get('terms_conditions', '')
        comments = request.POST.get('comments', '')
        before_image = request.FILES.get('before_rental_image')
        agreement_document = request.FILES.get('agreement_document')

        if not client_name or not vehicle_id or not driver_id:
            messages.error(request, 'Please fill in all required fields.')
        elif request.POST.get('terms_agree') != 'on':
            messages.error(request, 'Please accept the Terms of Service and Privacy Policy.')
        elif daily_price is None or deposit is None or daily_price < 0 or deposit < 0:
            messages.error(request, 'Please enter valid, non-negative rental and deposit amounts.')
        elif contract_type and contract_type not in Agreement.ContractType.values:
            messages.error(request, 'Please select a valid contract type.')
        elif before_image and not _is_valid_image(before_image):
            messages.error(request, 'Please upload a valid image under 10MB.')
        elif agreement_document and not _is_valid_pdf(agreement_document):
            messages.error(request, 'Please upload a valid PDF under 10MB.')
        else:
            with transaction.atomic():
                vehicle = get_object_or_404(
                    Vehicle.objects.select_for_update(),
                    pk=vehicle_id,
                    created_by__in=fleet_users,
                    status=Vehicle.Status.AVAILABLE,
                )
                driver = get_object_or_404(
                    Driver.objects.select_for_update(),
                    pk=driver_id,
                    created_by__in=fleet_users,
                    status=Driver.Status.AVAILABLE,
                )
                start_date = timezone.now()
                end_date = start_date + datetime.timedelta(days=14)

                agreement = Agreement.objects.create(
                    created_by=request.user,
                    contract_type=contract_type or Agreement.ContractType.SHORT_TERM,
                    company_name=company_name or 'Smart Motors Ltd.',
                    client_name=client_name,
                    vehicle=vehicle,
                    driver=driver,
                    start_date=start_date,
                    end_date=end_date,
                    daily_rental_price=daily_price,
                    deposit=deposit,
                    terms_conditions=terms,
                    comments=comments,
                    status=Agreement.Status.ACTIVE
                )
                if before_image:
                    AgreementMedia.objects.create(
                        agreement=agreement,
                        file=before_image,
                        is_before_rental=True,
                    )
                if agreement_document:
                    AgreementDocument.objects.create(
                        agreement=agreement,
                        document=agreement_document,
                    )

                vehicle.status = Vehicle.Status.RENTED
                vehicle.save(update_fields=['status', 'updated_at'])
                driver.status = Driver.Status.BUSY
                driver.save(update_fields=['status', 'updated_at'])

            messages.success(request, f'Agreement {agreement.contract_number} created successfully!')
            log_activity(
                request,
                ActivityLog.ActionType.CREATE,
                ActivityLog.Module.AGREEMENTS,
                f"Created rental agreement #{agreement.contract_number} for client {agreement.client_name} (Vehicle: {vehicle.title})"
            )
            return redirect('agreements:list')
    context = {
        'vehicles': vehicles,
        'drivers': drivers,
        'contract_types': Agreement.ContractType.choices,
        'current_dashboard': get_active_dashboard_role(request),
    }
    return render(request, 'agreements/create.html', context)
