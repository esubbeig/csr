from django.core.exceptions import ValidationError
import os


def validate_file_type(f):
	ext = os.path.splitext(f.name)[1]
	valid_extensions = ['.docx']
	if ext.lower() not in valid_extensions:
		raise ValidationError('file must be .docx formate!')

def validate_project_name(value):
	if value == '':
		raise ValidationError('this field not be blank')
	return value