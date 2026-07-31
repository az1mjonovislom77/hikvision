
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0009_alter_employee_employee_no'),
        ('utils', '0006_telegramchannel'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='employee',
            unique_together={('device', 'employee_no')},
        ),
    ]
