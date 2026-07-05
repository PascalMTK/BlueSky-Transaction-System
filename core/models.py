from django.db import models


class Country(models.Model):
    name                    = models.CharField(max_length=100)
    code                    = models.CharField(max_length=2, unique=True)
    currency_code           = models.CharField(max_length=5)
    currency_name           = models.CharField(max_length=60)
    flag_emoji              = models.CharField(max_length=10)
    phone_code              = models.CharField(max_length=10)
    default_fee_percentage  = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)
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
    STATUS_CHOICES = [('active', 'Active'), ('pending', 'Pending'), ('inactive', 'Inactive'), ('deleted', 'Supprimé')]

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
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        managed  = True
        db_table = 'users'

    def __str__(self):
        return self.name

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_agent(self):
        return self.role == self.ROLE_AGENT

    def is_active_user(self):
        return self.status == self.STATUS_ACTIVE

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
    destination_country = models.ForeignKey(Country, related_name='incoming', on_delete=models.PROTECT, db_column='destination_country_id')
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

    def __str__(self):
        return self.transaction_number


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

    def __str__(self):
        return self.subject
