from rest_framework import permissions

class IsAdminOrOwnerOrReadOnly(permissions.BasePermission):
    """
    Only admins or product owners can edit/delete.
    Everyone else can read.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            request.user.is_admin or obj.created_by == request.user
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Customers can access only their own cart/orders.
    Admins can see all.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.is_admin or obj.user == request.user
