# Re-adds client_email after the earlier removal (0005) — the feature is
# being restored now that direct SMTP is viable (paid PythonAnywhere plan,
# no outbound whitelist restriction).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_remove_transaction_client_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='client_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
