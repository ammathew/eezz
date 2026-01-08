from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_add_skipped_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='FacebookConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField()),
                ('token_expires_at', models.DateTimeField(blank=True, null=True)),
                ('page_id', models.CharField(blank=True, max_length=64)),
                ('page_name', models.CharField(blank=True, max_length=255)),
                ('page_access_token', models.TextField(blank=True)),
                ('ad_account_id', models.CharField(blank=True, max_length=64)),
                ('ad_account_name', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='facebook_connection', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
