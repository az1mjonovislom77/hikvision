from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0017_alter_employee_begin_time'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['device'], name='person_emp_device_idx'),
        ),
    ]
