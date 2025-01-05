from django_filters import rest_framework as filters
from rest_framework import generics

from .models import Project
from .serializers import ProjectSerializer

# Create your views here.


class ProjectFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="category", lookup_expr="iexact")
    featured = filters.BooleanFilter(field_name="featured")

    class Meta:
        model = Project
        fields = ["category", "featured"]


class ProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    filterset_class = ProjectFilter
    queryset = Project.objects.all()


class ProjectDetailView(generics.RetrieveAPIView):
    """API view to retrieve a single project by ID."""

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
