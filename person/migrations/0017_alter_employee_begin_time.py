
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0016_alter_employee_begin_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='begin_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
