import json
import os
import logging
import math
import decimal
import traceback
from operator import itemgetter

from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseRedirect, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from django.urls import reverse
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage, get_connection, EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.views import View

from .admin_operations import *
from .user_operations import *
from .models import *
from .forms import *
from .token_generator import *
from .generate_csr import *
from .edit_csr_mapping import *
from .admin_csr_mapping import *
from .audit import *


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_NAME = BASE_DIR.split('\\')[-1]

csr_logger = logging.getLogger('csr')
csr_except_logger = logging.getLogger('csr_except')


def release_note(request):
    return render(request, 'releasenote.html')

def handler404(request, exception):
    return render(request,'404.html', status=404)

def handler500(request):
    return render(request,'500.html', status=500)

def handler400(request, exception):
    return render(request,'400.html', status=400)

def handler403(request, exception):
    return render(request,'403.html', status=403)

def home(request):

    try:

        if request.user.is_authenticated:

            latest_client = ClientInfo.objects.latest('id')
            
            if request.user.is_superuser:
                projects = ProjectInfo.objects.all()
                return render(request, 'admin_projects.html', {'projects' : projects, 'latest_client' : latest_client})
                
            else:
                proj = get_user_projects(request.user.id)
                return render(request, 'user_projects.html', {'user_projects' : proj, 'latest_client' : latest_client})
        
            return redirect('home')

        else:
            return redirect('login')

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


@login_required(login_url='/')
def add_user(request):

    try:

        if request.is_ajax():

            data = {}

            if request.method == 'POST':

                try:
                    form = SignUpForm(request.POST)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                if form.is_valid():
                    user = form.save(commit=False)
                    user.is_active = False
                    user.set_unusable_password()
                    user.save()

                    # Updating the extend user modal
                    username = form.cleaned_data.get('username')
                    mobile = request.POST['mobile']
                    temp = ExtendedUser(phone=mobile, user=user, created_by=request.user)
                    temp.save()
                    temp_count = UserProjectCount(user=user)
                    temp_count.save()

                    
                    #to send confirmation mail
                    try:
                        config  = EmailConfiguration.objects.last()
                    except EmailConfiguration.DoesNotExist:
                        config = None
                    
                    backend = EmailBackend(

                        host          = config.email_host,
                        # host          = '',
                        username      = config.email_host_user,
                        password      = config.email_host_password,
                        port          = config.email_port,
                        use_tls       = True,
                        fail_silently = True

                    )
                    from_email = config.email_default_mail
                    current_site = get_current_site(request)
                    email_subject = 'Activate Your Account with CSR'
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = account_activation_token.make_token(user)
                    activation_link = "http://{0}/set_password/?uid={1}".format(current_site, uid)
                    # message = "Dear {0},\n {1}" .format(user.username, activation_link)
                    to_email = form.cleaned_data.get('email')
                    html_content = "<h3>Dear <b>"+ user.username +"</b>,</h3><br>A new account was created with CSR. To make use of your account, first you need to set the password. Please follow the below link.<br><br>"+ activation_link + "<br><br><b>Thanks & Regards<br>CSR Automation</b>"
                    # html_content = "hello"
                    email = EmailMessage(subject=email_subject, body=html_content, from_email=from_email, to=[to_email], connection=backend)
                    email.content_subtype = 'html'
                    email_status = email.send()

                    # recording Email logs
                    e_log = LogsEmails(

                            event = 'Create User',
                            to_email = to_email,
                            from_email = from_email,
                            subject = email_subject,
                            message_body = html_content,
                            email_sent = email_status,
                            created_by = request.user

                        )
                    if email_status:
                        e_log.email_response = "Email sent scuccessfully"
                        data['mail_status'] = True
                        messages.success(request, "Confirmation mail send to the registered mail! Please activate")
                        # recording logging
                        csr_logger.info(username + " is successfully created by " + request.user.username + " & email sent.")

                    else:
                        e_log.email_response = "Not able to connect SMTP server"
                        data['mail_status'] = False
                        messages.error(request, "Problem with connecting SMTP server. Please check the Email Configurations!")
                        # recording logging
                        csr_except_logger.critical("Not able to connect SMTP server while creating " + username)

                    e_log.save()

                    #recording activity log
                    event = 'Add User'
                    record_user_activity_log(
                        event       = event,
                        actor       = request.user, 
                        dif_user    = username, 
                        session_id  = request.session.session_key
                        )

                    data['form_is_valid'] = True

                else:
                    data['form_is_valid'] = False

            else:
                form = SignUpForm()

            context = {
                'form' : form
            }
            data['html_form'] = render_to_string('registration/signup.html', context, request=request)
            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

# to set the password first time when user is created
def set_password(request):

    try:

        uidb64 = request.GET.get('uid')
        uid = force_bytes(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if user is not None:

            if user.has_usable_password():

                return HttpResponse('Sorry, You have already set your password. Please contact Admin!')
            
            else:

                status = 0
                user.is_active = True
                user.save()
                login(request, user)
        
                if request.method == 'POST':

                    try:
                        form = SetPasswordForm(request.user, request.POST)
                    except Exception as e:
                        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                    if form.is_valid():
                        user = form.save()
                        update_session_auth_hash(request, user)
                        logout(request)
                        return render(request, 'registration/set_password_success.html')
                        status = 1

                    else:
                        pass

                else:
                    form = SetPasswordForm(request.user)

                if status == 0:
                    user.is_active = False
                    user.save()

                return render(request, 'registration/activate_set_password.html', {'form' : form})

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



# to reset the password if user forgets the password
def reset_password(request):

    try:

        uidb64 = request.GET.get('uid')
        uid = force_bytes(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if user is not None:

            if user.is_active:

                login(request, user)
                
                if request.method == 'POST':

                    try:
                        form = SetPasswordForm(request.user, request.POST)
                    except Exception as e:
                        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                    if form.is_valid():
                        user = form.save()
                        update_session_auth_hash(request, user)
                        logout(request)
                        return render(request, 'registration/reset_password_success.html')

                    else:
                        # messages.error(request, 'Passwords mismatched!')
                        pass

                else:
                    form = SetPasswordForm(request.user)

                return render(request, 'registration/reset_password.html', {'form' : form})

            else:
                return HttpResponse('Sorry, Your account has been disabled, please contact Admin!')

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle forgot password
def forgot_password(request):

    try:

        if request.method == 'POST':

            to_email = request.POST['email']

            try:
                user = User.objects.get(email=to_email)
            except User.DoesNotExist:
                user = None


            if user is not None:

                if user.is_active:

                    #to send forgot password mail
                    config  = EmailConfiguration.objects.last()
                    backend = EmailBackend(

                        host          = config.email_host,
                        username      = config.email_host_user,
                        password      = config.email_host_password,
                        port          = config.email_port,
                        use_tls       = True,
                        fail_silently = True
                    )
                    from_email            = config.email_default_mail
                    current_site          = get_current_site(request)
                    email_subject         = 'Reset your Account Password with CSR'
                    uid                   = urlsafe_base64_encode(force_bytes(user.pk))
                    password_reset_link   = "http://{0}/reset_password/?uid={1}".format(current_site, uid)
                    html_content          = "<h3>Dear <b>"+ user.username +"</b>,</h3><br>We got a request to reset your password with CSR. Please follow the below link.<br><br>"+ password_reset_link + "<br><br><b>Thanks & Regards<br>CSR Automation</b>"
                    email                 = EmailMessage(subject=email_subject, body=html_content, from_email=from_email, to=[to_email], connection=backend)
                    email.content_subtype = 'html'
                    email_status          = email.send()

                    # recording Email logs
                    e_log = LogsEmails(

                            event        = 'Forgot Password',
                            to_email     = to_email,
                            from_email   = from_email,
                            subject      = email_subject,
                            message_body = html_content,
                            email_sent   = email_status,
                            created_by   = User.objects.get(email=to_email)
                        )
                    if email_status:
                        e_log.email_response = "Email sent scuccessfully"

                    else:
                        e_log.email_response = "Not able to connect SMTP server"                    

                    e_log.save()

                    if email_status:
                        messages.success(request, 'A password reset link has been sent to your email')
                    else:
                        messages.error(request, 'Failed! to send reset password link. Please try after some time.')

                else:
                    messages.error(request, 'Sorry, Your account has been disabled. Please contact Admin!')

            else:
                messages.error(request, 'No user found with given email')
                

        return render(request, 'registration/forgot_password.html')

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle login request
def login_request(request):

    try:

        if request.user.is_authenticated:

            return redirect('/')
        
        if request.method == 'POST':

            try:
                form = AuthenticationForm(request, request.POST)
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        messages.success(request, "You are logged in as " + username)
                        return redirect('home')
                        
                    else:
                        messages.error(request, "Your account is disabled!")
                else:
                    messages.error(request, 'Invalid username or password')
            else:
                messages.error(request, 'Invalid username or password')
        else:
            form = AuthenticationForm()

        return render(request, 'registration/login.html', {'form' : form})

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle login request
@login_required(login_url='/')
def logout_request(request):

    try:

        logout(request)
        return redirect('home')

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle change password request
@login_required(login_url='/')
def change_password(request):

    try:

        if request.is_ajax():

            data = {}

            if request.method == 'POST':

                try:
                    form = PasswordChangeForm(request.user, request.POST)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                if form.is_valid():

                    updated_pass = request.POST.get('new_password1')

                    req_user = User.objects.get(pk=request.user.id)

                    if not req_user.check_password(updated_pass):

                        user = form.save()

                        update_session_auth_hash(request, user)

                        messages.success(request, "Password changed successfully")

                        data['form_is_valid'] = True

                    else:

                        data['form_is_valid'] = False
                        data['old_pass'] = True

                else:
                    data['form_is_valid'] = False
            else:
                form = PasswordChangeForm(request.user)
                
            context = {
                'form' : form
            }
            data['html_form'] = render_to_string('registration/change_password.html', context, request=request)
            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))




