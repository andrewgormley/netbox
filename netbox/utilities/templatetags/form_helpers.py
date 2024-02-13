from django import template


__all__ = (
    'getfield',
    'getfilterfield',
    'render_custom_fields',
    'render_errors',
    'render_field',
    'render_form',
    'widget_type',
)

from utilities.templatetags.helpers import querystring

register = template.Library()


#
# Filters
#

@register.filter()
def getfield(form, fieldname):
    """
    Return the specified bound field of a Form.
    """
    try:
        return form[fieldname]
    except KeyError:
        return None


@register.filter()
def getfilterfield(form, fieldname):
    field = getfield(form, f'{fieldname}')
    if field is not None:
        return field
    else:
        return getfield(form, f'{fieldname}_id')


@register.filter(name='widget_type')
def widget_type(field):
    """
    Return the widget type
    """
    if hasattr(field, 'widget'):
        return field.widget.__class__.__name__.lower()
    elif hasattr(field, 'field'):
        return field.field.widget.__class__.__name__.lower()
    else:
        return None


#
# Inclusion tags
#

@register.inclusion_tag('form_helpers/render_field.html')
def render_field(field, bulk_nullable=False, label=None):
    """
    Render a single form field from template
    """

    return {
        'field': field,
        'label': label or field.label,
        'bulk_nullable': bulk_nullable,
    }


@register.inclusion_tag('form_helpers/render_field.html')
def render_table_filter_field(field, table=None, request=None):
    """
    Render a single form field for table column filters from template
    """
    url = ""

    # Handle filter forms
    if table:
        # Build kwargs for querystring function
        kwargs = {field.name: None}
        # Build request url
        if request and table.htmx_url:
            url = table.htmx_url + querystring(request, **kwargs)
        elif request:
            url = querystring(request, **kwargs)
        # Set HTMX args

    if hasattr(field.field, 'widget'):
        field.field.widget.attrs.update({
            'id': f'table_filter_id_{field.name}',
            'hx-get': url if url else '#',
            'hx-push-url': "true",
            'hx-target': '#object_list',
            'hx-trigger': 'hidden.bs.dropdown from:closest .dropdown'
        })

    return {
        'field': field,
        'label': None,
        'bulk_nullable': False,
    }


@register.inclusion_tag('form_helpers/render_custom_fields.html')
def render_custom_fields(form):
    """
    Render all custom fields in a form
    """
    return {
        'form': form,
    }


@register.inclusion_tag('form_helpers/render_form.html')
def render_form(form):
    """
    Render an entire form from template
    """
    return {
        'form': form,
    }


@register.inclusion_tag('form_helpers/render_errors.html')
def render_errors(form):
    """
    Render form errors, if they exist.
    """
    return {
        "form": form
    }
