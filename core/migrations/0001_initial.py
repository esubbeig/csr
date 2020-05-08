# Generated by Django 2.2.6 on 2020-04-17 11:18

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLogEvents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(max_length=150)),
                ('message', models.CharField(max_length=1024)),
            ],
            options={
                'db_table': 'activity_log_events',
            },
        ),
        migrations.CreateModel(
            name='GlobalMappingTable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csr_heading', models.CharField(max_length=1024)),
                ('source_file', models.CharField(max_length=1024, null=True)),
                ('copy_headings', models.CharField(max_length=2048, null=True)),
                ('parent_id', models.CharField(default=0, max_length=1024)),
            ],
            options={
                'db_table': 'global_mapping_table',
            },
        ),
        migrations.CreateModel(
            name='LogsActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(max_length=64)),
                ('message', models.CharField(max_length=1024)),
                ('userid', models.IntegerField()),
                ('created_on', models.DateTimeField(auto_now=True)),
                ('sessionid', models.CharField(max_length=256)),
            ],
            options={
                'db_table': 'logs_activity',
            },
        ),
        migrations.CreateModel(
            name='ProjectInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_name', models.CharField(max_length=512)),
                ('protocol_id', models.CharField(error_messages={'unique': 'This protocol id already existed.'}, max_length=32, unique=True)),
                ('phase', models.CharField(max_length=16)),
                ('client', models.CharField(max_length=32)),
                ('active', models.BooleanField(default=True)),
                ('delete', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('generated', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'projectinfo',
            },
        ),
        migrations.CreateModel(
            name='TherapeuticArea',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('therapeutic_area', models.CharField(max_length=512)),
            ],
            options={
                'db_table': 'ikp_therapeutic_area',
            },
        ),
        migrations.CreateModel(
            name='UserProjectCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_count', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'usersXprojectCount',
            },
        ),
        migrations.CreateModel(
            name='SarFileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sar_document_location', models.FileField(default=None, upload_to='users/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['docx'])])),
                ('version_no', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('uploaded_on', models.DateTimeField(auto_now_add=True)),
                ('delete', models.BooleanField(default=False)),
                ('comments', models.CharField(blank=True, max_length=512, null=True)),
                ('created_by', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ProjectInfo')),
                ('therapeutic_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.TherapeuticArea')),
            ],
            options={
                'db_table': 'sar_file_upload',
            },
        ),
        migrations.CreateModel(
            name='SARAdmin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sar_template_location', models.FileField(default=None, upload_to='admin/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['docx'])])),
                ('version_no', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('comments', models.CharField(blank=True, max_length=512, null=True)),
                ('delete', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('therapeutic_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.TherapeuticArea')),
            ],
            options={
                'db_table': 'ikp_sar_admin',
            },
        ),
        migrations.CreateModel(
            name='ProtocolFileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('protocol_document_location', models.FileField(default=None, upload_to='users/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['docx'])])),
                ('version_no', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('uploaded_on', models.DateTimeField(auto_now_add=True)),
                ('delete', models.BooleanField(default=False)),
                ('comments', models.CharField(blank=True, max_length=512, null=True)),
                ('created_by', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ProjectInfo')),
                ('therapeutic_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.TherapeuticArea')),
            ],
            options={
                'db_table': 'protocol_file_upload',
            },
        ),
        migrations.CreateModel(
            name='ProtocolAdmin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('protocol_template_location', models.FileField(default=None, upload_to='admin/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['docx'])])),
                ('version_no', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('comments', models.CharField(blank=True, max_length=512, null=True)),
                ('delete', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('therapeutic_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.TherapeuticArea')),
            ],
            options={
                'db_table': 'ikp_protocol_admin',
            },
        ),
        migrations.CreateModel(
            name='ProjectsXUsers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projectxusers_created_by', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ProjectInfo')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'projectsXusers',
            },
        ),
        migrations.AddField(
            model_name='projectinfo',
            name='therapeutic_area',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.TherapeuticArea'),
        ),
        migrations.CreateModel(
            name='LogsEmails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(max_length=64)),
                ('to_email', models.CharField(max_length=128)),
                ('from_email', models.CharField(max_length=1024)),
                ('subject', models.CharField(max_length=512)),
                ('message_body', models.CharField(max_length=1024)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('email_sent', models.BooleanField(default=False)),
                ('email_response', models.CharField(blank=True, max_length=2048, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'logs_emails',
            },
        ),
        migrations.CreateModel(
            name='Generated_Reports',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generated_report_path', models.CharField(max_length=200)),
                ('version_no', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('delete', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ProjectInfo')),
                ('therapeutic_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.TherapeuticArea')),
            ],
            options={
                'db_table': 'generated_reports',
            },
        ),
        migrations.CreateModel(
            name='ExtendedUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=10)),
                ('deleted', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_created_by', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'extendeduser',
            },
        ),
        migrations.CreateModel(
            name='EmailConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_host', models.CharField(max_length=1024)),
                ('email_host_user', models.CharField(max_length=255)),
                ('email_host_password', models.CharField(blank=True, max_length=255, null=True)),
                ('email_port', models.PositiveSmallIntegerField(default=587)),
                ('email_default_mail', models.CharField(blank=True, max_length=255, null=True)),
                ('email_use_tls', models.BooleanField(default=True)),
                ('email_fail_silently', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'email_configuration',
            },
        ),
        migrations.CreateModel(
            name='CustomMappingTable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csr_heading', models.CharField(max_length=1024)),
                ('source_file', models.CharField(max_length=1024, null=True)),
                ('copy_headings', models.CharField(max_length=2048, null=True)),
                ('parent_id', models.CharField(default=0, max_length=1024)),
                ('created_by', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ProjectInfo')),
            ],
            options={
                'db_table': 'custom_mapping_table',
            },
        ),
        migrations.CreateModel(
            name='CSRTemplateUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csr_template_location', models.FileField(default=None, upload_to='users/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['docx'])])),
                ('version_no', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('comments', models.CharField(blank=True, max_length=512, null=True)),
                ('delete', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ProjectInfo')),
                ('therapeutic_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.TherapeuticArea')),
            ],
            options={
                'db_table': 'ikp_csrtemplateuser',
            },
        ),
        migrations.CreateModel(
            name='CSRTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csr_template_location', models.FileField(default=None, upload_to='admin/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['docx'])])),
                ('version_no', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('comments', models.CharField(blank=True, max_length=512, null=True)),
                ('delete', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('therapeutic_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.TherapeuticArea')),
            ],
            options={
                'db_table': 'ikp_csrtemplate',
            },
        ),
        migrations.CreateModel(
            name='AuditLogsForMappingUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(blank=True, max_length=100, null=True)),
                ('previous_state', models.TextField(blank=True)),
                ('current_state', models.TextField(blank=True)),
                ('reason', models.CharField(max_length=2048, null=True)),
                ('ip', models.CharField(max_length=100)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ProjectInfo')),
                ('user', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'auditlogs_for_mapping_user',
            },
        ),
        migrations.CreateModel(
            name='AuditLogsForMappingAdmin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(blank=True, max_length=100, null=True)),
                ('previous_state', models.TextField(blank=True)),
                ('current_state', models.TextField(blank=True)),
                ('reason', models.CharField(max_length=2048, null=True)),
                ('ip', models.CharField(max_length=100)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'auditlogs_for_mapping_admin',
            },
        ),
        migrations.CreateModel(
            name='AnotherFileUploadUserInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_name', models.CharField(max_length=100)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ProjectInfo')),
                ('therapeutic_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.TherapeuticArea')),
            ],
            options={
                'db_table': 'another_file_upload_user_info',
            },
        ),
        migrations.CreateModel(
            name='AnotherFileUploadUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('another_document_location', models.FileField(default=None, upload_to='users/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['docx'])])),
                ('version_no', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('uploaded_on', models.DateTimeField(auto_now_add=True)),
                ('delete', models.BooleanField(default=False)),
                ('comments', models.CharField(blank=True, max_length=512, null=True)),
                ('created_by', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.ProjectInfo')),
                ('therapeutic_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.TherapeuticArea')),
            ],
            options={
                'db_table': 'another_file_upload_user',
            },
        ),
    ]
