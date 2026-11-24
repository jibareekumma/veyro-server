

from rest_framework.permissions import BasePermission


class IsStaffMember(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_staff_member)


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.role == 'super_admin')


class CanManageParcels(BasePermission):
    allowed_roles = ('support', 'operations', 'super_admin')

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.is_staff_member
            and user.role in self.allowed_roles
        )