from django.db import models
from django.db.models import Avg
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Driver(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'Available', 'Available'
        BUSY = 'Busy', 'Busy'
        WARNING = 'Warning', 'Warning'
        INACTIVE = 'Inactive', 'Inactive'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='driver_profile'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_drivers'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_drivers'
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True, null=True)
    
    passport_number = models.CharField(max_length=30, db_index=True)
    passport_expiry = models.DateField(blank=True, null=True)
    license_number = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    license_expiry = models.DateField(blank=True, null=True)
    personal_id = models.CharField(max_length=30, db_index=True, help_text='14 digits personal ID number')
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    user_comments = models.TextField(blank=True, null=True)
    admin_comments = models.TextField(blank=True, null=True)
    
    avatar = models.ImageField(upload_to='drivers/avatars/', blank=True, null=True)
    passport_copy_pdf = models.FileField(upload_to='drivers/passports/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Driver'
        verbose_name_plural = 'Drivers'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.passport_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def average_rating(self):
        if 'average_rating_value' in self.__dict__:
            average = self.average_rating_value
        else:
            average = self.ratings.aggregate(average=Avg('rating'))['average']
        return round(average, 1) if average is not None else 5.0

    @property
    def total_agreements_count(self):
        return self.agreements.count()

    @property
    def active_agreements_count(self):
        return self.agreements.filter(status='Active').count()

    @property
    def completed_agreements_count(self):
        return self.agreements.filter(status='Completed').count()

    @property
    def issues_count(self):
        return self.history_entries.count()

    @property
    def completion_rate(self):
        total = self.total_agreements_count
        if total > 0:
            return int((self.completed_agreements_count / total) * 100)
        return 100


class DriverHistory(models.Model):
    class HistoryType(models.TextChoices):
        NON_PAYMENT = 'Non-payment', 'Non-payment'
        DISAPPEARED = 'Disappeared or Ran Away', 'Disappeared or Ran Away'
        UNPAID_FINES = 'Unpaid Fines', 'Unpaid Fines'
        VIOLATION = 'Violation of Contract Terms', 'Violation of Contract Terms'
        ACCIDENT = 'Accident or Damage', 'Accident or Damage'
        FRAUD = 'Fraud or Suspicious Behavior', 'Fraud or Suspicious Behavior'
        OTHER = 'Other', 'Other'

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='history_entries')
    history_type = models.CharField(max_length=50, choices=HistoryType.choices)
    incident_date = models.DateField()
    description = models.TextField()
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-incident_date']
        verbose_name = 'Driver History Entry'
        verbose_name_plural = 'Driver History Entries'

    def __str__(self):
        return f"{self.history_type} - {self.driver.full_name} ({self.incident_date})"


class DriverRating(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='ratings')
    rated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_ratings'
    )
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)]
    )
    admin_comments = models.TextField(blank=True, null=True)
    user_comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating} stars for {self.driver.full_name}"
