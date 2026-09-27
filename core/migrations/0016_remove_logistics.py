# Removes the logistics module (clients, addresses, notes, deliveries, imports).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_user_forum_last_read_at'),
    ]

    operations = [
        migrations.DeleteModel(name='Delivery'),
        migrations.DeleteModel(name='ClientNote'),
        migrations.DeleteModel(name='ClientAddress'),
        migrations.DeleteModel(name='LogisticsImportBatch'),
        migrations.DeleteModel(name='Client'),
    ]
