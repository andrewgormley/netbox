from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

from core.models import ObjectType
from netbox.api.fields import ContentTypeField
from netbox.api.serializers import WritableNestedSerializer
from users.models import Group, ObjectPermission, Token

__all__ = [
    'NestedGroupSerializer',
    'NestedObjectPermissionSerializer',
    'NestedTokenSerializer',
    'NestedUserSerializer',
]


class NestedGroupSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users-api:group-detail')
    display_url = serializers.HyperlinkedIdentityField(view_name='users:group-detail')

    class Meta:
        model = Group
        fields = ['id', 'url', 'display_url', 'display', 'name']


class NestedUserSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users-api:user-detail')
    display_url = serializers.HyperlinkedIdentityField(view_name='users:user-detail')

    class Meta:
        model = get_user_model()
        fields = ['id', 'url', 'display_url', 'display', 'username']

    @extend_schema_field(OpenApiTypes.STR)
    def get_display(self, obj):
        if full_name := obj.get_full_name():
            return f"{obj.username} ({full_name})"
        return obj.username


class NestedTokenSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users-api:token-detail')
    display_url = serializers.HyperlinkedIdentityField(view_name='users:token-detail')

    class Meta:
        model = Token
        fields = ['id', 'url', 'display_url', 'display', 'key', 'write_enabled']


class NestedObjectPermissionSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users-api:objectpermission-detail')
    display_url = serializers.HyperlinkedIdentityField(view_name='users:objectpermission-detail')
    object_types = ContentTypeField(
        queryset=ObjectType.objects.all(),
        many=True
    )
    groups = serializers.SerializerMethodField(read_only=True)
    users = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ObjectPermission
        fields = [
            'id', 'url', 'display_url', 'display', 'name', 'enabled', 'object_types', 'groups', 'users', 'actions'
        ]

    @extend_schema_field(serializers.ListField)
    def get_groups(self, obj):
        return [g.name for g in obj.groups.all()]

    @extend_schema_field(serializers.ListField)
    def get_users(self, obj):
        return [u.username for u in obj.users.all()]
