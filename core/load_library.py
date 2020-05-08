from .models import *
import pandas as pd
import numpy as np
import re
import logging
import traceback

csr_logger 		  = logging.getLogger('csr')
csr_except_logger = logging.getLogger('csr_except')

def load_library(data_frame):

	try:

		if not data_frame.empty:

			for index, row in data_frame.iterrows():
				
				db_obj = Library.objects.filter(standard_csr_heading=re.sub("^\d+(?:\.\d*)*", '', row['csr_heading']).strip()).first()

				if db_obj:

					if row['source_file'] == 'Protocol':

						lib_headings = db_obj.protocol_headings

						if lib_headings != '':

							temp_headings = lib_headings.lower().split(',')

							if re.sub("^\d+(?:\.\d*)*", '', row['copy_headings']).strip().lower() in temp_headings:

								pass

							else:

								lib_headings += re.sub("^\d+(?:\.\d*)*", '', row['copy_headings']).strip() + ','
						else:

							lib_headings = re.sub("^\d+(?:\.\d*)*", '', row['copy_headings']).strip() + ','

						db_obj.protocol_headings = lib_headings

						db_obj.save()

							

					elif row['source_file'] == 'SAR':

						lib_headings = db_obj.sar_headings

						if lib_headings != '':

							temp_headings = lib_headings.lower().split(',')

							if re.sub("^\d+(?:\.\d*)*", '', row['copy_headings']).strip().lower() in temp_headings:

								pass

							else:

								lib_headings += re.sub("^\d+(?:\.\d*)*", '', row['copy_headings']).strip() + ','
						else:

							lib_headings = re.sub("^\d+(?:\.\d*)*", '', row['copy_headings']).strip() + ','

						db_obj.sar_headings = lib_headings

						db_obj.save()


					else:
						pass

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


def load_library_with_admin_configurations(req_client):

	try:

		mapped_configurations = list(GlobalMappingTable.objects.filter(client=req_client).values('csr_heading', 'source_file', 'copy_headings'))

		data_frame = pd.DataFrame(mapped_configurations, columns=['csr_heading', 'source_file', 'copy_headings'])

		data_frame = data_frame.replace(r'^\s*$', np.nan, regex=True)

		data_frame = data_frame.dropna()

		load_library(data_frame)

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


def load_library_with_user_configurations(projects):

	try:
	
		mapped_configurations = list(CustomMappingTable.objects.filter(project=projects).values('csr_heading', 'source_file', 'copy_headings'))

		data_frame = pd.DataFrame(mapped_configurations, columns=['csr_heading', 'source_file', 'copy_headings'])

		data_frame = data_frame.replace(r'^\s*$', np.nan, regex=True)

		data_frame = data_frame.dropna()

		load_library(data_frame)

	except Exception as e:
		csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))
