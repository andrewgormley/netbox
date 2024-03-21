from urllib.parse import urlencode

from django.db.models import Count, ManyToOneRel, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.http import QueryDict
from django.utils import timezone
from django.utils.datastructures import MultiValueDict
from django.utils.timezone import localtime

from .string import title


def dynamic_import(name):
    """
    Dynamically import a class from an absolute path string
    """
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def count_related(model, field):
    """
    Return a Subquery suitable for annotating a child object count.
    """
    subquery = Subquery(
        model.objects.filter(
            **{field: OuterRef('pk')}
        ).order_by().values(
            field
        ).annotate(
            c=Count('*')
        ).values('c')
    )

    return Coalesce(subquery, 0)


def dict_to_filter_params(d, prefix=''):
    """
    Translate a dictionary of attributes to a nested set of parameters suitable for QuerySet filtering. For example:

        {
            "name": "Foo",
            "rack": {
                "facility_id": "R101"
            }
        }

    Becomes:

        {
            "name": "Foo",
            "rack__facility_id": "R101"
        }

    And can be employed as filter parameters:

        Device.objects.filter(**dict_to_filter(attrs_dict))
    """
    params = {}
    for key, val in d.items():
        k = prefix + key
        if isinstance(val, dict):
            params.update(dict_to_filter_params(val, k + '__'))
        else:
            params[k] = val
    return params


def dict_to_querydict(d, mutable=True):
    """
    Create a QueryDict instance from a regular Python dictionary.
    """
    qd = QueryDict(mutable=True)
    for k, v in d.items():
        item = MultiValueDict({k: v}) if isinstance(v, (list, tuple, set)) else {k: v}
        qd.update(item)
    if not mutable:
        qd._mutable = False
    return qd


def normalize_querydict(querydict):
    """
    Convert a QueryDict to a normal, mutable dictionary, preserving list values. For example,

        QueryDict('foo=1&bar=2&bar=3&baz=')

    becomes:

        {'foo': '1', 'bar': ['2', '3'], 'baz': ''}

    This function is necessary because QueryDict does not provide any built-in mechanism which preserves multiple
    values.
    """
    return {
        k: v if len(v) > 1 else v[0] for k, v in querydict.lists()
    }


def prepare_cloned_fields(instance):
    """
    Generate a QueryDict comprising attributes from an object's clone() method.
    """
    # Generate the clone attributes from the instance
    if not hasattr(instance, 'clone'):
        return QueryDict(mutable=True)
    attrs = instance.clone()

    # Prepare querydict parameters
    params = []
    for key, value in attrs.items():
        if type(value) in (list, tuple):
            params.extend([(key, v) for v in value])
        elif value not in (False, None):
            params.append((key, value))
        else:
            params.append((key, ''))

    # Return a QueryDict with the parameters
    return QueryDict(urlencode(params), mutable=True)


def content_type_name(ct, include_app=True):
    """
    Return a human-friendly ContentType name (e.g. "DCIM > Site").
    """
    try:
        meta = ct.model_class()._meta
        app_label = title(meta.app_config.verbose_name)
        model_name = title(meta.verbose_name)
        if include_app:
            return f'{app_label} > {model_name}'
        return model_name
    except AttributeError:
        # Model no longer exists
        return f'{ct.app_label} > {ct.model}'


def content_type_identifier(ct):
    """
    Return a "raw" ContentType identifier string suitable for bulk import/export (e.g. "dcim.site").
    """
    return f'{ct.app_label}.{ct.model}'


def local_now():
    """
    Return the current date & time in the system timezone.
    """
    return localtime(timezone.now())


def get_related_models(model, ordered=True):
    """
    Return a list of all models which have a ForeignKey to the given model and the name of the field. For example,
    `get_related_models(Tenant)` will return all models which have a ForeignKey relationship to Tenant.
    """
    related_models = [
        (field.related_model, field.remote_field.name)
        for field in model._meta.related_objects
        if type(field) is ManyToOneRel
    ]

    if ordered:
        return sorted(related_models, key=lambda x: x[0]._meta.verbose_name.lower())

    return related_models
