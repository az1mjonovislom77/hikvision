from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0008_alter_accessevent_major_alter_accessevent_minor_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='accessevent',
            index=models.Index(fields=['employee'], name='event_acces_employe_idx'),
        ),
    ]
