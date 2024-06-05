from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from netbox.api.serializers import WritableNestedSerializer
from tenancy.models import *

__all__ = [
    'NestedContactSerializer',
    'NestedContactAssignmentSerializer',
    'NestedContactGroupSerializer',
    'NestedContactRoleSerializer',
    'NestedTenantGroupSerializer',
    'NestedTenantSerializer',
]


#
# Tenants
#

@extend_schema_serializer(
    exclude_fields=('tenant_count',),
)
class NestedTenantGroupSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='tenancy-api:tenantgroup-detail')
    display_url = serializers.HyperlinkedIdentityField(view_name='tenancy:tenantgroup')
    tenant_count = serializers.IntegerField(read_only=True)
    _depth = serializers.IntegerField(source='level', read_only=True)

    class Meta:
        model = TenantGroup
        fields = ['id', 'url', 'display_url', 'display', 'name', 'slug', 'tenant_count', '_depth']


class NestedTenantSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='tenancy-api:tenant-detail')
    display_url = serializers.HyperlinkedIdentityField(view_name='tenancy:tenant')

    class Meta:
        model = Tenant
        fields = ['id', 'url', 'display_url', 'display', 'name', 'slug']


#
# Contacts
#

@extend_schema_serializer(
    exclude_fields=('contact_count',),
)
class NestedContactGroupSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='tenancy-api:contactgroup-detail')
    display_url = serializers.HyperlinkedIdentityField(view_name='tenancy:contactgroup')
    contact_count = serializers.IntegerField(read_only=True)
    _depth = serializers.IntegerField(source='level', read_only=True)

    class Meta:
        model = ContactGroup
        fields = ['id', 'url', 'display_url', 'display', 'name', 'slug', 'contact_count', '_depth']


class NestedContactRoleSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='tenancy-api:contactrole-detail')
    display_url = serializers.HyperlinkedIdentityField(view_name='tenancy:contactrole')

    class Meta:
        model = ContactRole
        fields = ['id', 'url', 'display_url', 'display', 'name', 'slug']


class NestedContactSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='tenancy-api:contact-detail')
    display_url = serializers.HyperlinkedIdentityField(view_name='tenancy:contact')

    class Meta:
        model = Contact
        fields = ['id', 'url', 'display_url', 'display', 'name']


class NestedContactAssignmentSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='tenancy-api:contactassignment-detail')
    display_url = serializers.CharField(allow_null=True, read_only=True)
    contact = NestedContactSerializer()
    role = NestedContactRoleSerializer

    class Meta:
        model = ContactAssignment
        fields = ['id', 'url', 'display_url', 'display', 'contact', 'role', 'priority']
