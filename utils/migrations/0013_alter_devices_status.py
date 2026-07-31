
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0012_notification_delete_notifications'),
    ]

    operations = [
        migrations.AlterField(
            model_name='devices',
            name='status',
            field=models.CharField(choices=[('active', 'active'), ('inactive', 'inactive')], max_length=100),
        ),
    ]
