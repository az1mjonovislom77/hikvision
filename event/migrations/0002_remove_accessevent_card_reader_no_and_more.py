
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accessevent',
            name='card_reader_no',
        ),
        migrations.RemoveField(
            model_name='accessevent',
            name='card_type',
        ),
        migrations.RemoveField(
            model_name='accessevent',
            name='door_no',
        ),
        migrations.RemoveField(
            model_name='accessevent',
            name='mask',
        ),
        migrations.RemoveField(
            model_name='accessevent',
            name='user_type',
        ),
        migrations.RemoveField(
            model_name='accessevent',
            name='verify_mode',
        ),
    ]
