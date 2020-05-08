from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

# admin.site.register(CSRTemplate)

# @admin.register(GlobalMappingTable)
# class GlobalMappingTableAdmin(ImportExportModelAdmin):
#     pass

@admin.register(ActivityLogEvents)
class ActivityLogEventsAdmin(ImportExportModelAdmin):
    pass

@admin.register(TherapeuticArea)
class TherapeuticAreaAdmin(ImportExportModelAdmin):
    pass

@admin.register(Library)
class Library(ImportExportModelAdmin):
    pass

    