import uuid
from django.db import models

# Create your models here.
class ScrapingType(models.Model):
    slot     = models.CharField(max_length=150)
    slug     = models.SlugField(max_length=250, null=True, blank=True)
    heading  = models.CharField(max_length=150)
    scraping_type = models.CharField(max_length=50, null=True, blank=True)
    short_description = models.TextField()

    def __str__(self):
        return self.heading

class ScrapingInfo(models.Model):
    sales_url = models.TextField(null=True, blank=True)
    session_cookie = models.TextField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    remove_duplicate_profiles = models.BooleanField(default=False, null=True, blank=True)
    input_type = models.CharField(max_length=50, null=True, blank=True)
    slots = models.CharField(max_length=10, null=True, blank=True, default='0')
    scraping_id = models.CharField(max_length=15 ,null=True, blank=True)
    scraping_name = models.CharField(max_length=255, null=True, blank=True, default='Untitled Sales Navigator Search Export')
    headline = models.CharField(max_length=255, null=True, blank=True)
    authentication = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    starting_time = models.DateTimeField(null=True, blank=True)
    duration = models.CharField(max_length=100, null=True, blank=True)
    launch = models.BooleanField(default=False, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    number_of_profiles = models.IntegerField(null=True, blank=True)
    number_of_results_per_search = models.IntegerField(null=True, blank=True)
    number_of_lines_per_launch = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.scraping_name or "Scraping Info"} - {self.starting_time}'

    class Meta:
        indexes = [
            models.Index(fields=['starting_time']),
            models.Index(fields=['status']),
        ]

class LinkedInProfile(models.Model):
    scraping_id = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    linkedin_url = models.TextField(null=True, blank=True)
    connections = models.CharField(max_length=50, null=True, blank=True)
    years_in_position = models.CharField(max_length=50, null=True, blank=True)
    months_in_position = models.CharField(max_length=50, null=True, blank=True)
    years_in_company = models.CharField(max_length=50, null=True, blank=True)
    months_in_company = models.CharField(max_length=50, null=True, blank=True)
    sales_navigator_url = models.TextField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    headline = models.CharField(max_length=200, null=True, blank=True)
    is_premium = models.BooleanField(default=False)
    current_positions = models.CharField(max_length=50 ,null=True, blank=True)
    phone_no = models.CharField(max_length=15, null=True, blank=True)
    email_address = models.EmailField(null=True, blank=True)
    connection_degree = models.CharField(max_length=50, null=True, blank=True)
    profile_picture = models.TextField(null=True, blank=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    query = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.job_title}"

class LinkedInCompany(models.Model):
    scraping_id = models.CharField(max_length=100, null=True, blank=True)
    company_name = models.CharField(max_length=100, null=True, blank=True)
    company_website = models.TextField(null=True, blank=True)
    company_number = models.CharField(max_length=15, null=True, blank=True)
    company_domain = models.CharField(max_length=100, null=True, blank=True)
    company_headquarters = models.CharField(max_length=100, null=True, blank=True)
    company_id = models.CharField(max_length=150, null=True, blank=True)
    regular_company_url = models.TextField(null=True, blank=True)
    vmid = models.CharField(max_length=100, null=True, blank=True)
    company_industry = models.CharField(max_length=100, null=True, blank=True)
    company_specialties = models.TextField(null=True, blank=True)
    company_employee_count = models.CharField(max_length=50, null=True, blank=True)
    company_employee_range = models.CharField(max_length=50, null=True, blank=True)
    company_location = models.CharField(max_length=100, null=True, blank=True)
    company_linkedin_id_url = models.TextField(null=True, blank=True)
    company_description = models.TextField(null=True, blank=True)
    company_profile_picture = models.TextField(null=True, blank=True)
    company_year_founded = models.CharField(max_length=50 ,null=True, blank=True)
    sales_navigator_company_url = models.TextField(null=True, blank=True)
    is_hiring = models.BooleanField(default=False)
    specialties = models.CharField(max_length=50, null=True, blank=True)
    company_type = models.CharField(max_length=50, null=True, blank=True)
    company_revenue_min = models.CharField(max_length=50, null=True, blank=True)
    company_revenue_max = models.CharField(max_length=50, null=True, blank=True)
    city    = models.CharField(max_length=50, null=True, blank=True)
    geographicArea = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    query = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name