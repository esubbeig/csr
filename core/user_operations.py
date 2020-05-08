import pandas as pd
import numpy as np
import logging
import traceback
from datetime import datetime
import os
import re

from django.conf import settings
from django.contrib.auth.models import User
from .models import *


csr_logger 		  = logging.getLogger('csr')
csr_except_logger = logging.getLogger('csr_except')

def get_user_projects(usr):
	try:

		projects = ProjectsXUsers.objects.filter(user=usr, active=True)
		return projects

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

def csr_updated_user_form_data(csr_headings_data, source_data, copy_headings_data, parent_ids, custom_mapping):

	try:

		data = {
			'csr_heading' : csr_headings_data,
			'source_file' : source_data,
			'copy_headings' : copy_headings_data,
			'parent_id' : parent_ids,
		}

		dataframe = pd.DataFrame(data, columns=['csr_heading', 'source_file', 'copy_headings', 'parent_id'])
		dataframe = dataframe.drop(dataframe[(dataframe['parent_id'] != '0') & ((dataframe['source_file'] == '') | (dataframe['copy_headings'] == ''))].index)
		dataframe = dataframe.replace(r'^\s*$', np.nan, regex=True)
		dataframe = dataframe.dropna()

		CDframe = pd.DataFrame(custom_mapping)

		Only_updated = pd.concat([dataframe, CDframe]).drop_duplicates(keep=False)

		Dframe = Only_updated.to_dict(orient='records')
		
		return Dframe
		
	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



def get_global_mapping_suggestions(csr_headings, protocol_headings, sar_headings, projects):

	try:

		global_pre_mapped_headings = list(GlobalMappingTable.objects.filter(client=projects.client).values())

		filtered_global_pre_mapped_headings = []

		filtered_global_pre_mapped_headings_parent = []


		if protocol_headings != None and sar_headings != None:
			
			for i in csr_headings:
				for j in range(len(global_pre_mapped_headings)):
					if (re.sub("^\d+(?:\.\d*)*", '', i).strip() == re.sub("^\d+(?:\.\d*)*", '', global_pre_mapped_headings[j]['csr_heading']).strip() and global_pre_mapped_headings[j]['source_file'] != '' and global_pre_mapped_headings[j]['copy_headings'] != ''):
						filtered_global_pre_mapped_headings.append(global_pre_mapped_headings[j])

						if (re.sub("^\d+(?:\.\d*)*", '', i).strip() == re.sub("^\d+(?:\.\d*)*", '', global_pre_mapped_headings[j]['csr_heading']).strip() and global_pre_mapped_headings[j]['source_file'] != '' and global_pre_mapped_headings[j]['copy_headings'] != '' and global_pre_mapped_headings[j]['parent_id'] == '0'):
							filtered_global_pre_mapped_headings_parent.append(global_pre_mapped_headings[j])
		else:
			
			if protocol_headings != None:
				
				for i in csr_headings:
					for j in range(len(global_pre_mapped_headings)):
						if (re.sub("^\d+(?:\.\d*)*", '', i).strip() == re.sub("^\d+(?:\.\d*)*", '', global_pre_mapped_headings[j]['csr_heading']).strip() and global_pre_mapped_headings[j]['source_file'] == 'Protocol' and global_pre_mapped_headings[j]['copy_headings'] != ''):
							filtered_global_pre_mapped_headings.append(global_pre_mapped_headings[j])

							if (re.sub("^\d+(?:\.\d*)*", '', i).strip() == re.sub("^\d+(?:\.\d*)*", '', global_pre_mapped_headings[j]['csr_heading']).strip() and global_pre_mapped_headings[j]['source_file'] == 'Protocol' and global_pre_mapped_headings[j]['copy_headings'] != '' and global_pre_mapped_headings[j]['parent_id'] == '0'):
								filtered_global_pre_mapped_headings_parent.append(global_pre_mapped_headings[j])

			elif sar_headings != None:
				
				for i in csr_headings:
					for j in range(len(global_pre_mapped_headings)):
						if (re.sub("^\d+(?:\.\d*)*", '', i).strip() == re.sub("^\d+(?:\.\d*)*", '', global_pre_mapped_headings[j]['csr_heading']).strip() and global_pre_mapped_headings[j]['source_file'] == 'SAR' and global_pre_mapped_headings[j]['copy_headings'] != ''):
							filtered_global_pre_mapped_headings.append(global_pre_mapped_headings[j])

							if (re.sub("^\d+(?:\.\d*)*", '', i).strip() == re.sub("^\d+(?:\.\d*)*", '', global_pre_mapped_headings[j]['csr_heading']).strip() and global_pre_mapped_headings[j]['source_file'] == 'SAR' and global_pre_mapped_headings[j]['copy_headings'] != '' and global_pre_mapped_headings[j]['parent_id'] == '0'):
								filtered_global_pre_mapped_headings_parent.append(global_pre_mapped_headings[j])

		return filtered_global_pre_mapped_headings, filtered_global_pre_mapped_headings_parent

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

def del_files__(template_list):

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


def del_file_on_clear__config_usr(proj_id):

	try:
	
		csr_templates_list 	  = list(CSRTemplateUser.objects.filter(project=proj_id).values_list('csr_template_location', flat=True))
		protocol_list 	  	  = list(ProtocolFileUpload.objects.filter(project=proj_id).values_list('protocol_document_location', flat=True))
		sar_list 		      = list(SarFileUpload.objects.filter(project=proj_id).values_list('sar_document_location', flat=True))
		generated_report_list = list(Generated_Reports.objects.filter(project=proj_id).values_list('generated_report_path', flat=True))

		del_files__(csr_templates_list)
		del_files__(protocol_list)
		del_files__(sar_list)
		del_files__(generated_report_list)
		
	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))
