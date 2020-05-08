from .models import *
import pandas as pd
import numpy as np
import logging
import traceback

from .models import *

from django.forms.models import model_to_dict

csr_logger 		  = logging.getLogger('csr')
csr_except_logger = logging.getLogger('csr_except')

# audit log for user's edit project
def edit_project_log(previoust_state, current_state, project, user, client_ip):

	try:

		action = 'Edit Project'

		rm_keys = ['id', 'active', 'delete', 'created_by', 'generated']

		# conveting to dictionary from model instalce
		pre_dict_obj = model_to_dict(previoust_state)
		cur_dict_obj = model_to_dict(current_state)

		# replacing id with the name
		pre_dict_obj['therapeutic_area'] = previoust_state.therapeutic_area.therapeutic_area
		cur_dict_obj['therapeutic_area'] = current_state.therapeutic_area.therapeutic_area

		# popping keys which are not required
		[pre_dict_obj.pop(key) for key in rm_keys]
		[cur_dict_obj.pop(key) for key in rm_keys]

		audit_model = AuditLogsForMappingUser(

				user 		   = user,
				project 	   = project,
				action	  	   = action,
				previous_state = pre_dict_obj,
				current_state  = cur_dict_obj,
				ip 			   = client_ip
			)
		audit_model.save()

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

# audit log for admin assing projects
def assign_project_log(pre_assinged, post_assinged, user, client_ip):

	try:

		action = 'Assign Project'

		audit_model = AuditLogsForMappingAdmin(

				user 		   = user,
				action		   = action,
				previous_state = pre_assinged,
				current_state  = post_assinged,
				ip 			   = client_ip,
			)
		audit_model.save()

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))
	

# audit log for user's custom csr mapping
def edit_custom_csr_mapping_log(custom_mapping, csr_headings_data, source_data, copy_headings_data, reason, user, project, client_ip):

	try:

		action = 'Edit Mapping'
		
		new_custom_mapping = [{k: v for k, v in d.items() if k != 'id' and k != 'project_id' and k != 'created_by_id'} for d in custom_mapping]
			
		pre_mapped_dataframe = pd.DataFrame(new_custom_mapping, columns=['csr_heading', 'source_file', 'copy_headings'])

		pre_mapped_dataframe = pre_mapped_dataframe.replace(r'^\s*$', np.nan, regex=True)
		pre_mapped_dataframe = pre_mapped_dataframe.dropna()

		pre_mapped_dataframe_dict = pre_mapped_dataframe.to_dict(orient='records')
		
		data = {
			'csr_heading' : csr_headings_data,
			'source_file' : source_data,
			'copy_headings' : copy_headings_data
		}

		dataframe = pd.DataFrame(data, columns=['csr_heading', 'source_file', 'copy_headings'])
		dataframe = dataframe.replace(r'^\s*$', np.nan, regex=True)
		dataframe = dataframe.dropna()

		dataframe_dict = dataframe.to_dict(orient='records')

		audit_model = AuditLogsForMappingUser(

				user 		   = user,
				project 	   = project,
				action		   = action,
				previous_state = pre_mapped_dataframe_dict,
				current_state  = dataframe_dict,
				ip 			   = client_ip,
				reason 		   = reason
			)
		audit_model.save()

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

# audit log for admin's global csr mapping
def edit_global_csr_mapping_log(pre_mapped_headings, csr_headings_data, source_data, copy_headings_data, reason, user, client_ip):

	try:

		action = 'Edit Mapping'
		
		new_pre_mapped_headings = [{k: v for k, v in d.items() if k != 'id'} for d in pre_mapped_headings]

		pre_mapped_dataframe = pd.DataFrame(new_pre_mapped_headings, columns=['csr_heading', 'source_file', 'copy_headings'])

		pre_mapped_dataframe = pre_mapped_dataframe.replace(r'^\s*$', np.nan, regex=True)
		pre_mapped_dataframe = pre_mapped_dataframe.dropna()

		pre_mapped_dataframe_dict = pre_mapped_dataframe.to_dict(orient='records')

		data = {
			'csr_heading' : csr_headings_data,
			'source_file' : source_data,
			'copy_headings' : copy_headings_data
		}

		dataframe = pd.DataFrame(data, columns=['csr_heading', 'source_file', 'copy_headings'])
		dataframe = dataframe.replace(r'^\s*$', np.nan, regex=True)
		dataframe = dataframe.dropna()

		dataframe_dict = dataframe.to_dict(orient='records')

		audit_model = AuditLogsForMappingAdmin(

				user 		   = user,
				action		   = action,
				previous_state = pre_mapped_dataframe_dict,
				current_state  = dataframe_dict,
				ip 			   = client_ip,
				reason 	       = reason
			)
		audit_model.save()

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))