
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('day', '0002_breaktime_user_dayoff_user_shift_user_workday_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dayoff',
            name='days',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='workday',
            name='days',
            field=models.JSONField(default=list),
        ),
    ]