#to activate the users
@login_required(login_url='/')
def activate_user(request, usr_id):

    try:

        if request.user.is_superuser:

            usr = User.objects.get(pk=usr_id)

            if usr.has_usable_password():

                usr.is_active = True
                usr.save()
                messages.success(request, usr.username + ' has been activated successfully!')

                #recording user acivity log
                event = 'Activate User'
                record_user_activity_log(
                    event       = event, 
                    actor       = request.user, 
                    dif_user    = usr.username, 
                    session_id  = request.session.session_key
                    )

            else:
                messages.error(request, 'Sorry! '+ usr.username +' not set the password yet!')

            return redirect('get_all_users_details')

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


#to deactivate the users
@login_required(login_url='/')
def deactivate_user(request, usr_id):

    try:

        if request.user.is_superuser:

            usr = User.objects.get(pk=usr_id)
            usr.is_active = False
            usr.save()
            messages.success(request, usr.username + ' has been deactivated successfully!')

            #recording user acivity log
            event = 'Deactivate User'
            record_user_activity_log(
                event       = event, 
                actor       = request.user, 
                dif_user    = usr.username, 
                session_id  = request.session.session_key
                )

            return redirect('get_all_users_details')

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle admin csr template upload
@login_required(login_url='/')
def upload_csr_admin(request, cli_id):

    try:

        if request.is_ajax() and request.user.is_superuser:

            data = {}

            therapeutic_area_list = TherapeuticArea.objects.all()

            req_client = ClientInfo.objects.get(pk=cli_id)

            if request.method == 'POST':

                version          = request.POST['version']
                file_Name        = request.FILES['csr_template_location']

                try:
                    form = GlobalCsrUploadForm(request.POST, request.FILES)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))            

                if form.is_valid():
                    
                    fr__mt = check_file_content(file_Name)

                    if fr__mt == '':

                        dd = form.save(commit=False)
                        dd.created_by = request.user
                        dd.client = req_client

                        try:
                            obj = CSRTemplate.objects.filter(client=req_client).latest('id').version_no
                        except CSRTemplate.DoesNotExist:
                            obj = None

                        if obj is not None:

                            if version == '0.1':
                                ver, rev = obj.split('.')
                                obj = ver + '.' + str(int(rev) + 1)

                                # obj = obj + decimal.Decimal(float(version))
                            else:
                                ver, rev = obj.split('.')
                                obj = str(int(ver)+1) + '.' + str(0)
                                # obj = obj + decimal.Decimal(float(version))
                                # obj = decimal.Decimal(float(math.floor(obj)))

                        else:
                            obj = version
                            # obj = decimal.Decimal(float(version))

                        dd.version_no = obj
                        dd.save()
                        # Deleting premapped data in GlobalMappingTable
                        try:
                            GlobalMappingTable.objects.filter(client=req_client).delete()
                        except Exception as e:
                            csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


                        messages.success(request, "Global CSR has been uploaded successfully!")

                        #recording user acivity log
                        event = 'CSR Upload'
                        record_user_activity_log(
                            event       = event, 
                            actor       = request.user,
                            client      = req_client.client_name,
                            session_id  = request.session.session_key
                            )

                        data['form_is_valid'] = True
                        data['file_data_format'] = ''

                    else:
                        data['form_is_valid'] = False
                        data['file_data_format'] = fr__mt

                else:
                    data['form_is_valid'] = False
                    data['file_data_format'] = ''
            else:
                form = GlobalCsrUploadForm()

            context = {

                'form' : form,
                'therapeutic_area_list' : therapeutic_area_list,
                'req_client' : req_client,
            }

            data['html_form'] = render_to_string('upload_global_csr_admin.html', context, request=request)
            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle admin protocol upload
@login_required(login_url='/')
def upload_protocol_admin(request, cli_id):

    try:

        if request.is_ajax() and request.user.is_superuser:

            data = {}

            therapeutic_area_list = TherapeuticArea.objects.all()

            req_client = ClientInfo.objects.get(pk=cli_id)

            if request.method == 'POST':

                version          = request.POST['version']
                file_Name        = request.FILES['protocol_template_location']

                try:
                    form = ProtocolUploadAdminForm(request.POST, request.FILES)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                if form.is_valid():

                    fr__mt = check_file_content(file_Name)
                    
                    if fr__mt == '':

                        dd = form.save(commit=False)
                        dd.created_by = request.user
                        dd.client = req_client

                        try:
                            obj = ProtocolAdmin.objects.filter(client=req_client).latest('id').version_no
                        except ProtocolAdmin.DoesNotExist:
                            obj = None

                        if obj is not None:

                            if version == '0.1':
                                ver, rev = obj.split('.')
                                obj = ver + '.' + str(int(rev) + 1)

                                # obj = obj + decimal.Decimal(float(version))
                            else:
                                ver, rev = obj.split('.')
                                obj = str(int(ver)+1) + '.' + str(0)
                                # obj = obj + decimal.Decimal(float(version))
                                # obj = decimal.Decimal(float(math.floor(obj)))

                        else:
                            obj = version
                            # obj = decimal.Decimal(float(version))

                        dd.version_no = obj
                        dd.save()
                        messages.success(request, "Protocol has been uploaded successfully!")

                        event = 'Upload Protocol'
                        record_user_activity_log(
                            event       = event, 
                            actor       = request.user,
                            client      = req_client.client_name,
                            session_id  = request.session.session_key
                            )

                        data['form_is_valid'] = True
                        data['file_data_format'] = ''

                    else:
                        data['form_is_valid'] = False
                        data['file_data_format'] = fr__mt

                else:
                    data['form_is_valid'] = False
                    data['file_data_format'] = ''
            else:
                form = ProtocolUploadAdminForm()

            context = {

                'form' : form,
                'therapeutic_area_list' : therapeutic_area_list,
                'req_client' : req_client,
            }

            data['html_form'] = render_to_string('upload_protocol_admin.html', context, request=request)
            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle admin sar upload
