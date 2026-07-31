
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendancedaily',
            name='status',
            field=models.CharField(choices=[('sbk', 'Sababli kelmadi'), ('szk', 'Sababsiz kelmadi')], max_length=30),
        ),
    ]
