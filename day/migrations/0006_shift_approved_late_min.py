
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('day', '0005_breaktime_created_at_dayoff_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='approved_late_min',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
