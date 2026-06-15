from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_alter_attendancedaily_status'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='attendancedaily',
            index=models.Index(fields=['status'], name='attendance_status_idx'),
        ),
        migrations.AddIndex(
            model_name='attendancedaily',
            index=models.Index(fields=['date'], name='attendance_date_idx'),
        ),
    ]
