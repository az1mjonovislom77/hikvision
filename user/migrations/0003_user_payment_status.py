
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='payment_status',
            field=models.CharField(blank=True, choices=[('p', 'paid'), ('np', 'not paid')], max_length=10, null=True),
        ),
    ]
