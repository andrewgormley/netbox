from rest_framework import serializers

from core.models import ObjectType
from netbox.api.fields import ContentTypeField, SerializedPKRelatedField
from netbox.api.serializers import ValidatedModelSerializer
from users.api.nested_serializers import NestedGroupSerializer, NestedUserSerializer
from users.models import Group, ObjectPermission, User

__all__ = (
    'ObjectPermissionSerializer',
)


class ObjectPermissionSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users-api:objectpermission-detail')
    display_url = serializers.HyperlinkedIdentityField(view_name='users:objectpermission')
    object_types = ContentTypeField(
        queryset=ObjectType.objects.all(),
        many=True
    )
    groups = SerializedPKRelatedField(
        queryset=Group.objects.all(),
        serializer=NestedGroupSerializer,
        nested=True,
        required=False,
        many=True
    )
    users = SerializedPKRelatedField(
        queryset=User.objects.all(),
        serializer=NestedUserSerializer,
        nested=True,
        required=False,
        many=True
    )

    class Meta:
        model = ObjectPermission
        fields = (
            'id', 'url', 'display_url', 'display', 'name', 'description', 'enabled', 'object_types', 'actions',
            'constraints', 'groups', 'users',
        )
        brief_fields = (
            'id', 'url', 'display', 'name', 'description', 'enabled', 'object_types', 'actions',
        )
