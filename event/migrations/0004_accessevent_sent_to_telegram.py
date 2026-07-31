
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0003_accessevent_employee'),
    ]

    operations = [
        migrations.AddField(
            model_name='accessevent',
            name='sent_to_telegram',
            field=models.BooleanField(default=False),
        ),
    ]
