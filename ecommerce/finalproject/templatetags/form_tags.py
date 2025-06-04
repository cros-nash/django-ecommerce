# File: form_tags.py
# Author: Crosby Nash (crosbyn@bu.edu), 12/26/2024
# Description: Defines custom template filters for dynamically adding CSS classes to form fields.

from django import template

# Register this module as a library of custom template tags/filters.
register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    """
    Allows the form field to be rendered as a widget with the specified CSS class.
    """
    return field.as_widget(attrs={"class": css})
