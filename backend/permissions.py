from rest_framework.permissions import BasePermission

class IsOrderOwner(BasePermission):
    """
    Checks if the user making the request owns the Order object (ProjectOrder).
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsProjectOwner(BasePermission):
    """
    Checks if the user making the request owns the Project object.
    A Project references 'order_link' (OneToOneField to orders.ProjectOrder).
    """
    def has_object_permission(self, request, view, obj):
        # If the project is linked to an order, check if that order belongs to the user.
        if obj.order_link:
            return obj.order_link.user == request.user
        return False
