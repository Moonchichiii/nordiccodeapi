# Generated by Django 5.1.5 on 2025-02-10 23:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('billing', '0001_initial'),
        ('projects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentmethod',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_methods', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='paymentplan',
            name='project',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment_plan', to='projects.project'),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='billing.paymentplan'),
        ),
        migrations.AddConstraint(
            model_name='paymentmethod',
            constraint=models.UniqueConstraint(condition=models.Q(('is_default', True)), fields=('user',), name='unique_default_payment_method'),
        ),
    ]
