
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0014_employee_is_fine'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='employeehistory',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
