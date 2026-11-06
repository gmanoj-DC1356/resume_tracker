from django.contrib import admin

from .models import CandidateProfile


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("resume", "role_title", "years_experience")
    search_fields = ("resume__candidate_name", "role_title")
