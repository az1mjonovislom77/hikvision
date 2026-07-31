
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0008_delete_employeehistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramchannel',
            name='resolve_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
