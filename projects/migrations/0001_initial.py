# Generated by Django 5.1.5 on 2025-01-23 19:08

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Project title', max_length=200)),
                ('description', models.TextField(help_text='Detailed project description')),
                ('client_specifications', models.FileField(blank=True, help_text='Client-provided documents (PDF, DOC, DOCX)', null=True, upload_to='client_specs/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])])),
                ('status', models.CharField(choices=[('planning', 'Planning Phase'), ('pending_payment', 'Pending Payment'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='planning', help_text='Current project status', max_length=20)),
                ('planning_completed', models.BooleanField(default=False)),
                ('planning_locked', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Project creation timestamp')),
            ],
            options={
                'verbose_name': 'Project',
                'verbose_name_plural': 'Projects',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProjectPackage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('enterprise', 'Enterprise Full-Stack Solution'), ('mid_tier', 'Mid-Tier Solution'), ('static', 'Static Frontend Solution')], help_text='Type of project package', max_length=50, unique=True)),
                ('base_price', models.DecimalField(decimal_places=2, help_text='Base price for the package', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('features', models.JSONField(default=dict, help_text='Package features in JSON format')),
                ('tech_stack', models.JSONField(default=list, help_text='Technologies used in this package')),
                ('deliverables', models.JSONField(default=list, help_text='Project deliverables')),
                ('estimated_duration', models.PositiveIntegerField(help_text='Estimated duration in days', validators=[django.core.validators.MinValueValidator(1)])),
                ('maintenance_period', models.PositiveIntegerField(default=30, help_text='Support period in days', validators=[django.core.validators.MinValueValidator(1)])),
                ('sla_response_time', models.PositiveIntegerField(default=24, help_text='Response time in hours', validators=[django.core.validators.MinValueValidator(1)])),
            ],
            options={
                'verbose_name': 'Project Package',
                'verbose_name_plural': 'Project Packages',
                'ordering': ['base_price'],
            },
        ),
    ]
