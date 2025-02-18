from django.db import migrations

def create_default_packages(apps, schema_editor):
    ProjectPackage = apps.get_model('projects', 'ProjectPackage')
    default_packages = [
        {
            'type': 'static',
            'name': 'Static Frontend',
            'price_eur_cents': 60000,
            'price_sek_ore': 6300,
            'description': 'Modern TypeScript-based front end with responsive design and basic on-page SEO.',
            'features': ['Modern TypeScript-based front end', 'Responsive design', 'Basic on-page SEO'],
            'extra_features': [
                'Developer-built React/TypeScript application',
                'Vite-based build for speed',
                '14 days of developer support',
            ],
            'is_recommended': False,
            'support_days': 14,
        },
        {
            'type': 'fullstack',
            'name': 'Full Stack',
            'price_eur_cents': 110000,
            'price_sek_ore': 112000,
            'description': 'Includes everything in Static Frontend plus Django-based back end and database integration.',
            'features': [
                'Everything in Static Frontend',
                'Django-based back end',
                'Database integration & API endpoints',
            ],
            'extra_features': [
                'Secure authentication (session-based)',
                'Admin dashboard & management tools',
                '30 days developer support',
            ],
            'is_recommended': True,
            'support_days': 30,
        },
        {
            'type': 'enterprise',
            'name': 'Enterprise',
            'price_eur_cents': 200000,
            'price_sek_ore': 202000,
            'description': 'All features of Full Stack plus advanced security, cloud infrastructure, and premium support.',
            'features': [
                'Everything in Full Stack',
                'Advanced security & authentication',
                'Cloud infrastructure & deployment',
            ],
            'extra_features': [
                'High-performance database optimization',
                'Load balancing configuration',
                '45 days premium support',
                'CI/CD pipeline setup',
            ],
            'is_recommended': False,
            'support_days': 45,
        },
    ]
    for pkg in default_packages:
        ProjectPackage.objects.get_or_create(type=pkg['type'], defaults=pkg)

def remove_default_packages(apps, schema_editor):
    ProjectPackage = apps.get_model('projects', 'ProjectPackage')
    ProjectPackage.objects.filter(type__in=['static', 'fullstack', 'enterprise']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(create_default_packages, remove_default_packages),
    ]
