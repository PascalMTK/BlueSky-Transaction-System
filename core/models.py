from datetime import timedelta
from django.db import models
from django.utils import timezone

ONLINE_THRESHOLD = timedelta(minutes=5)


class Country(models.Model):
    name                    = models.CharField(max_length=100)
    code                    = models.CharField(max_length=2, unique=True)
    currency_code           = models.CharField(max_length=5)
    currency_name           = models.CharField(max_length=60)
    flag_emoji              = models.CharField(max_length=10)
    phone_code              = models.CharField(max_length=10)
    default_fee_percentage  = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)
    # Units of local currency per 1 USD — set/updated manually by an admin.
    # Used to convert mixed-currency totals (e.g. total fees across all
    # countries) into a single comparable USD figure.
    usd_exchange_rate       = models.DecimalField(max_digits=14, decimal_places=4, default=1)
    is_active               = models.BooleanField(default=True)
    created_at              = models.DateTimeField(auto_now_add=True)
    updated_at              = models.DateTimeField(auto_now=True)

    class Meta:
        managed  = True
        db_table = 'countries'
        ordering = ['name']

    def __str__(self):
        return f"{self.flag_emoji} {self.name}"


class User(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_AGENT = 'agent'
    ROLE_CHOICES = [('admin', 'Admin'), ('agent', 'Agent')]

    STATUS_ACTIVE  = 'active'
    STATUS_PENDING = 'pending'
    STATUS_DELETED = 'deleted'
    STATUS_CHOICES = [('active', 'Active'), ('pending', 'Pending'), ('inactive', 'Inactive'), ('deleted', 'Deleted')]

    name          = models.CharField(max_length=255)
    email         = models.EmailField(unique=True)
    password      = models.CharField(max_length=255)
    phone         = models.CharField(max_length=20, null=True, blank=True)
    role          = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    country       = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL, db_column='country_id')
    agent_code    = models.CharField(max_length=20, unique=True, null=True, blank=True)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address       = models.CharField(max_length=255, null=True, blank=True)
    id_number     = models.CharField(max_length=50, null=True, blank=True)
    profile_photo = models.CharField(max_length=255, null=True, blank=True)
    last_seen     = models.DateTimeField(null=True, blank=True)
    forum_last_read_at = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        managed  = True
        db_table = 'users'
        indexes = [
            models.Index(fields=['role', 'status'], name='user_role_status_idx'),
            models.Index(fields=['country', 'status'], name='user_country_status_idx'),
        ]

    def __str__(self):
        return self.name

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_agent(self):
        return self.role == self.ROLE_AGENT

    def is_active_user(self):
        return self.status == self.STATUS_ACTIVE

    def is_online(self):
        return bool(self.last_seen) and (timezone.now() - self.last_seen) < ONLINE_THRESHOLD

    def initials(self):
        return self.name[:2].upper()

    def check_password(self, raw_password):
        from core.hashers import LaravelBcryptHasher
        hasher = LaravelBcryptHasher()
        return hasher.verify(raw_password, self.password)

    def set_password(self, raw_password):
        import bcrypt
        hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt(10))
        self.password = hashed.decode()

    def photo_url(self):
        if self.profile_photo:
            return f"/media/{self.profile_photo}"
        return None


