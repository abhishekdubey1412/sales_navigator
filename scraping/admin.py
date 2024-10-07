from django.contrib import admin
from .models import ScrapingType, ScrapingInfo, LinkedInProfile, LinkedInCompany

@admin.register(ScrapingType)
class ScrapingTypeAdmin(admin.ModelAdmin):
    list_display = ('slot', 'slug', 'heading', 'scraping_type')
    search_fields = ('slot', 'slug', 'heading', 'scraping_type')
    list_filter = ('scraping_type',)
    ordering = ('heading',)

@admin.register(ScrapingInfo)
class ScrapingInfoAdmin(admin.ModelAdmin):
    list_display = ('scraping_name', 'starting_time', 'status', 'number_of_profiles')
    search_fields = ('scraping_name', 'status', 'email')
    list_filter = ('status', 'starting_time')
    ordering = ('-starting_time',)

@admin.register(LinkedInProfile)
class LinkedInProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job_title', 'location', 'linkedin_url', 'timestamp')
    search_fields = ('full_name', 'job_title', 'location', 'linkedin_url')
    list_filter = ('location', 'is_premium', 'timestamp')
    ordering = ('-timestamp',)

@admin.register(LinkedInCompany)
class LinkedInCompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_website', 'company_industry', 'company_employee_count', 'timestamp')
    search_fields = ('company_name', 'company_website', 'company_industry')
    list_filter = ('company_industry', 'company_employee_count', 'timestamp')
    ordering = ('-timestamp',)