
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0007_employeehistory'),
    ]

    operations = [
        migrations.DeleteModel(
            name='EmployeeHistory',
        ),
    ]
