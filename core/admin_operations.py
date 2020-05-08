from django.contrib.auth.models import User
from datetime import datetime
from .models import *
import os
import pandas as pd
import numpy as np
import logging
import traceback
import re
from docx import Document
from .admin_csr_mapping import get_all_headings
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

csr_logger = logging.getLogger('csr')
csr_except_logger = logging.getLogger('csr_except')


def get_all_users():

	try:

		users = User.objects.all()
		return users

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


def get_all_users_active():

	try:

		users = User.objects.filter(is_active=True)
		return users

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


def get_all_project_list():

	try:

		projects = ProjectInfo.objects.all()
		return projects

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


#to record activity log
def record_user_activity_log(event, actor, **kwargs):

	try:

		raw_message = ActivityLogEvents.objects.get(event=event).message

		if event == 'Add User':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('dif_user'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Activate User':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('dif_user'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Deactivate User':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('dif_user'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Create Project':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('proj_name'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Assign Project':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('proj_name'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'CSR Upload':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('client'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Edit Project':
			temp_message = raw_message.replace('#', kwargs.get('proj_name')) + ' by ' + str(actor)
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Protocol Upload':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('proj_name'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'SAR Upload':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('proj_name'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Upload Protocol':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('client'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Upload SAR':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('client'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Custom CSR Upload':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('proj_name'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Generate CSR':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('proj_name'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Edit Custom CSR':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('proj_name'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'CSR Mapping':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('client'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Resend Email':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('email')).replace('$', kwargs.get('log_event'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Clear Configurations':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('client'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Configurations Clear':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('proj_name'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Another Document':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('proj_name')).replace('@', kwargs.get('source_name'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()

		elif event == 'Another Doc Upload':
			temp_message = str(actor) + ' ' + raw_message.replace('#', kwargs.get('proj_name')).replace('@', kwargs.get('source_name'))
			log_model 	 = LogsActivity(
				event 	 = event,
				message  = temp_message,
				userid 	 = actor.id,
				sessionid= kwargs.get('session_id')
				)
			log_model.save()


	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



def filtered_pre_mapped_admin_data(req_client):

	try:

		pre_mapped_headings = list(GlobalMappingTable.objects.filter(client=req_client).order_by('id').values())

		dataframe = pd.DataFrame(pre_mapped_headings, columns=['csr_heading', 'source_file', 'copy_headings', 'parent_id'])
		
		dataframe = dataframe.replace(r'^\s*$', np.nan, regex=True)
		dataframe = dataframe.dropna()
		
		Dframe = dataframe.to_dict(orient='records')

		return Dframe

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



def csr_updated_admin_form_data(csr_headings_data, source_data, copy_headings_data, parent_ids, pre_mapped_headings):

	try:

		data = {
			'csr_heading' : csr_headings_data,
			'source_file' : source_data,
			'copy_headings' : copy_headings_data,
			'parent_id' : parent_ids
		}

		dataframe = pd.DataFrame(data, columns=['csr_heading', 'source_file', 'copy_headings', 'parent_id'])
		dataframe = dataframe.drop(dataframe[(dataframe['parent_id'] != '0') & ((dataframe['source_file'] == '') | (dataframe['copy_headings'] == ''))].index)
		dataframe = dataframe.replace(r'^\s*$', np.nan, regex=True)
		dataframe = dataframe.dropna()

		CDframe = pd.DataFrame(pre_mapped_headings)

		Only_updated = pd.concat([dataframe, CDframe]).drop_duplicates(keep=False)

		Dframe = Only_updated.to_dict(orient='records')

		return Dframe
		
	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


def global_mapping_table_structure(mapping_table, req_client):

	try:

		dicT = {}

		for i in mapping_table:
			if i.parent_id == '0':
				ch_cont = GlobalMappingTable.objects.filter(csr_heading = i.csr_heading, parent_id=i.csr_heading, client=req_client).count()
				dicT[i.csr_heading] = ch_cont

		return dicT

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


def check_file_content(document):
	
	try:

		# calling procedure from admin_csr_mapping
		headings = get_all_headings(document)
		wrg__frmt = ''
		for i in headings:
			if re.match("^\d+(?:\.\d*)*(?![\w-])", i):
				wrg__frmt += i
				break

		return wrg__frmt

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



# def del_file_on_clear__config_admin(req_client):

# 	try:

# 		media_path = settings.MEDIA_ROOT

# 		admin_media_path = media_path + '\\admin'

# 		for root, dirs, files in os.walk(admin_media_path):
# 			for file in files:
				
# 				if os.path.exists(os.path.join(root, file)):
					
# 					try:
# 						os.remove(os.path.join(root, file))
# 					except:
# 						pass


# 	except Exception as e:
# 		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# To delete the admin files from filesystem on clear_config
def del_files__admin(template_list):

	try:
		media_path = settings.MEDIA_ROOT

		if template_list:
			for each in template_list:
				temp_path = media_path + '\\' + each
				try:
					os.remove(temp_path)
				except:
					pass
		else:
			pass

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


def del_file_on_clear__config_admin(req_client):

	try:
	
		csr_templates_list 	  = list(CSRTemplate.objects.filter(client=req_client).values_list('csr_template_location', flat=True))
		protocol_list 	  	  = list(ProtocolAdmin.objects.filter(client=req_client).values_list('protocol_template_location', flat=True))
		sar_list 		      = list(SARAdmin.objects.filter(client=req_client).values_list('sar_template_location', flat=True))
		

		del_files__admin(csr_templates_list)
		del_files__admin(protocol_list)
		del_files__admin(sar_list)
		
		
	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))