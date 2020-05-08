from django import template
import re

register = template.Library()

@register.filter(name='remove_leading_numbers_str')
def remove_leading_numbers_str(value):

	value = re.sub("^\d+(?:\.\d*)*", '', value).strip().lower()

	return value


@register.filter(name='remove_leading_numbers_list')
def remove_leading_numbers_list(list_items):

	list_items = list(map(lambda x: re.sub("^\d+(?:\.\d*)*", '', x).strip().lower(), list_items))

	return list_items