@login_required(login_url='/')
def upload_sar_admin(request, cli_id):

    try:

        if request.is_ajax() and request.user.is_superuser:

            data = {}

            therapeutic_area_list = TherapeuticArea.objects.all()

            req_client = ClientInfo.objects.get(pk=cli_id)

            if request.method == 'POST':

                version          = request.POST['version']

                try:
                    form = SARUploadAdminForm(request.POST, request.FILES)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                if form.is_valid():
                    
                    dd = form.save(commit=False)
                    dd.created_by = request.user
                    dd.client = req_client

                    try:
                        obj = SARAdmin.objects.filter(client=req_client).latest('id').version_no
                    except SARAdmin.DoesNotExist:
                        obj = None

                    if obj is not None:

                        if version == '0.1':
                            ver, rev = obj.split('.')
                            obj = ver + '.' + str(int(rev) + 1)

                            # obj = obj + decimal.Decimal(float(version))
                        else:
                            ver, rev = obj.split('.')
                            obj = str(int(ver)+1) + '.' + str(0)
                            # obj = obj + decimal.Decimal(float(version))
                            # obj = decimal.Decimal(float(math.floor(obj)))

                    else:
                        obj = version
                        # obj = decimal.Decimal(float(version))

                    dd.version_no = obj
                    dd.save()
                    messages.success(request, "SAR has been uploaded successfully!")

                    # recording activity log
                    event = 'Upload SAR'
                    record_user_activity_log(
                        event       = event, 
                        actor       = request.user,
                        client      = req_client.client_name,
                        session_id  = request.session.session_key
                        )

                    data['form_is_valid'] = True
                else:
                    data['form_is_valid'] = False
            else:
                form = SARUploadAdminForm()

            context = {

                'form' : form,
                'therapeutic_area_list' : therapeutic_area_list,
                'req_client' : req_client,
            }

            data['html_form'] = render_to_string('upload_sar_admin.html', context, request=request)
            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# this handle globaL csr upload functionality
@login_required(login_url='/')
def global_csr_upload(request, cli_id):

    try:

        if request.user.is_superuser:

            therapeutic_area_list = TherapeuticArea.objects.all()
            client_list = ClientInfo.objects.all()
            latest_client = ClientInfo.objects.latest('id')

            req_client = ClientInfo.objects.get(pk=cli_id)

            try:
                csr_doc_latest = CSRTemplate.objects.filter(client=req_client).latest('id')
            except CSRTemplate.DoesNotExist:
                csr_doc_latest = None
            try:
                csr_doc_list = CSRTemplate.objects.filter(client=req_client).order_by('-created_on')[1:]
            except CSRTemplate.DoesNotExist:
                csr_doc_list = None

            try:
                protocol_doc_latest = ProtocolAdmin.objects.filter(client=req_client).latest('id')
            except ProtocolAdmin.DoesNotExist:
                protocol_doc_latest = None
            try:
                protocol_doc_list = ProtocolAdmin.objects.filter(client=req_client).order_by('-created_on')[1:]
            except ProtocolAdmin.DoesNotExist:
                protocol_doc_list = None

            try:
                sar_doc_latest = SARAdmin.objects.filter(client=req_client).latest('id')
            except SARAdmin.DoesNotExist:
                sar_doc_latest = None
            try:
                sar_doc_list = SARAdmin.objects.filter(client=req_client).order_by('-created_on')[1:]
            except SARAdmin.DoesNotExist:
                sar_doc_list = None
                
            context = {
                'csr_doc_latest'      : csr_doc_latest,
                'csr_doc_list'        : csr_doc_list,
                'protocol_doc_latest' : protocol_doc_latest,
                'protocol_doc_list'   : protocol_doc_list,
                'sar_doc_latest'      : sar_doc_latest,
                'sar_doc_list'        : sar_doc_list,
                'client_list'         : client_list,
                'latest_client'       : latest_client,
                'req_client'          : req_client,
            }
            return render(request, 'global_csr_upload.html', context)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


