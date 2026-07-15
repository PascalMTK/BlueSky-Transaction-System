from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0008_user_last_seen'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['role', 'status'], name='user_role_status_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['country', 'status'], name='user_country_status_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['status', 'created_at'], name='tx_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['agent', 'created_at'], name='tx_agent_created_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['transaction_type'], name='tx_type_idx'),
        ),
        migrations.AddIndex(
            model_name='agentreport',
            index=models.Index(fields=['status', 'created_at'], name='report_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='agentreport',
            index=models.Index(fields=['agent', 'created_at'], name='report_agent_created_idx'),
        ),
    ]
