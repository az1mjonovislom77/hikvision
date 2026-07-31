
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0011_employeehistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeehistory',
            name='label_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