class Transaction(models.Model):
    TYPE_SEND       = 'send'
    TYPE_RECEIVE    = 'receive'
    TYPE_EXCHANGE   = 'exchange'
    TYPE_WITHDRAWAL = 'withdrawal'
    TYPE_CHOICES    = [
        ('send', 'Send'),
        ('receive', 'Receive'),
        ('exchange', 'Exchange'),
        ('withdrawal', 'Withdrawal'),
    ]

    STATUS_COMPLETED = 'completed'
    STATUS_PENDING   = 'pending'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES   = [('completed', 'Completed'), ('pending', 'Pending'), ('cancelled', 'Cancelled')]

    PAYMENT_CHOICES = [('cash', 'Cash'), ('mobile_money', 'Mobile Money'), ('bank', 'Bank')]

    transaction_number  = models.CharField(max_length=30, unique=True)
    sender_name         = models.CharField(max_length=255)
    sender_phone        = models.CharField(max_length=25)
    receiver_name       = models.CharField(max_length=255, null=True, blank=True)
    receiver_phone      = models.CharField(max_length=25, null=True, blank=True)
    client_email        = models.EmailField(null=True, blank=True)
    amount              = models.DecimalField(max_digits=15, decimal_places=2)
    fee_percentage      = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)
    fee_amount          = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount        = models.DecimalField(max_digits=15, decimal_places=2)
    currency            = models.CharField(max_length=10, null=True, blank=True)
    origin_country      = models.ForeignKey(Country, related_name='outgoing', on_delete=models.PROTECT, db_column='origin_country_id')
    # Set when the agent picks "Other / not listed" for the origin country —
    # origin_country then points at a generic placeholder Country row and
    # this field carries the name the agent actually typed in.
    origin_country_manual_name = models.CharField(max_length=100, null=True, blank=True)
    destination_country = models.ForeignKey(Country, related_name='incoming', on_delete=models.PROTECT, db_column='destination_country_id', null=True, blank=True)
    agent               = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='agent_id')
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes               = models.TextField(null=True, blank=True)
    payment_method      = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default='cash')
    transaction_type    = models.CharField(max_length=20, choices=TYPE_CHOICES, default='send')
    sent_at             = models.DateTimeField(null=True, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        managed  = True
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='tx_status_created_idx'),
            models.Index(fields=['agent', 'created_at'], name='tx_agent_created_idx'),
            models.Index(fields=['transaction_type'], name='tx_type_idx'),
        ]

    def __str__(self):
        return self.transaction_number


class Client(models.Model):
    name       = models.CharField(max_length=255)
    phone      = models.CharField(max_length=25, db_index=True)
    email      = models.EmailField(null=True, blank=True)
    country    = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL, db_column='country_id')
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, db_column='created_by_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed  = True
        db_table = 'logistics_clients'
        ordering = ['name']
        indexes = [
            models.Index(fields=['phone'], name='client_phone_idx'),
            models.Index(fields=['name'], name='client_name_idx'),
        ]

    def __str__(self):
        return self.name


class ClientAddress(models.Model):
    SOURCE_GEOCODED   = 'geocoded'
    SOURCE_MANUAL     = 'manual'
    SOURCE_UNRESOLVED = 'unresolved'
    SOURCE_CHOICES = [
        ('geocoded', 'Geocoded'),
        ('manual', 'Manual'),
        ('unresolved', 'Unresolved'),
    ]

    client         = models.ForeignKey(Client, related_name='addresses', on_delete=models.CASCADE, db_column='client_id')
    label          = models.CharField(max_length=60, default='Autre')
    address_line   = models.CharField(max_length=255)
    city           = models.CharField(max_length=120, null=True, blank=True)
    country        = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL, db_column='country_id')
    latitude       = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude      = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lat_lng_source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='unresolved')
    is_default     = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        managed  = True
        db_table = 'logistics_client_addresses'
        ordering = ['-is_default', 'label']
        indexes = [
            models.Index(fields=['client'], name='client_addr_client_idx'),
        ]

    def __str__(self):
        return f"{self.label} — {self.address_line}"

    def has_coordinates(self):
        return self.latitude is not None and self.longitude is not None


class ClientNote(models.Model):
    client     = models.ForeignKey(Client, related_name='notes', on_delete=models.CASCADE, db_column='client_id')
    author     = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, db_column='author_id')
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed  = True
        db_table = 'logistics_client_notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'created_at'], name='client_note_client_idx'),
        ]

    def __str__(self):
        return f"Note on {self.client_id} ({self.created_at:%Y-%m-%d})"