#this handle the csr upload operation in each project of user
@login_required(login_url='/')
def csr_upload(request, usr_id, pro_id):

    try:

        proj = ProjectInfo.objects.get(pk=pro_id)

        is_belongs = ProjectsXUsers.objects.get(project=proj, user=request.user)

        if request.user.id == int(usr_id) and request.is_ajax() and is_belongs.is_active:

            data = {}

            therapeutic_area_list = TherapeuticArea.objects.all()

            if request.method == 'POST':

                version          = request.POST['version']
                file_Name        = request.FILES['csr_template_location']

                try:
                    form = CsrUploadForm(request.POST, request.FILES)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))
                
                if form.is_valid():

                    fr__mt = check_file_content(file_Name)

                    if fr__mt == '':

                        dd = form.save(commit=False)
                        dd.project = proj
                        dd.created_by = request.user

                        try:
                            obj = CSRTemplateUser.objects.filter(project=pro_id).latest('id').version_no
                        except CSRTemplateUser.DoesNotExist:
                            obj = None

                        if obj is not None:

                            if version == '0.1':
                                ver, rev = obj.split('.')
                                obj = ver + '.' + str(int(rev) + 1)

                                # obj = obj + decimal.Decimal(float(version))
                            else:
                                ver, rev = obj.split('.')
                                obj = str(int(ver)+1) + '.' + str(0)
                                # obj = obj + decimal.Decimal(float(version))
                                # obj = decimal.Decimal(float(math.floor(obj)))

                        else:
                            obj = version
                            # obj = decimal.Decimal(float(version))

                        dd.version_no = obj
                        dd.save()

                        # Deleting premapped data in GlobalMappingTable
                        try:
                            CustomMappingTable.objects.filter(project=pro_id).delete()
                        except Exception as e:
                            csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                        # Logging activity log
                        event = 'Custom CSR Upload'
                        record_user_activity_log(
                            event       = event, 
                            actor       = request.user,
                            proj_name   = proj.project_name, 
                            session_id  = request.session.session_key
                            )

                        messages.success(request, "Custom CSR has been uploaded successfully!")
                        data['form_is_valid'] = True
                        data['file_data_format'] = ''

                    else:
                        data['form_is_valid'] = False
                        data['file_data_format'] = fr__mt


                else:
                    data['form_is_valid'] = False
                    data['file_data_format'] = ''

            else:
                form = CsrUploadForm()

            context = {

                'form' : form,
                'therapeutic_area_list' : therapeutic_area_list,
                'proj' : proj
            }
            data['html_form'] = render_to_string('csr_upload.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


#this handle the protocol upload operation in each project of user
@login_required(login_url='/')
def protocol_file_upload(request, usr_id, pro_id):

    try:

        proj = ProjectInfo.objects.get(pk=pro_id)

        is_belongs = ProjectsXUsers.objects.get(project=proj, user=request.user)

        if request.user.id == int(usr_id) and request.is_ajax() and is_belongs.is_active:

            data = {}

            therapeutic_area_list = TherapeuticArea.objects.all()

            if request.method == 'POST':

                version          = request.POST['version']
                file_Name        = request.FILES['protocol_document_location']

                try:
                    form = ProtocolFileUploadForm(request.POST, request.FILES)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))
                
                if form.is_valid():

                    fr__mt = check_file_content(file_Name)

                    if fr__mt == '':

                        dd = form.save(commit=False)
                        dd.project = proj
                        dd.created_by = request.user

                        try:
                            obj = ProtocolFileUpload.objects.filter(project=pro_id).latest('id').version_no
                        except ProtocolFileUpload.DoesNotExist:
                            obj = None

                        if obj is not None:

                            if version == '0.1':
                                ver, rev = obj.split('.')
                                obj = ver + '.' + str(int(rev) + 1)

                                # obj = obj + decimal.Decimal(float(version))
                            else:
                                ver, rev = obj.split('.')
                                obj = str(int(ver)+1) + '.' + str(0)
                                # obj = obj + decimal.Decimal(float(version))
                                # obj = decimal.Decimal(float(math.floor(obj)))

                        else:
                            obj = version
                            # obj = decimal.Decimal(float(version))

                        dd.version_no = obj
                        dd.save()
                        # Logging activity log
                        event = 'Protocol Upload'
                        record_user_activity_log(
                            event       = event, 
                            actor       = request.user,
                            proj_name   = proj.project_name, 
                            session_id  = request.session.session_key
                            )

                        messages.success(request, "Protocol has been uploaded successfully!")
                        data['form_is_valid'] = True
                        data['file_data_format'] = ''

                    else:
                        data['form_is_valid'] = False
                        data['file_data_format'] = fr__mt
                else:
                    data['form_is_valid'] = False
                    data['file_data_format'] = ''
            else:
                form = ProtocolFileUploadForm()

            context = {

                'form' : form,
                'therapeutic_area_list' : therapeutic_area_list,
                'proj' : proj
            }
            data['html_form'] = render_to_string('protocol_upload.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


#this handle the sar upload operation in each project of user
@login_required(login_url='/')
def sar_file_upload(request, usr_id, pro_id):

    try:

        proj = ProjectInfo.objects.get(pk=pro_id)

        is_belongs = ProjectsXUsers.objects.get(project=proj, user=request.user)

        if request.user.id == int(usr_id) and request.is_ajax() and is_belongs.is_active:

            data = {}

            therapeutic_area_list = TherapeuticArea.objects.all()

            if request.method == 'POST':

                version  = request.POST['version']

                try:
                    form = SarFileUploadForm(request.POST, request.FILES)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                if form.is_valid():
                    dd = form.save(commit=False)
                    dd.project = proj
                    dd.created_by = request.user

                    try:
                        obj = SarFileUpload.objects.filter(project=pro_id).latest('id').version_no
                    except SarFileUpload.DoesNotExist:
                        obj = None

                    if obj is not None:

                        if version == '0.1':
                            ver, rev = obj.split('.')
                            obj = ver + '.' + str(int(rev) + 1)

                            # obj = obj + decimal.Decimal(float(version))
                        else:
                            ver, rev = obj.split('.')
                            obj = str(int(ver)+1) + '.' + str(0)
                            # obj = obj + decimal.Decimal(float(version))
                            # obj = decimal.Decimal(float(math.floor(obj)))

                    else:
                        obj = version
                        # obj = decimal.Decimal(float(version))

                    dd.version_no = obj
                    dd.save()
                    # logging activity log
                    event = 'SAR Upload'
                    record_user_activity_log(
                        event       = event, 
                        actor       = request.user,
                        proj_name   = proj.project_name, 
                        session_id  = request.session.session_key
                        )

                    messages.success(request, "SAR has been uploaded successfully!")
                    data['form_is_valid'] = True

                else:
                    data['form_is_valid'] = False

            else:
                form = SarFileUploadForm()

            context = {

                'form' : form,
                'therapeutic_area_list' : therapeutic_area_list,
                'proj' : proj
            }
            data['html_form'] = render_to_string('sar_upload.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


#this handle the another document upload operation in each project of user
@login_required(login_url='/')
def another_file_upload(request, usr_id, pro_id):

    try:

        proj = ProjectInfo.objects.get(pk=pro_id)

        is_belongs = ProjectsXUsers.objects.get(project=proj, user=request.user)

        if request.user.id == int(usr_id) and request.is_ajax() and is_belongs.is_active:

            data = {}

            therapeutic_area_list = TherapeuticArea.objects.all()

            is_another_doc_available = AnotherFileUploadUserInfo.objects.get(project=pro_id)

            if request.method == 'POST':

                version  = request.POST['version']
                file_Name = request.FILES['another_document_location']

                try:
                    form = AnotherFileUploadUserForm(request.POST, request.FILES)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                if form.is_valid():

                    fr__mt = check_file_content(file_Name)

                    if fr__mt == '':

                        dd = form.save(commit=False)
                        dd.project = proj
                        dd.created_by = request.user

                        try:
                            obj = AnotherFileUploadUser.objects.filter(project=pro_id).latest('id').version_no
                        except AnotherFileUploadUser.DoesNotExist:
                            obj = None

                        if obj is not None:

                            if version == '0.1':
                                ver, rev = obj.split('.')
                                obj = ver + '.' + str(int(rev) + 1)

                                # obj = obj + decimal.Decimal(float(version))
                            else:
                                ver, rev = obj.split('.')
                                obj = str(int(ver)+1) + '.' + str(0)
                                # obj = obj + decimal.Decimal(float(version))
                                # obj = decimal.Decimal(float(math.floor(obj)))

                        else:
                            obj = version
                            # obj = decimal.Decimal(float(version))

                        dd.version_no = obj
                        dd.save()
                        # logging activity log
                        event = 'Another Doc Upload'
                        record_user_activity_log(
                            event       = event, 
                            actor       = request.user,
                            proj_name   = proj.project_name,
                            source_name = is_another_doc_available.source_name,
                            session_id  = request.session.session_key
                            )

                        messages.success(request, is_another_doc_available.source_name + " has been uploaded successfully!")
                        data['form_is_valid'] = True
                        data['file_data_format'] = ''

                    else:
                        data['form_is_valid'] = False
                        data['file_data_format'] = fr__mt

                else:
                    data['form_is_valid'] = False
                    data['file_data_format'] = ''
            else:
                form = AnotherFileUploadUserForm()

            context = {

                'form' : form,
                'therapeutic_area_list' : therapeutic_area_list,
                'proj' : proj,
                'is_another_doc_available' : is_another_doc_available
            }
            data['html_form'] = render_to_string('another_upload_user.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


@login_required(login_url='/')
def create_project(request, usr_id):

    try:

        if request.user.id == int(usr_id) and request.is_ajax():
    
            therapeutic_area_list = TherapeuticArea.objects.all()
            client_list = ClientInfo.objects.all()

            data = {}

            if request.method == 'POST':

                try:
                    form = CreateProjectForm(request.POST or None)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                if form.is_valid():
                    dd = form.save(commit=False)
                    dd.created_by   = request.user
                    dd.save()
                    #updating projectsXusers
                    projectxusers = ProjectsXUsers(project=dd, user=request.user, created_by=request.user)
                    projectxusers.save()
                    #updating userprojectcount
                    try:
                        y = ProjectsXUsers.objects.filter(user=usr_id, active=True).count()
                        proj_count = UserProjectCount.objects.get(user=usr_id)
                        proj_count.project_count = y
                        proj_count.save()
                    except:
                        pass
                    
                    messages.success(request, "Project has been created successfully!")
                    data['form_is_valid'] = True

                    #recording activity log
                    event = 'Create Project'
                    record_user_activity_log(
                        event       = event, 
                        actor       = request.user, 
                        proj_name   = dd.project_name, 
                        session_id  = request.session.session_key
                        )

                else:
                    data['form_is_valid'] = False
            else:
                form = CreateProjectForm()

            context = {

                'form' : form,
                'therapeutic_area_list' : therapeutic_area_list,
                'client_list' : client_list
            }
            data['html_form'] = render_to_string('create_project.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

    

# to hanlde assign projects in admin
@login_required(login_url='/')
def assign_project_new(request, prj_id):

    try:

        if request.user.is_superuser and request.is_ajax():

            pre = []
            post = []

            post_assigned_user_emails = []

            project = ProjectInfo.objects.get(pk=prj_id)

            # recording pre assinged users
            pre_assigned_user_names_active = ProjectsXUsers.objects.filter(project=prj_id, active=True)
            for i in pre_assigned_user_names_active:
                pre.append(i.user.username)

            #to get all the records
            pre_assigned_all = ProjectsXUsers.objects.filter(project=prj_id)
            pre_assigned_user_ids_all = []
            for m in pre_assigned_all:
                pre_assigned_user_ids_all.append(m.user.id)

            #to get all active records which passed into the form
            pre_assigned_active = ProjectsXUsers.objects.filter(project=prj_id, active=True)
            pre_assigned_user_ids_active = []   

            for n in pre_assigned_active:
                pre_assigned_user_ids_active.append(n.user.id)
            
            pre_assigned_user_ids_all = set(pre_assigned_user_ids_all)
            pre_assigned_user_ids_active = set(pre_assigned_user_ids_active)

            data = {}
            
            users = get_all_users_active()

            if request.method == 'POST':
                some_values = request.POST.getlist('check_user')
                if len(some_values) > 0:
                    
                    for i in range(len(some_values)):
                        try:
                            temp = ProjectsXUsers.objects.get(project=prj_id, user=int(some_values[i]))
                            if temp:
                                if temp.is_active:
                                    pass
                                else:
                                    temp.active = True
                                    temp.save()
                        except ProjectsXUsers.DoesNotExist:
                            temp = ProjectsXUsers(created_by = User.objects.get(pk=1), project=ProjectInfo.objects.get(pk=prj_id), user=User.objects.get(pk=int(some_values[i])))
                            temp.save()

                    #this makes the record deactive if user is unchecked
                    new_values = set(int(l) for l in some_values)
                    for j in pre_assigned_user_ids_all:
                        if j in new_values:
                            pass
                        else:
                            try:
                                temp = ProjectsXUsers.objects.get(project=prj_id, user=User.objects.get(pk=j))
                                temp.active = False
                                temp.save()
                            except:
                                pass

                    #updating project count table
                    for k in users:
                        try:
                            upc = UserProjectCount.objects.get(user=k.id)
                            upc.project_count = ProjectsXUsers.objects.filter(user=k.id, active=True).count()
                            upc.save()
                        except UserProjectCount.DoesNotExist:
                            pass

                    # recording post assinged users
                    post_assigned_user_names_active = ProjectsXUsers.objects.filter(project=prj_id, active=True)
                    for i in post_assigned_user_names_active:
                        post.append(i.user.username)
                        post_assigned_user_emails.append(i.user.email)

                    # recording audit log
                    client_ip = request.META['REMOTE_ADDR']
                    assign_project_log(pre, post, request.user, client_ip)

                    #recording activity log
                    event = 'Assign Project'
                    record_user_activity_log(
                        event       = event, 
                        actor       = request.user, 
                        proj_name   = project.project_name, 
                        session_id  = request.session.session_key
                        )

                    #to send alert email
                    try:
                        config  = EmailConfiguration.objects.last()
                    except EmailConfiguration.DoesNotExist:
                        config = None
                    
                    backend = EmailBackend(

                        host          = config.email_host,
                        username      = config.email_host_user,
                        password      = config.email_host_password,
                        port          = config.email_port,
                        use_tls       = True,
                        fail_silently = True

                    )
                    from_email = config.email_default_mail
                    current_site = get_current_site(request)
                    email_subject = 'Project Assignment in CSR.'
                    
                    for i in range(len(post)):
                        if post_assigned_user_emails[i] != '':

                            to_email = post_assigned_user_emails[i]
                            html_content = "<h3>Dear <b>"+ post[i] +"</b>,</h3><br>You have been assigned with a new project, <b>" + project.project_name + "</b><br><br><b>Thanks & Regards<br>CSR Automation</b>"

                            email = EmailMessage(subject=email_subject, body=html_content, from_email=from_email, to=[to_email], connection=backend)
                            email.content_subtype = 'html'
                            email_status = email.send()
                    
                            # recording Email logs
                            e_log = LogsEmails(

                                    event = 'Assign Project',
                                    to_email = to_email,
                                    from_email = from_email,
                                    subject = email_subject,
                                    message_body = html_content,
                                    email_sent = email_status,
                                    created_by = request.user

                                )
                            e_log.save()         

                    messages.success(request, "Project has been Assigned successfully!")
                    data['form_is_valid'] = True
                else:
                    data['form_is_valid'] = False

            context = {

                'users' : users,
                'project' : project,
                'pre_assigned_user_ids_active' : pre_assigned_user_ids_active

            }

            data['html_form'] =  render_to_string('assign_project.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



#this fetches all the users project details
@login_required(login_url='/')
def get_all_users_details(request):

    try:
        if request.user.is_superuser:

            try:
                config = EmailConfiguration.objects.last()
            except EmailConfiguration.DoesNotExist:
                config = None
            
            proj_count = UserProjectCount.objects.all()
            users = get_all_users_active()
            latest_client = ClientInfo.objects.latest('id')
            return render(request, 'admin_users.html', {'users' : users,  'proj_count' : proj_count, 'config' : config, 'latest_client' : latest_client})

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


#this fetches all the users project details
@login_required(login_url='/')
def get_all_active_users_details(request):

    try:

        if request.user.is_superuser and request.is_ajax():

            data = {}

            try:
                config = EmailConfiguration.objects.last()
            except EmailConfiguration.DoesNotExist:
                config = None
            
            proj_count = UserProjectCount.objects.all()
            users = get_all_users_active()
            context ={
                'users'      : users,
                'proj_count' : proj_count,
                'config'     : config
            }
            data['html_form'] =  render_to_string('admin_users_partial.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


#this fetches all the users project details
@login_required(login_url='/')
def get_all_act_inact_users_details(request):

    try:

        if request.user.is_superuser and request.is_ajax():

            data = {}

            try:
                config = EmailConfiguration.objects.last()
            except EmailConfiguration.DoesNotExist:
                config = None
            
            proj_count = UserProjectCount.objects.all()
            users = get_all_users()
            context ={
                'users'      : users,
                'proj_count' : proj_count,
                'config'     : config
            }
            data['html_form'] =  render_to_string('admin_users_partial.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle project editing
@login_required(login_url='/')
def edit_user_project(request, usr_id, proj_id):

    try:

        projects = ProjectInfo.objects.get(pk=proj_id)

        is_belongs = ProjectsXUsers.objects.get(project=projects, user=request.user)

        if request.user.id == int(usr_id) and request.is_ajax() and is_belongs.is_active:

            therapeutic_area_list = TherapeuticArea.objects.all()
            client_list           = ClientInfo.objects.all()

            data = {}

            if request.method == 'POST':

                try:
                    form = EditProjectForm(request.POST or None, instance=projects)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                if form.is_valid():

                    # recording previous state
                    previoust_state = ProjectInfo.objects.get(pk=proj_id)

                    # updating project details
                    projects.project_name     = request.POST.get('project_name')
                    projects.protocol_id      = request.POST.get('protocol_id')
                    projects.client           = ClientInfo.objects.get(pk=request.POST.get('client'))
                    projects.therapeutic_area = TherapeuticArea.objects.get(pk=request.POST.get('therapeutic_area'))
                    projects.phase            = request.POST.get('phase')
                    projects.save()

                    # recording current state
                    current_state = ProjectInfo.objects.get(pk=proj_id)

                    # recording audit log
                    client_ip = request.META['REMOTE_ADDR']
                    edit_project_log(previoust_state, current_state, projects, request.user, client_ip)

                    #recording activity log
                    event = 'Edit Project'
                    record_user_activity_log(
                        event       = event, 
                        actor       = request.user,
                        proj_name   = request.POST.get('project_name'),
                        session_id  = request.session.session_key
                        )

                    messages.success(request, "Project " + current_state.project_name + " has been updated successfully!")
                    data['form_is_valid'] = True

                else:
                    data['form_is_valid'] = False

            else:
                form = EditProjectForm()

            context = {

                'form' : form,
                'projects' : projects,
                'therapeutic_area_list' : therapeutic_area_list,
                'client_list' : client_list,

            }
            data['html_form'] =  render_to_string('edit_user_project.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


#each project dashboard
@login_required(login_url='/')
def project_dashboard(request, usr_id, proj_id):

    try:

        projects = ProjectInfo.objects.get(pk=proj_id)

        is_belongs = ProjectsXUsers.objects.get(project=projects, user=request.user)

        if request.user.id == int(usr_id) and not request.user.is_superuser and is_belongs.is_active:

            latest_client = ClientInfo.objects.latest('id')

            # Latest Global CSR
            try:
                csr_doc_latest = CSRTemplate.objects.filter(client=projects.client).latest('id')
            except CSRTemplate.DoesNotExist:
                csr_doc_latest = None
            # List of Global CSR
            try:
                csr_doc_list = CSRTemplate.objects.filter(client=projects.client).order_by('-created_on')[1:]
            except CSRTemplate.DoesNotExist:
                csr_doc_list = None

            # Latest Custom CSR
            try:
                custom_csr_doc_latest = CSRTemplateUser.objects.filter(project=proj_id).latest('id')
            except CSRTemplateUser.DoesNotExist:
                custom_csr_doc_latest = None
            # List of Custom CSR
            try:
                custom_csr_doc_list = CSRTemplateUser.objects.filter(project=proj_id).order_by('-created_on')[1:]
            except CSRTemplateUser.DoesNotExist:
                custom_csr_doc_list = None


            # Latest Protocol
            try:
                protocol_doc_latest = ProtocolFileUpload.objects.filter(project=proj_id).latest('id')
            except ProtocolFileUpload.DoesNotExist:
                protocol_doc_latest = None
            # List of Protocol
            try:
                protocol_doc_list = ProtocolFileUpload.objects.filter(project=proj_id).order_by('-uploaded_on')[1:]
            except ProtocolFileUpload.DoesNotExist:
                protocol_doc_list = None


            # Latest SAR
            try:
                sar_doc_latest = SarFileUpload.objects.filter(project=proj_id).latest('id')
            except SarFileUpload.DoesNotExist:
                sar_doc_latest = None
            # List of SAR
            try:
                sar_doc_list = SarFileUpload.objects.filter(project=proj_id).order_by('-uploaded_on')[1:]
            except SarFileUpload.DoesNotExist:
                sar_doc_list = None

            # Latest CSR Report
            try:
                csr_report_latest = Generated_Reports.objects.filter(project=proj_id).latest('id')
            except Generated_Reports.DoesNotExist:
                csr_report_latest = None
            # List of CSR Report
            try:
                csr_report_list = Generated_Reports.objects.filter(project=proj_id).order_by('-created_on')[1:]
            except Generated_Reports.DoesNotExist:
                csr_report_list = None

            # Check if other document info available
            try:
                is_another_doc_available = AnotherFileUploadUserInfo.objects.get(project=proj_id)
            except AnotherFileUploadUserInfo.DoesNotExist:
                is_another_doc_available = None

            # Latest another document
            try:
                another_doc_latest = AnotherFileUploadUser.objects.filter(project=proj_id).latest('id')
            except AnotherFileUploadUser.DoesNotExist:
                another_doc_latest = None
            # List of another document
            try:
                another_doc_list = AnotherFileUploadUser.objects.filter(project=proj_id).order_by('-uploaded_on')[1:]
            except AnotherFileUploadUser.DoesNotExist:
                another_doc_list = None


            context = {

                'projects'                 : projects,
                'csr_doc_latest'           : csr_doc_latest,
                'csr_doc_list'             : csr_doc_list,
                'custom_csr_doc_latest'    : custom_csr_doc_latest,
                'custom_csr_doc_list'      : custom_csr_doc_list,
                'protocol_doc_latest'      : protocol_doc_latest,
                'protocol_doc_list'        : protocol_doc_list,
                'sar_doc_latest'           : sar_doc_latest,
                'sar_doc_list'             : sar_doc_list,
                'csr_report_latest'        : csr_report_latest,
                'csr_report_list'          : csr_report_list,
                'usr_id'                   : usr_id,
                'is_another_doc_available' : is_another_doc_available,
                'another_doc_latest'       : another_doc_latest,
                'another_doc_list'         : another_doc_list,
                'latest_client'            : latest_client,

            }

            return render(request, 'project_dashboard.html', context)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


#to download any file
@login_required(login_url='/')
def download(request, path):

    try:

        file_path = os.path.join(settings.MEDIA_ROOT, path)
        if os.path.exists(file_path):

            with open(file_path, 'rb') as fh:

                response = HttpResponse(fh.read(), content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)

                return response

        raise Http404

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle activity log
@login_required(login_url='/')
def activity_log(request, usr_id):

    try:

        if request.user.id == int(usr_id) or request.user.is_superuser:

            data  = {}

            latest_client = ClientInfo.objects.latest('id')
            
            logs = LogsActivity.objects.filter(userid=usr_id)

            users = get_all_users()

            req_user = User.objects.get(pk=usr_id)

            if logs:
                logs  = LogsActivity.objects.filter(userid=usr_id).order_by('-id')

            return render(request, 'activity_log.html', {'logs' : logs, 'req_user' : req_user, 'users' : users, 'latest_client' : latest_client})

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



# to handle audit log
@login_required(login_url='/')
def audit_log(request, usr_id):

    try:

        if request.user.id == int(usr_id) or request.user.is_superuser:

            users = get_all_users()

            latest_client = ClientInfo.objects.latest('id')

            req_user = User.objects.get(pk=usr_id)

            if req_user.is_superuser:
               audit_logs = AuditLogsForMappingAdmin.objects.filter(user=usr_id).order_by('-id')

            else:
                audit_logs = AuditLogsForMappingUser.objects.filter(user=usr_id).order_by('-id')

            return render(request, 'audit_log.html', {'audit_logs' : audit_logs, 'users' : users, 'req_user' : req_user, 'latest_client' : latest_client})

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



# to dispaly global mapping in users role
@login_required(login_url='/')
def display_global_csr_mapping(request, cli_id):

    try:

        if not request.user.is_superuser:

            client_list   = ClientInfo.objects.all()
            latest_client = ClientInfo.objects.latest('id')
            req_client    = ClientInfo.objects.get(pk=cli_id)
            mapping_table = list(GlobalMappingTable.objects.filter(client=req_client).order_by('id'))
            ch_cnt        = global_mapping_table_structure(mapping_table, req_client)

            context       = {

                'mapping_table' : mapping_table,
                'ch_cnt'        : ch_cnt,
                'client_list'   : client_list,
                'latest_client' : latest_client,
                'req_client'    : req_client,

            }

            return render(request, 'global_csr_mapping.html', context=context)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle generate csr as per mapping
@login_required(login_url='/')
@csrf_exempt
def generate_csr(request, usr_id, proj_id):

    try:

        projects = ProjectInfo.objects.get(pk=proj_id)

        is_belongs = ProjectsXUsers.objects.get(project=projects, user=request.user)

        if request.user.id == int(usr_id) and not request.user.is_superuser and request.is_ajax() and is_belongs.is_active:

            data = {}
            filename = ''
            version  = ''

            # if request.is_ajax():

            try:
                response_data = json.loads(request.body)
                filename      = response_data[0]
                version       = response_data[1]

            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # recording logging
            csr_logger.info("Generate CSR started for project - '" + projects.project_name +"' by - " + request.user.username)

            status = generate_csr_document(usr_id, proj_id, filename, version)

            if status == 1:
                # to update project info if csr generated
                obj = ProjectInfo.objects.get(pk=proj_id)
                obj.generated = True
                obj.save()

                # recording activity log
                event = 'Generate CSR'
                record_user_activity_log(
                    event       = event, 
                    actor       = request.user,
                    proj_name   = projects.project_name,
                    session_id  = request.session.session_key
                    )

                messages.success(request, "CSR generated succesfully!")
                data['form_is_valid'] = True
                # recording logging
                csr_logger.info("Generate CSR completed for project - '" + projects.project_name +"' by - " + request.user.username)

            elif status == 2:
                messages.info(request, "CSR generated succesfully! But Some sections of data is not Copied, due to invalid format.")
                data['form_is_valid'] = True

            else:
                messages.error(request, "Custom Mapping not found. Please map through Edit Mapping!")
                data['form_is_valid'] = False

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



# edit csr mapping user
@login_required(login_url='/')
@csrf_exempt
def edit_csr_mapping(request, usr_id, proj_id):

    try:

        projects = ProjectInfo.objects.get(pk=proj_id)

        is_belongs = ProjectsXUsers.objects.get(project=projects, user=request.user)

        if request.user.id == int(usr_id) and not request.user.is_superuser and is_belongs.is_active:

            latest_client = ClientInfo.objects.latest('id')

            try:
                is_another_doc_available = AnotherFileUploadUserInfo.objects.get(project=proj_id)
            except AnotherFileUploadUserInfo.DoesNotExist:
                is_another_doc_available = None

            fetched_data         = get_global_mapped_data_usr(usr_id, proj_id)
            custom_mapping       = fetched_data[0]
            csr_headings         = fetched_data[1]
            protocol_headings    = fetched_data[2]
            sar_headings         = fetched_data[3]
            another_doc_headings = fetched_data[4]

            try:
                protocol_headings_json    = json.dumps(protocol_headings)
                sar_headings_json         = json.dumps(sar_headings)
                another_doc_headings_json = json.dumps(another_doc_headings)
            except Exception as e:
                
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # global admin mapped data
            pre_global_mapping = get_global_mapping_suggestions(csr_headings, protocol_headings, sar_headings, projects)

            global_pre_mapped_headings          = pre_global_mapping[0]
            list_global_pre_mapped_csr_headings = list(map(itemgetter('csr_heading'), global_pre_mapped_headings))

            global_pre_mapped_headings_parent          = pre_global_mapping[1]
            list_global_pre_mapped_csr_headings_parent = list(map(itemgetter('csr_heading'), global_pre_mapped_headings_parent))

            record_len = len(csr_headings) + len(global_pre_mapped_headings)

            loop = len(custom_mapping)

            if request.method == 'POST':
                
                try:

                    csr_headings_data  = request.POST.getlist('csr_headings[]')
                    source_data        = request.POST.getlist('source[]')
                    copy_headings_data = request.POST.getlist('copy_headings[]')
                    reason             = request.POST.get('reason')
                    parent_ids         = request.POST.getlist('child_parent_id[]')

                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                status = load_custom_mapping_to_model(csr_headings_data, source_data, copy_headings_data,usr_id, proj_id, parent_ids)

                if status == 1:
                    messages.success(request, 'Custom Mapping table updated scuccessfully!')

                    # loading library
                    load_library_with_user_configurations(projects)

                    # recording audit log
                    client_ip = request.META['REMOTE_ADDR']
                    edit_custom_csr_mapping_log(custom_mapping, csr_headings_data, source_data, copy_headings_data, reason, request.user, projects, client_ip)

                    # recording activity log
                    event = 'Edit Custom CSR'
                    record_user_activity_log(
                        event       = event, 
                        actor       = request.user,
                        proj_name   = projects.project_name, 
                        session_id  = request.session.session_key
                        )

                    return redirect('project_dashboard', usr_id=usr_id, proj_id=proj_id)
                    
                else:
                    messages.error(request, 'Please Map again!')

            context = {
                'projects'          : projects,
                'loop'              : loop,
                'custom_mapping'    : custom_mapping,
                'csr_headings'      : csr_headings,
                'protocol_headings' : protocol_headings,
                'protocol_headings_json' : protocol_headings_json,
                'sar_headings'      : sar_headings,
                'sar_headings_json' : sar_headings_json,
                'proj_id'           : proj_id,
                'usr_id'            : usr_id,
                'global_pre_mapped_headings' : global_pre_mapped_headings,
                'list_global_pre_mapped_csr_headings' : list_global_pre_mapped_csr_headings,
                'global_pre_mapped_headings_parent' : global_pre_mapped_headings_parent,
                'list_global_pre_mapped_csr_headings_parent' : list_global_pre_mapped_csr_headings_parent,
                'record_len' : record_len,
                'is_another_doc_available' : is_another_doc_available,
                'another_doc_headings' : another_doc_headings,
                'another_doc_headings_json' : another_doc_headings_json,
                'latest_client' : latest_client,

            }
            

            return render(request, 'edit_mapping.html', context)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# csr mapping confirmation user
@login_required(login_url='/')
@csrf_exempt
def confirm_csr_mapping_user(request, usr_id, proj_id):

    try:

        projects = ProjectInfo.objects.get(pk=proj_id)

        is_belongs = ProjectsXUsers.objects.get(project=projects, user=request.user)

        if request.user.id == int(usr_id) and not request.user.is_superuser and request.is_ajax() and is_belongs.is_active:
    
            data = {}

            custom_mapping = filtered_pre_mapped_user_data(usr_id, proj_id)

            csr_head   = ''
            src_file   = ''
            src_head   = ''
            parent_ids = ''

            if request.is_ajax():

                try:
                    response_data = json.loads(request.body)
                    csr_head   = response_data[0]
                    src_file   = response_data[1]
                    src_head   = response_data[2]
                    parent_ids = response_data[3]

                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            updated_mapping_form_data = csr_updated_user_form_data(csr_head, src_file, src_head, parent_ids, custom_mapping)

            context = {
                'updated_mapping_form_data' : updated_mapping_form_data,
                'custom_mapping'            : custom_mapping
            }

            data['html_form'] = render_to_string('confirm_csr_mapping_user.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


from .load_library import *

# Admin csr mapping
@login_required(login_url='/')
def csr_mapping(request, cli_id):

    try:

        if request.user.is_superuser:

            latest_client = ClientInfo.objects.latest('id')
            req_client    = ClientInfo.objects.get(pk=cli_id)

            file_locations      = get_file_locations(req_client)
            csr_headings        = GetHeadings_addHeaderNumbering(file_locations[0])
            protocol_headings   = GetHeadings_addHeaderNumbering(file_locations[1])
            sar_headings        = get_all_headings(file_locations[2])
            pre_mapped_headings = get_global_mapped_data(req_client)

            try:
                protocol_headings_json = json.dumps(protocol_headings)
                sar_headings_json      = json.dumps(sar_headings)
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            if request.method == 'POST':
                
                try:
                    csr_headings_data  = request.POST.getlist('csr_headings[]')
                    source_data        = request.POST.getlist('source[]')
                    copy_headings_data = request.POST.getlist('copy_headings[]')
                    reason             = request.POST.get('reason')
                    parent_ids         = request.POST.getlist('child_parent_id[]')

                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

                status = load_mapping_to_model(csr_headings_data, source_data, copy_headings_data, parent_ids, req_client)

                if status == 1:
                    messages.success(request, 'Global Mapping table updated scuccessfully!')

                    # loading library
                    load_library_with_admin_configurations(req_client)

                    # recording audit log
                    client_ip = request.META['REMOTE_ADDR']
                    edit_global_csr_mapping_log(pre_mapped_headings, csr_headings_data, source_data, copy_headings_data, reason, request.user, client_ip)

                    # recording activity log
                    event = 'CSR Mapping'
                    record_user_activity_log(
                        event       = event, 
                        actor       = request.user,
                        client      = req_client.client_name,
                        session_id  = request.session.session_key
                        )

                    return redirect('global_csr_upload', cli_id=cli_id)

                else:
                    messages.error(request, 'Please Map again!')

            context = {

                'csr_headings'           : csr_headings,
                'protocol_headings'      : protocol_headings,
                'protocol_headings_json' : protocol_headings_json,
                'sar_headings'           : sar_headings,
                'sar_headings_json'      : sar_headings_json,
                'pre_mapped_headings'    : pre_mapped_headings,
                'latest_client'          : latest_client,
                'req_client'             : req_client,
            }
            
            return render(request, 'admin_csr_mapping.html', context)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# csr mapping confirmation admin
@login_required(login_url='/')
@csrf_exempt
def confirm_csr_mapping_admin(request, cli_id):

    try:

        if request.user.is_superuser and request.is_ajax():
    
            data = {}

            req_client = ClientInfo.objects.get(pk=cli_id)

            pre_mapped_headings = filtered_pre_mapped_admin_data(req_client)

            csr_head = ''
            src_file = ''
            src_head = ''
            parent_ids = ''

            if request.is_ajax():

                try:
                    response_data = json.loads(request.body)
                    csr_head      = response_data[0]
                    src_file      = response_data[1]
                    src_head      = response_data[2]
                    parent_ids    = response_data[3]

                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            updated_mapping_form_data = csr_updated_admin_form_data(csr_head, src_file, src_head, parent_ids, pre_mapped_headings)

            context = {
                'updated_mapping_form_data' : updated_mapping_form_data,
                'pre_mapped_headings'       : pre_mapped_headings
            }

            data['html_form'] = render_to_string('confirm_csr_mapping_admin.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))
      
    

# to handle email configurations
@login_required(login_url='/')
def email_configuration(request):

    try:

        if request.is_ajax() and request.user.is_superuser:

            data = {}

            if request.method == 'POST':

                try:
                    form = EmailConfigurationForm(request.POST)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))
                    
                if form.is_valid():

                    # to delete already existed records
                    EmailConfiguration.objects.all().delete()

                    config = form.save(commit=False)
                    config.created_by = request.user
                    config.save()
                    
                    data['form_is_valid'] = True
                    messages.success(request, 'Email Configuration added succesfully')

                else:
                    data['form_is_valid'] = False
            else:
                form = EmailConfigurationForm()
                
            context = {
                'form' : form
            }
            data['html_form'] = render_to_string('email_configuration.html', context, request=request)

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle email logs
@login_required(login_url='/')
def mail_logs(request):

    try:

        if request.user.is_superuser:

            data = {}

            latest_client = ClientInfo.objects.latest('id')

            try:
                email_logs = LogsEmails.objects.all().order_by('-id')

            except LogsEmails.DoesNotExist:

                email_logs = None

            context = {

                'email_logs'    : email_logs,
                'latest_client' : latest_client,
            }

            return render(request, 'mail_logs.html', context)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle resend emails
@login_required(login_url='/')
def resend_email(request, mail_id):

    try:

        if request.user.is_superuser and request.is_ajax():

            data = {}

            obj  = LogsEmails.objects.get(pk=mail_id)

            #to resend email
            config  = EmailConfiguration.objects.last()
            backend = EmailBackend(

                host          = config.email_host,
                username      = config.email_host_user,
                password      = config.email_host_password,
                port          = config.email_port,
                use_tls       = True,
                fail_silently = True

            )
            from_email = config.email_default_mail
            email_subject = obj.subject
            to_email = obj.to_email
            html_content = obj.message_body
            email = EmailMessage(subject=email_subject, body=html_content, from_email=from_email, to=[to_email], connection=backend)
            email.content_subtype = 'html'
            email_status = email.send()

            # recording Email logs
            e_log = LogsEmails(

                    event = obj.event,
                    to_email = to_email,
                    from_email = from_email,
                    subject = email_subject,
                    message_body = html_content,
                    email_sent = email_status,
                    created_by = request.user

                )
            if email_status:

                obj.email_sent = True
                obj.save()

                e_log.email_response  = "Email sent scuccessfully"
                data['resend_status'] = True

                messages.success(request, 'Resend Email succesfully!')

                #recording activity log
                event = 'Resend Email'
                record_user_activity_log(
                    event       = event,
                    actor       = request.user, 
                    email       = to_email,
                    log_event   = obj.event, 
                    session_id  = request.session.session_key
                    )

            else:
                e_log.email_response  = "Not able to connect SMTP server"
                data['resend_status'] = False
                messages.error(request, 'Problem with connecting SMTP server. Please check the Email Configurations!')

            e_log.save()

            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


# to handle displayig logging
@login_required(login_url='/')
def display_logging(request):

    try:

        if request.user.is_superuser:

            log_arr = []

            latest_client = ClientInfo.objects.latest('id')

            file = BASE_DIR+'\\'+'media'+'\\logs\\'+'csr_except.log'

            with open(file) as f:
                lines = f.read()
                temp = []
                spl_lines = lines.split('\n[')

                log_arr = spl_lines[::-1]

            return render(request, 'logging.html', {'log_arr' : log_arr, 'latest_client' : latest_client})

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))
    

@login_required(login_url='/')
def clear_configurations__admin(request, cli_id):

    try:

        if request.user.is_superuser:

            req_client = ClientInfo.objects.get(pk=cli_id)

            # to delete files from filesystem
            del_file_on_clear__config_admin(req_client)

            # To Delete GlobalMappingTable
            try:
                GlobalMappingTable.objects.filter(client=req_client).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # To Delete all global/admin csr documents
            try:
                CSRTemplate.objects.filter(client=req_client).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # To Delete all global/admin Protocol documents
            try:
                ProtocolAdmin.objects.filter(client=req_client).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # To Delete all global/admin SAR documents
            try:
                SARAdmin.objects.filter(client=req_client).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # recording activity log
            event = 'Clear Configurations'
            record_user_activity_log(
                event       = event, 
                actor       = request.user,
                client      = req_client.client_name,
                session_id  = request.session.session_key
            )

            # return HttpResponseRedirect(reverse('global_csr_upload'))
            return redirect('global_csr_upload', cli_id=cli_id)

        else:
            return HttpResponseForbidden()


    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


@login_required(login_url='/')
def clear_configurations__usr(request, usr_id, proj_id):

    try:

        projects = ProjectInfo.objects.get(pk=proj_id)

        is_belongs = ProjectsXUsers.objects.get(project=projects, user=request.user)

        if request.user.id == int(usr_id) and not request.user.is_superuser and is_belongs.is_active:

            del_file_on_clear__config_usr(proj_id)

            # To Delete GlobalMappingTable
            try:
                CustomMappingTable.objects.filter(project=proj_id).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # To Delete all user csr documents
            try:
                CSRTemplateUser.objects.filter(project=proj_id).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # To Delete all user Protocol documents
            try:
                ProtocolFileUpload.objects.filter(project=proj_id).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # To Delete all user SAR documents
            try:
                SarFileUpload.objects.filter(project=proj_id).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # To Delete all another documents
            try:
                AnotherFileUploadUser.objects.filter(project=proj_id).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # To Delete all another documents info
            try:
                AnotherFileUploadUserInfo.objects.filter(project=proj_id).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


            # To Delete all user generated_report documents
            try:
                Generated_Reports.objects.filter(project=proj_id).delete()
            except Exception as e:
                csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))

            # to update project info if csr generated
            projects.generated = False
            projects.save()

            # recording activity log
            event = 'Configurations Clear'
            record_user_activity_log(
                event       = event, 
                actor       = request.user,
                proj_name   = projects.project_name, 
                session_id  = request.session.session_key
            )


            return redirect('project_dashboard', usr_id=usr_id, proj_id=proj_id)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))


@login_required(login_url='/')
@csrf_exempt
def add_another_document__usr(request, usr_id, proj_id):

    try:

        project = ProjectInfo.objects.get(pk=proj_id)

        is_belongs = ProjectsXUsers.objects.get(project=project, user=request.user)

        if request.user.id == int(usr_id) and request.is_ajax() and is_belongs.is_active:

            data = {}

            if request.is_ajax():
                response_data = json.loads(request.body)
                source_name = response_data[0]
                
                if source_name != '':
                    instance = AnotherFileUploadUserInfo.objects.create(

                            source_name = source_name,
                            project     = project,
                            created_by  = request.user

                        )
                    instance.save()
                    messages.success(request, 'Added new document succesfully!')
                    data['add_status'] = True

                    # recording activity log
                    event = 'Another Document'
                    record_user_activity_log(
                        event       = event, 
                        actor       = request.user,
                        proj_name   = project.project_name,
                        source_name = source_name,
                        session_id  = request.session.session_key
                    )

                else:
                    messages.error(request, 'Something went wrong, please try later!')
                    data['add_status'] = False
            
            return JsonResponse(data)

        else:
            return HttpResponseForbidden()


    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



# to create client
@login_required(login_url='/')
def add_client(request):

    try:

        if request.is_ajax() and request.user.is_superuser:

            data = {}

            if request.method == 'POST':

                try:
                    form = AddClientForm(request.POST)
                except Exception as e:
                    csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))
                    
                if form.is_valid():

                    obj = form.save(commit=False)
                    obj.created_by = request.user
                    obj.save()
                    
                    data['form_is_valid'] = True
                    messages.success(request, 'Client added succesfully')

                else:
                    data['form_is_valid'] = False
            else:
                form = AddClientForm()
                
            context = {
                'form' : form
            }
            data['html_form'] = render_to_string('add_client.html', context, request=request)
            return JsonResponse(data)

        else:
            return HttpResponseForbidden()

    except Exception as e:
        csr_except_logger.critical(str(e) + '\n' + str(traceback.format_exc()))



