
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0015_alter_employee_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='begin_time',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