class Delivery(models.Model):
    TYPE_PICKUP  = 'pickup'
    TYPE_DROPOFF = 'dropoff'
    TASK_TYPE_CHOICES = [('pickup', 'Pickup'), ('dropoff', 'Drop-off')]

    STATUS_PENDING    = 'pending'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_DELAYED    = 'delayed'
    STATUS_COMPLETED  = 'completed'
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('delayed', 'Delayed'),
        ('completed', 'Completed'),
    ]

    PAYMENT_CASH  = 'cash'
    PAYMENT_OTHER = 'other'
    PAYMENT_METHOD_CHOICES = [('cash', 'Cash'), ('other', 'Autre')]

    client      = models.ForeignKey(Client, on_delete=models.PROTECT, db_column='client_id')
    address     = models.ForeignKey(ClientAddress, null=True, blank=True, on_delete=models.PROTECT, db_column='address_id')
    transaction = models.ForeignKey(Transaction, null=True, blank=True, on_delete=models.SET_NULL, related_name='deliveries', db_column='transaction_id')
    task_type   = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='pickup')
    scheduled_at = models.DateTimeField()
    driver      = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='deliveries_driven', db_column='driver_id')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes       = models.TextField(null=True, blank=True)
    # Free-text address as reported/corrected on the ground (by the driver or
    # the dispatcher) — kept separate from the client's saved ClientAddress
    # so correcting it here never silently rewrites the client's profile.
    address_note          = models.TextField(null=True, blank=True)
    amount                = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    payment_method        = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_method_other  = models.CharField(max_length=100, null=True, blank=True)
    created_by  = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', db_column='created_by_id')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        managed  = True
        db_table = 'logistics_deliveries'
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_at'], name='delivery_status_sched_idx'),
            models.Index(fields=['driver', 'scheduled_at'], name='delivery_driver_sched_idx'),
            models.Index(fields=['task_type'], name='delivery_task_type_idx'),
        ]

    def __str__(self):
        return f"{self.get_task_type_display()} — {self.client.name}"


class LogisticsImportBatch(models.Model):
    FILE_CSV  = 'csv'
    FILE_XLSX = 'xlsx'
    FILE_TYPE_CHOICES = [('csv', 'CSV'), ('xlsx', 'Excel')]

    STATUS_PENDING_MAPPING = 'pending_mapping'
    STATUS_COMPLETED       = 'completed'
    STATUS_FAILED          = 'failed'
    STATUS_CHOICES = [
        ('pending_mapping', 'Pending Mapping'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    uploaded_by       = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, db_column='uploaded_by_id')
    original_filename = models.CharField(max_length=255)
    file_type         = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    raw_rows          = models.JSONField()
    column_mapping    = models.JSONField(null=True, blank=True)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_mapping')
    created_count     = models.IntegerField(default=0)
    error_log         = models.TextField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        managed  = True
        db_table = 'logistics_import_batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"Import {self.original_filename} ({self.status})"


class AgentReport(models.Model):
    STATUS_CHOICES = [('unread', 'Unread'), ('read', 'Read')]

    agent       = models.ForeignKey(User, on_delete=models.CASCADE, db_column='agent_id')
    subject     = models.CharField(max_length=150)
    message     = models.TextField()
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unread')
    admin_reply = models.TextField(null=True, blank=True)
    replied_at  = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        managed  = True
        db_table = 'agent_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='report_status_created_idx'),
            models.Index(fields=['agent', 'created_at'], name='report_agent_created_idx'),
        ]

    def __str__(self):
        return self.subject


class ForumMessage(models.Model):
    """A flat, company-wide message wall — every active user (admin or
    agent) can post and everyone sees the same feed. No threading, no
    per-conversation scoping; deliberately simple."""
    author     = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, db_column='author_id')
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed  = True
        db_table = 'forum_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at'], name='forum_msg_created_idx'),
        ]

    def __str__(self):
        return f'{self.author}: {self.body[:40]}'
