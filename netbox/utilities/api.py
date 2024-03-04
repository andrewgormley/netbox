import platform
import sys

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import (
    FieldDoesNotExist, FieldError, MultipleObjectsReturned, ObjectDoesNotExist, ValidationError,
)
from django.db.models.fields.related import ManyToOneRel, RelatedField
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.serializers import Serializer
from rest_framework.utils import formatting

from netbox.api.fields import RelatedObjectCountField
from netbox.api.exceptions import GraphQLTypeNotFound, SerializerNotFound
from .utils import count_related, dict_to_filter_params, dynamic_import

__all__ = (
    'get_annotations_for_serializer',
    'get_graphql_type_for_model',
    'get_prefetches_for_serializer',
    'get_related_object_by_attrs',
    'get_serializer_for_model',
    'get_view_name',
    'is_api_request',
    'rest_api_server_error',
)


def get_serializer_for_model(model, prefix=''):
    """
    Dynamically resolve and return the appropriate serializer for a model.
    """
    app_label, model_name = model._meta.label.split('.')
    serializer_name = f'{app_label}.api.serializers.{prefix}{model_name}Serializer'
    try:
        return dynamic_import(serializer_name)
    except AttributeError:
        raise SerializerNotFound(
            f"Could not determine serializer for {app_label}.{model_name} with prefix '{prefix}'"
        )


def get_graphql_type_for_model(model):
    """
    Return the GraphQL type class for the given model.
    """
    app_name, model_name = model._meta.label.split('.')
    # Object types for Django's auth models are in the users app
    if app_name == 'auth':
        app_name = 'users'
    class_name = f'{app_name}.graphql.types.{model_name}Type'
    try:
        return dynamic_import(class_name)
    except AttributeError:
        raise GraphQLTypeNotFound(f"Could not find GraphQL type for {app_name}.{model_name}")


def is_api_request(request):
    """
    Return True of the request is being made via the REST API.
    """
    api_path = reverse('api-root')

    return request.path_info.startswith(api_path) and request.content_type == 'application/json'


def get_view_name(view, suffix=None):
    """
    Derive the view name from its associated model, if it has one. Fall back to DRF's built-in `get_view_name`.
    """
    if hasattr(view, 'queryset'):
        # Determine the model name from the queryset.
        name = view.queryset.model._meta.verbose_name
        name = ' '.join([w[0].upper() + w[1:] for w in name.split()])  # Capitalize each word

    else:
        # Replicate DRF's built-in behavior.
        name = view.__class__.__name__
        name = formatting.remove_trailing_string(name, 'View')
        name = formatting.remove_trailing_string(name, 'ViewSet')
        name = formatting.camelcase_to_spaces(name)

    if suffix:
        name += ' ' + suffix

    return name


def get_prefetches_for_serializer(serializer_class, fields_to_include=None):
    """
    Compile and return a list of fields which should be prefetched on the queryset for a serializer.
    """
    model = serializer_class.Meta.model

    # If fields are not specified, default to all
    if not fields_to_include:
        fields_to_include = serializer_class.Meta.fields

    prefetch_fields = []
    for field_name in fields_to_include:
        serializer_field = serializer_class._declared_fields.get(field_name)

        # Determine the name of the model field referenced by the serializer field
        model_field_name = field_name
        if serializer_field and serializer_field.source:
            model_field_name = serializer_field.source

        # If the serializer field does not map to a discrete model field, skip it.
        try:
            field = model._meta.get_field(model_field_name)
            if isinstance(field, (RelatedField, ManyToOneRel, GenericForeignKey)):
                prefetch_fields.append(field.name)
        except FieldDoesNotExist:
            continue

        # If this field is represented by a nested serializer, recurse to resolve prefetches
        # for the related object.
        if serializer_field:
            if issubclass(type(serializer_field), Serializer):
                # Determine which fields to prefetch for the nested object
                subfields = serializer_field.Meta.brief_fields if serializer_field.nested else None
                for subfield in get_prefetches_for_serializer(type(serializer_field), subfields):
                    prefetch_fields.append(f'{field_name}__{subfield}')

    return prefetch_fields


def get_annotations_for_serializer(serializer_class, fields_to_include=None):
    """
    Return a mapping of field names to annotations to be applied to the queryset for a serializer.
    """
    annotations = {}

    # If specific fields are not specified, default to all
    if not fields_to_include:
        fields_to_include = serializer_class.Meta.fields

    model = serializer_class.Meta.model

    for field_name, field in serializer_class._declared_fields.items():
        if field_name in fields_to_include and type(field) is RelatedObjectCountField:
            related_field = model._meta.get_field(field.relation).field
            annotations[field_name] = count_related(related_field.model, related_field.name)

    return annotations


def get_related_object_by_attrs(queryset, attrs):
    """
    Return an object identified by either a dictionary of attributes or its numeric primary key (ID). This is used
    for referencing related objects when creating/updating objects via the REST API.
    """
    if attrs is None:
        return None

    # Dictionary of related object attributes
    if isinstance(attrs, dict):
        params = dict_to_filter_params(attrs)
        try:
            return queryset.get(**params)
        except ObjectDoesNotExist:
            raise ValidationError(
                _("Related object not found using the provided attributes: {params}").format(params=params))
        except MultipleObjectsReturned:
            raise ValidationError(
                _("Multiple objects match the provided attributes: {params}").format(params=params)
            )
        except FieldError as e:
            raise ValidationError(e)

    # Integer PK of related object
    try:
        # Cast as integer in case a PK was mistakenly sent as a string
        pk = int(attrs)
    except (TypeError, ValueError):
        raise ValidationError(
            _(
                "Related objects must be referenced by numeric ID or by dictionary of attributes. Received an "
                "unrecognized value: {value}"
            ).format(value=attrs)
        )

    # Look up object by PK
    try:
        return queryset.get(pk=pk)
    except ObjectDoesNotExist:
        raise ValidationError(_("Related object not found using the provided numeric ID: {id}").format(id=pk))


def rest_api_server_error(request, *args, **kwargs):
    """
    Handle exceptions and return a useful error message for REST API requests.
    """
    type_, error, traceback = sys.exc_info()
    data = {
        'error': str(error),
        'exception': type_.__name__,
        'netbox_version': settings.VERSION,
        'python_version': platform.python_version(),
    }
    return JsonResponse(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
