from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .validators import validate_file_type
from .models import	*
import re

class SignUpForm(UserCreationForm):
	first_name = forms.CharField(max_length=30, required=True)
	email = forms.EmailField(max_length=254, required=True)

	class Meta:
		model = User
		fields = ('username', 'first_name', 'email',)

	def __init__(self, *args, **kwargs):
		super(SignUpForm, self).__init__(*args, **kwargs)
		self.fields['password1'].required = False
		self.fields['password2'].required = False
		self.fields['email'].required = True

	def clean_email(self):
		email  = self.cleaned_data['email']
		username = self.cleaned_data['username']
		if email and User.objects.filter(email=email).count() > 0:
			raise forms.ValidationError(u'This email address is already registered.')
		return email


class GlobalCsrUploadForm(forms.ModelForm):

	class Meta:
		model = CSRTemplate
		fields = ('csr_template_location', 'comments',)

	def clean_csr_template_location(self):
		csr_template_location = self.cleaned_data['csr_template_location']
		if str(csr_template_location).lower().endswith('.docx'):
			pass
		else:
			raise forms.ValidationError(u'Please Upload .docx file only!')
		return csr_template_location


class ProtocolUploadAdminForm(forms.ModelForm):

	class Meta:
		model = ProtocolAdmin
		fields = ('protocol_template_location', 'comments',)

	def clean_protocol_template_location(self):
		protocol_template_location = self.cleaned_data['protocol_template_location']
		if str(protocol_template_location).lower().endswith('.docx'):
			pass
		else:
			raise forms.ValidationError(u'Please Upload .docx file only!')
		return protocol_template_location


class SARUploadAdminForm(forms.ModelForm):

	class Meta:
		model = SARAdmin
		fields = ('sar_template_location', 'comments',)

	def clean_sar_template_location(self):
		sar_template_location = self.cleaned_data['sar_template_location']
		if str(sar_template_location).lower().endswith('.docx'):
			pass
		else:
			raise forms.ValidationError(u'Please Upload .docx file only!')
		return sar_template_location


class CsrUploadForm(forms.ModelForm):

	class Meta:
		model = CSRTemplateUser
		fields = ('csr_template_location', 'comments',)

	def clean_csr_template_location(self):
		csr_template_location = self.cleaned_data['csr_template_location']
		if str(csr_template_location).lower().endswith('.docx'):
			pass
		else:
			raise forms.ValidationError(u'Please Upload .docx file only!')
		return csr_template_location


class ProtocolFileUploadForm(forms.ModelForm):
	
	class Meta:
		model = ProtocolFileUpload
		fields = ('protocol_document_location', 'comments')

	def clean_protocol_document_location(self):
		protocol_document_location = self.cleaned_data['protocol_document_location']
		if str(protocol_document_location).lower().endswith('.docx'):
			pass
		else:
			raise forms.ValidationError(u'Please Upload .docx file only!')
		return protocol_document_location


class SarFileUploadForm(forms.ModelForm):
	
	class Meta:
		model = SarFileUpload
		fields = ('sar_document_location', 'comments')

	def clean_sar_document_location(self):
		sar_document_location = self.cleaned_data['sar_document_location']
		if str(sar_document_location).lower().endswith('.docx'):
			pass
		else:
			raise forms.ValidationError(u'Please Upload .docx file only!')
		return sar_document_location


class AnotherFileUploadUserForm(forms.ModelForm):
	
	class Meta:
		model = AnotherFileUploadUser
		fields = ('another_document_location', 'comments')

	def clean_another_document_location(self):
		another_document_location = self.cleaned_data['another_document_location']
		if str(another_document_location).lower().endswith('.docx'):
			pass
		else:
			raise forms.ValidationError(u'Please Upload .docx file only!')
		return another_document_location


class CreateProjectForm(forms.ModelForm):

	PH_OPTIONS = (
    		('1', '1'),
    		('2', '2'),
    		('3', '3'),
    		('4', '4'),
    		('Observational', 'Observational'),
    	)
	phase = forms.ChoiceField(required=True, choices=PH_OPTIONS)
	
	class Meta:
		model = ProjectInfo
		fields = ('project_name', 'client', 'protocol_id', 'therapeutic_area', 'phase',)

	def clean_project_name(self):
		regex = '^[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*$'
		data = self.cleaned_data.get('project_name')

		if not re.compile(r"^[a-zA-Z]+[a-zA-Z_]").match(data):
			raise forms.ValidationError("Enter a valid input. Should start with [a-zA-Z] & minimum length is two")

		return data


class EditProjectForm(forms.ModelForm):

	PH_OPTIONS = (
    		('1', '1'),
    		('2', '2'),
    		('3', '3'),
    		('4', '4'),
    		('Observational', 'Observational'),
    	)
	phase = forms.ChoiceField(required=True, choices=PH_OPTIONS)
	
	class Meta:
		model = ProjectInfo
		fields = ('project_name', 'client', 'protocol_id', 'therapeutic_area', 'phase',)

	def clean_project_name(self):
		regex = '^[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*$'
		data = self.cleaned_data.get('project_name')

		if not re.compile(r"^[a-zA-Z]+[a-zA-Z_]").match(data):
			raise forms.ValidationError("Enter a valid input. Should start with [a-zA-Z] & minimum length is two")

		return data



class EmailConfigurationForm(forms.ModelForm):

	class Meta:
		model = EmailConfiguration
		fields = ('email_host', 'email_host_user', 'email_host_password', 'email_port', 'email_default_mail')


class AddClientForm(forms.ModelForm):

	class Meta:
		model = ClientInfo
		fields = ('client_name',)

	def clean_client_name(self):

		client_name = self.cleaned_data.get('client_name')
		if not re.compile(r"^[a-zA-Z]{2,}").match(client_name):
			raise forms.ValidationError("Should contain only alphabets & min two characters.")
		return client_name