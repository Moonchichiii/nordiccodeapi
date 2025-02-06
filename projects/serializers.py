from rest_framework import serializers
from .models import ProjectPackage, Addon, Project, ProjectAddon

class ProjectPackageSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProjectPackage model.
    Exposes read-only properties for price_eur and price_sek.
    """
    price_eur = serializers.FloatField(read_only=True)
    price_sek = serializers.FloatField(read_only=True)

    class Meta:
        model = ProjectPackage
        fields = [
            'id', 'type', 'name', 'price_eur', 'price_sek',
            'description', 'features', 'extra_features',
            'is_recommended', 'support_days'
        ]

class AddonSerializer(serializers.ModelSerializer):
    """
    Serializer for the Addon model.
    Returns the compatible packages as primary keys.
    """
    price_eur = serializers.FloatField(read_only=True)
    price_sek = serializers.FloatField(read_only=True)
    compatible_packages = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )

    class Meta:
        model = Addon
        fields = [
            'id', 'name', 'description',
            'price_eur', 'price_sek', 'compatible_packages'
        ]

class ProjectAddonSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProjectAddon (through) model.
    Uses the AddonSerializer to display addon details.
    """
    addon = AddonSerializer(read_only=True)

    class Meta:
        model = ProjectAddon
        fields = ['addon', 'is_included']

class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used when creating a new Project.
    Expects a package_id as a string (the package type, e.g. "enterprise")
    and a list of addon_ids.
    The total price is computed in cents.
    """
    package_id = serializers.CharField(write_only=True, required=True)
    addon_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=list
    )

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'requirements_doc',
            'package_id',
            'addon_ids',
        ]
        read_only_fields = ['id']

    def validate_package_id(self, package_id):
        try:
            package = ProjectPackage.objects.get(type=package_id)
            return package
        except ProjectPackage.DoesNotExist:
            raise serializers.ValidationError(f"Invalid package_id: {package_id}")

    def create(self, validated_data):
        addon_ids = validated_data.pop('addon_ids', [])
        # The validated package_id field now contains the Package instance
        package = validated_data.pop('package_id')

        # Initialize total price in cents using the package price
        total_price_eur_cents = package.price_eur_cents

        # Create the project; note that we save the total in cents
        project = Project.objects.create(
            **validated_data,
            package=package,
            total_price_eur_cents=total_price_eur_cents
        )

        # Process each addon, add its price if not included by default
        for addon_id in addon_ids:
            try:
                addon = Addon.objects.get(pk=addon_id, is_active=True)
                # Determine if the addon is included by default (for enterprise packages)
                included = (
                    project.package.type == 'enterprise' and
                    addon.compatible_packages.filter(type='enterprise').exists()
                )
                ProjectAddon.objects.create(
                    project=project,
                    addon=addon,
                    is_included=included
                )
                # If the addon is not included, add its price (in cents) to the total
                if not included:
                    total_price_eur_cents += addon.price_eur_cents
            except Addon.DoesNotExist:
                continue

        # Update the project's total price if any addon prices were added
        if total_price_eur_cents != project.total_price_eur_cents:
            project.total_price_eur_cents = total_price_eur_cents
            project.save()

        return project

class ProjectDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying detailed Project data.
    Includes nested package and addon information.
    """
    package = ProjectPackageSerializer(read_only=True)
    addons = ProjectAddonSerializer(source='projectaddon_set', many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    total_price_eur = serializers.FloatField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'user_email', 'package', 'addons',
            'title', 'description', 'status', 'requirements_doc',
            'start_date', 'target_completion_date',
            'is_planning_completed', 'is_planning_locked',
            'total_price_eur', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user_email', 'total_price_eur', 'created_at', 'updated_at']
