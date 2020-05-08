from django.urls import path, include
from django.contrib import admin
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('add_user/', views.add_user, name='add_user'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),    
    path('change_password/', views.change_password, name='change_password'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
	path('activate_user/<usr_id>', views.activate_user, name='activate_user'),
	path('deactivate_user/<usr_id>', views.deactivate_user, name='deactivate_user'),
    path('set_password/', views.set_password, name='set_password'),
    path('reset_password/', views.reset_password, name='reset_password'),

    path('add_client/', views.add_client, name='add_client'),
	path('global_csr_upload/<cli_id>', views.global_csr_upload, name='global_csr_upload'),
    path('upload_csr_admin/<cli_id>', views.upload_csr_admin, name='upload_csr_admin'),
    path('upload_protocol_admin/<cli_id>', views.upload_protocol_admin, name='upload_protocol_admin'),
    path('upload_sar_admin/<cli_id>', views.upload_sar_admin, name='upload_sar_admin'),
    path('csr_mapping/<cli_id>', views.csr_mapping, name='csr_mapping'),
    path('confirm_csr_mapping_admin/<cli_id>', views.confirm_csr_mapping_admin, name='confirm_csr_mapping_admin'),
    path('display_global_csr_mapping/<cli_id>', views.display_global_csr_mapping, name='display_global_csr_mapping'),
    path('clear_configurations__admin/<cli_id>', views.clear_configurations__admin, name='clear_configurations__admin'),
	    
    path('get_all_users_details/', views.get_all_users_details, name='get_all_users_details'),
    path('get_all_active_users_details/', views.get_all_active_users_details, name='get_all_active_users_details'),
    path('get_all_act_inact_users_details/', views.get_all_act_inact_users_details, name='get_all_act_inact_users_details'),

    path('create_project/<usr_id>', views.create_project, name='create_project'),
    path('edit_user_project/<usr_id>/<proj_id>', views.edit_user_project, name='edit_user_project'),
    path('assign_project/<prj_id>', views.assign_project_new, name='assign_project'),
    path('project_dashboard/<usr_id>/<proj_id>', views.project_dashboard, name='project_dashboard'),

    path('csr_upload/<usr_id>/<pro_id>', views.csr_upload, name='csr_upload'),
    path('protocol_file_upload/<usr_id>/<pro_id>', views.protocol_file_upload, name='protocol_file_upload'),
    path('sar_file_upload/<usr_id>/<pro_id>', views.sar_file_upload, name='sar_file_upload'),
    path('edit_csr_mapping/<usr_id>/<proj_id>/', views.edit_csr_mapping, name='edit_csr_mapping'),
    path('confirm_csr_mapping_user/<usr_id>/<proj_id>', views.confirm_csr_mapping_user, name='confirm_csr_mapping_user'),
    path('generate_csr/<usr_id>/<proj_id>', views.generate_csr, name='generate_csr'),
    path('add_another_document__usr/<usr_id>/<proj_id>', views.add_another_document__usr, name='add_another_document__usr'),
    path('another_file_upload/<usr_id>/<pro_id>', views.another_file_upload, name='another_file_upload'),
    path('clear_configurations__usr/<usr_id>/<proj_id>', views.clear_configurations__usr, name='clear_configurations__usr'),

    path('download/<path>', views.download, name='download'),
    
    path('activity_log/<usr_id>', views.activity_log, name='activity_log'),
    path('audit_log/<usr_id>', views.audit_log, name='audit_log'),
    path('mail_logs/', views.mail_logs, name='mail_logs'),
    path('display_logging/', views.display_logging, name='display_logging'),
        
    path('email_configuration/', views.email_configuration, name='email_configuration'),
    path('resend_email/<mail_id>', views.resend_email, name='resend_email'),

]


