import csv
import random
import threading
from .scrape_data import *
from core.models import WebsiteDetails
from subscriptions.models import Package
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import ScrapingType, ScrapingInfo, LinkedInProfile, LinkedInCompany
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404

# Function to get common context data for templates
def get_common_context(request):
    return {
        "active_package": Package.objects.filter(user=request.user, status="active").first(),
        "scraping_types": ScrapingType.objects.all(),
        "website_details": WebsiteDetails.objects.first(),
    }

# View for browser scraping page
@login_required(login_url='sign_in')
def browser_scraping(request):
    context = get_common_context(request)
    context["total_seconds"] = context["active_package"].execution_time_hours.total_seconds() if context["active_package"] else 0
    return render(request, 'scraping/browser-scraping.html', context)

# View for scraping setup page
@login_required(login_url='sign_in')
def scraping_setup(request, slug):
    context = get_common_context(request)
    context["total_seconds"] = context["active_package"].execution_time_hours.total_seconds() if context["active_package"] else 0
    scraping_type = get_object_or_404(ScrapingType, slug=slug)
    
    if request.method == "POST":
        data = request.POST
        sales_url = data.get('sales_url')
        session_cookie = data.get('session_cookie')
        browser_agent = data.get('browser_agent')
        export_per_search = data.get('export_per_search')
        export_per_launch = data.get('export_per_launch')
        name_results_file = data.get('name_results_file')
        fields_to_keep = data.get('fields_to_keep')
        csv_file = request.FILES.get('csv_file_url')

        # Generate a unique scraping ID
        scraping_id = random.randint(1, 100000000000000)
        while ScrapingInfo.objects.filter(scraping_id=scraping_id).exists():
            scraping_id = random.randint(1, 100000000000000)
        
        # Create a new ScrapingInfo object
        if csv_file:
            ScrapingInfo.objects.create(
                session_cookie=session_cookie,
                user_agent=browser_agent,
                number_of_lines_per_launch=export_per_launch,
                number_of_results_per_search=export_per_search,
                input_type=scraping_type.scraping_type,
                headline=scraping_type.heading,
                scraping_id=scraping_id,
                slots=scraping_type.slot,
                csv_file=csv_file
            )
        else:
            ScrapingInfo.objects.create(
                sales_url=sales_url,
                session_cookie=session_cookie,
                user_agent=browser_agent,
                number_of_lines_per_launch=export_per_launch,
                number_of_results_per_search=export_per_search,
                input_type=scraping_type.scraping_type,
                headline=scraping_type.heading,
                scraping_id=scraping_id,
                slots=scraping_type.slot
            )

        return redirect('launch', scraping_id=str(scraping_id))

    context.update({
        "scraping_type": scraping_type,
    })
    return render(request, 'scraping/scraping-setup.html', context)

# View for scraping blog page
@login_required(login_url='sign_in')    
def scraping_blog(request, slug):
    context = get_common_context(request)
    scraping_type = get_object_or_404(ScrapingType, slug=slug)
    context.update({
        'scraping_type': scraping_type,
    })
    return render(request, 'scraping/blog.html', context)

# View to launch the scraping process
@login_required(login_url='sign_in')
def launch(request, scraping_id):
    context = get_common_context(request)
    scraping_info = get_object_or_404(ScrapingInfo, scraping_id=scraping_id)
    active_package = Package.objects.filter(user=request.user, status="active").first()

    if request.method == "POST":
        if scraping_info.sales_url:
            scraping_info.email = request.user.email
            scraping_info.save()

            # Define scraping functions based on input type
            scraping_funcs = {
                "PNormal": people_normal_scrape_and_save_data,
                "PDeep": profile_deep_scrape_and_save_data,
                "PDeepCSV": profile_deep_scrape_and_save_data_csv,
                "CNormal": company_normal_scrape_and_save_data,
                "CDeep": company_deep_scrape_and_save_data,
                "CDeepCSV": company_deep_scrape_and_save_data_csv,
            }

            scrape_func = scraping_funcs.get(scraping_info.input_type)
            if scrape_func:
                # Start the scraping process in a new thread
                thread = threading.Thread(target=scrape_func, args=(scraping_info.sales_url, scraping_info.session_cookie, 
                                                                    scraping_info.id, scraping_info.user_agent, request, active_package))
                thread.start()

                return redirect('launch', scraping_id)
        elif scraping_info.csv_file:
            scraping_info.email = request.user.email
            scraping_info.save()

            # Define scraping functions based on input type
            scraping_funcs = {
                "PDeepCSV": profile_deep_scrape_and_save_data_csv,
                "CDeepCSV": company_deep_scrape_and_save_data_csv,
                }

            scrape_func = scraping_funcs.get(scraping_info.input_type)
            if scrape_func:
                # Start the scraping process in a new thread
                thread = threading.Thread(target=scrape_func, args=(scraping_info.csv_file, scraping_info.session_cookie, 
                                                                    scraping_info.id, scraping_info.user_agent, request, active_package))
                thread.start()
                return redirect('launch', scraping_id)
        else:
            return redirect('browser-scraping')
    
    context.update({
        'scraping_info': scraping_info
    })
    return render(request, 'scraping/launch.html', context)

# View to get scraping info details
@login_required(login_url='sign_in')
def scraping_info_detail(request, scraping_id):
    if request.method == 'GET':
        # Extract input_type from request query parameters
        input_type = request.GET.get('input-type')
        
        # Handle scraping ID as provided
        scraping_id = scraping_id.split('/')[0]  # Get the ID from the URL path

        # Count total records based on input type
        if input_type == 'CNormal' or 'CDeep':
            total_records = LinkedInCompany.objects.filter(scraping_id=scraping_id).count()
        elif input_type == 'PNormal' or 'PDeep':
            total_records = LinkedInProfile.objects.filter(scraping_id=scraping_id).count()
        else:
            total_records = 0  # Default case if input_type is unrecognized
        
        scraping_info = get_object_or_404(ScrapingInfo, scraping_id=scraping_id)
        scraping_info.number_of_profiles = total_records
        scraping_info.save()
        
        # Prepare the data to be returned as JSON
        data = {
            'id': scraping_info.id,
            'scraping_name': scraping_info.scraping_name,
            'sales_url': scraping_info.sales_url,
            'input_type': scraping_info.input_type,
            'email': scraping_info.email,
            'starting_time': scraping_info.starting_time,
            'duration': scraping_info.duration,
            'launch': scraping_info.launch,
            'status': scraping_info.status,
            'number_of_profiles': scraping_info.number_of_profiles,
            'number_of_results_per_search': scraping_info.number_of_results_per_search,
            'number_of_lines_per_launch': scraping_info.number_of_lines_per_launch,
            'remove_duplicate_profiles': scraping_info.remove_duplicate_profiles,
            'session_cookie': scraping_info.session_cookie,
            'user_agent': scraping_info.user_agent,
            'authentication': scraping_info.authentication,
            'total_records': scraping_info.number_of_profiles
        }
        
        return JsonResponse(data)

# View to get scraped data
@login_required(login_url='sign_in')
def scraped_data(request, scraping_id):
    if request.method == 'GET':
        input_type = request.GET.get('input-type')
        # Handle scraping ID as provided
        scraping_id = scraping_id.split('/')[0]

        # Fetch profiles and companies based on scraping_id
        if input_type in ['CNormal', 'CDeep', 'CDeepCSV']:
            companies = get_list_or_404(LinkedInCompany, scraping_id=scraping_id)

            if input_type == 'CNormal':
                combined_data_list = [{
                    'sales_navigator_company_url': company.sales_navigator_company_url,
                    'company_name': company.company_name,
                    'company_description': company.company_description,
                    'company_id': company.company_id,
                    'regular_company_url': company.regular_company_url,
                    'company_industry': company.company_industry,
                    'company_employee_count': company.company_employee_count,
                    'company_profile_picture': company.company_profile_picture,
                    'is_hiring': company.is_hiring,
                } for company in companies]
            
            elif input_type == 'CDeepCSV' or 'CDeep':
                combined_data_list = [{
                'company_name': company.company_name,
                'company_description': company.company_description,
                'company_industry': company.company_industry,
                'company_employee_count': company.company_employee_count,
                'company_location': company.company_location,
                'country': company.country,
                'geographicArea': company.geographicArea,
                'city': company.city,
                'company_id': company.company_id,
                'regular_company_url': company.regular_company_url,
                'sales_navigator_company_url': company.sales_navigator_company_url,
                'company_website': company.company_website,
                'company_employee_range': company.company_employee_range,
                'company_profile_picture': company.company_profile_picture,
                'company_year_founded': company.company_year_founded,
                'company_revenue_min': company.company_revenue_min,
                'company_revenue_max': company.company_revenue_max,
                'company_number': company.company_number,
                'address': company.address,
                'postal_code': company.postal_code,
                'specialties': company.specialties,
                'company_type': company.company_type,
                'decision_makers_search_url': company.decision_makers_search_url,
                'employee_search_url': company.employee_search_url,
                'decision_makers_count': company.decision_makers_count,
                'query': company.query,
                'timestamp': company.timestamp,
            } for company in companies]

        elif input_type in ["PNormal", "PDeep", "PDeepCSV"]:
            profiles = get_list_or_404(LinkedInProfile, scraping_id=scraping_id)
            companies = get_list_or_404(LinkedInCompany, scraping_id=scraping_id)

            # Use the minimum length to avoid index errors
            min_length = min(len(profiles), len(companies))
            combined_data_list = []

            for i in range(min_length):
                profile = profiles[i]
                company = companies[i]

                if input_type == "PNormal":
                    combined_data = {
                        'full_name': profile.full_name,
                        'first_name': profile.first_name,
                        'last_name': profile.last_name,
                        'company_name': company.company_name,
                        'job_title': profile.job_title,
                        'company_id': company.company_id,
                        'sales_navigator_company_url': company.sales_navigator_company_url,
                        'regular_company_url': company.regular_company_url,
                        'summary': profile.summary,
                        'company_industry': company.company_industry,
                        'company_location': company.company_location,
                        'location': profile.location,
                        'connection_degree': profile.connection_degree,
                        'profile_picture': profile.profile_picture,
                        'vmid': company.vmid,
                        'linkedin_url': profile.linkedin_url,
                        'is_premium': profile.is_premium,
                    }

                    combined_data_list.append(combined_data)

                else:
                    combined_data = {
                        'sales_navigator_url': profile.sales_navigator_url,
                        'full_name': profile.full_name,
                        'first_name': profile.first_name,
                        'last_name': profile.last_name,
                        'profile_picture': profile.profile_picture,
                        'job_title': profile.job_title,
                        'is_premium': profile.is_premium,
                        'location': profile.location,
                        'headline': profile.headline,
                        'connections': profile.connections,
                        'linkedin_url': profile.linkedin_url,
                        'summary': profile.summary,
                        'years_in_company': profile.years_in_company,
                        'months_in_company': profile.months_in_company,
                        'years_in_position': profile.years_in_position,
                        'months_in_position': profile.months_in_position,
                        'current_positions': profile.current_positions,
                        'company_name': company.company_name,
                        'company_linkedin_id_url': company.company_linkedin_id_url,
                        'company_website': company.company_website,
                        'company_domain': company.company_domain,
                        'company_industry': company.company_industry,
                        'company_specialties': company.company_specialties,
                        'company_employee_count': company.company_employee_count,
                        'company_employee_range': company.company_employee_range,
                        'company_location': company.company_location,
                        'company_year_founded': company.company_year_founded,
                        'company_description': company.company_description,
                        'company_profile_picture': company.company_profile_picture,
                        'company_number': company.company_number,
                    }
                    combined_data_list.append(combined_data)

        # Return the combined data as JSON
        return JsonResponse(combined_data_list, safe=False)

# View to rename scraping info
@login_required(login_url='sign_in')
def rename_scraping_info(request, scraping_id):
    if request.method == 'POST':
        new_name = request.POST.get('new_name')
        scraping_info = get_object_or_404(ScrapingInfo, scraping_id=scraping_id, email=request.user.email)
        scraping_info.scraping_name = new_name
        scraping_info.save()
        return redirect('home')

# View to delete scraping info
@login_required(login_url='sign_in')
def delete_scraping_info(request, scraping_id):
    scraping_info = get_object_or_404(ScrapingInfo, scraping_id=scraping_id, email=request.user.email)
    slots = scraping_info.slots
    scraping_info.delete()
    active_package = Package.objects.filter(user=request.user, status="active").first()
    active_package.used_slots -= int(slots.split(' ')[0])
    active_package.save()
    return redirect('home')

# View to export scraped data to CSV
@login_required(login_url='sign_in')
def export_csv(request, scraping_id):
    scraping_info = get_object_or_404(ScrapingInfo, scraping_id=scraping_id, email=request.user.email)
    
    # Fetch LinkedInProfile and LinkedInCompany data
    if scraping_info.input_type == "PNormal" or "PDeep" or "PDeepCSV":
        profiles = LinkedInProfile.objects.filter(scraping_id=scraping_id)
        companies = LinkedInCompany.objects.filter(scraping_id=scraping_id)
    elif scraping_info.input_type == "CNormal" or "CDeep" or "CDeepCSV":
        companies = LinkedInCompany.objects.filter(scraping_id=scraping_id)
    else:
        return redirect('home')
    
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{scraping_info.scraping_name}.csv"'
    active_package = Package.objects.filter(user=request.user, status="active").first()

    writer = csv.writer(response)
    
    # Write the headers
    if scraping_info.input_type == "PNormal":
        writer.writerow([
            'Full Name', 'First Name', 'Last Name', 'Connection Degree', 'Summary', 'Query', 'Location', 
            'Is Premium', 'Sales Navigator URL', 'LinkedIn URL', 'Profile Picture', 'Job Title', 'Company Name', 
            'Company ID', 'Sales Navigator Company URL', 'Regular Company URL', 'VMID', 'Company Location', 'Company Industry'
        ])
        
        for i, profile in enumerate(profiles):
            if not active_package.unlimited_export and i >= 500:
                break
            company = companies.first()
            writer.writerow([
                profile.full_name, profile.first_name, profile.last_name, profile.connection_degree, profile.summary, 
                profile.query, profile.location, profile.is_premium, profile.sales_navigator_url, profile.linkedin_url, 
                profile.profile_picture, profile.job_title, company.company_name if company else '', 
                company.company_id if company else '', company.sales_navigator_company_url if company else '', 
                company.regular_company_url if company else '', company.vmid if company else '', 
                company.company_location if company else '', company.company_industry if company else ''
            ])
    elif scraping_info.input_type == "PDeep" or scraping_info.input_type == "PDeepCSV":
        writer.writerow([
            'Query', 'Sales Navigator URL', 'Full Name', 'First Name', 'Last Name', 'Profile Picture', 'Job Title', 
            'Is Premium', 'Location', 'Headline', 'Connections', 'LinkedIn URL', 'Summary', 'Years in Company', 
            'Months in Company', 'Years in Position', 'Months in Position', 'Current Positions', 'Company Name', 
            'Company LinkedIn ID URL', 'Company Website', 'Company Domain', 'Company Industry', 'Company Specialties', 
            'Company Employee Count', 'Company Employee Range', 'Company Location', 'Company Year Founded', 
            'Company Description', 'Company Profile Picture', 'Company Number'
        ])
        
        for i, profile in enumerate(profiles):
            if not active_package.unlimited_export and i >= 500:
                break
            company = companies.first()
            writer.writerow([   
                profile.query, profile.sales_navigator_url, profile.full_name, profile.first_name, profile.last_name, 
                profile.profile_picture, profile.job_title, profile.is_premium, profile.location, profile.headline, 
                profile.connections, profile.linkedin_url, profile.summary, profile.years_in_company, profile.months_in_company, 
                profile.years_in_position, profile.months_in_position, profile.current_positions, company.company_name if company else '', 
                company.company_linkedin_id_url if company else '', company.company_website if company else '', 
                company.company_domain if company else '', company.company_industry if company else '', 
                company.company_specialties if company else '', company.company_employee_count if company else '', 
                company.company_employee_range if company else '', company.company_location if company else '', 
                company.company_year_founded if company else '', company.company_description if company else '', 
                company.company_profile_picture if company else '', company.company_number if company else ''
            ])   
    elif scraping_info.input_type == "CNormal":
        writer.writerow([
            'Sales Navigator Company URL', 'Company Name', 'Company Description', 'Company ID', 'Regular Company URL', 
            'Company Industry', 'Company Employee Count', 'Company Profile Picture', 'Is Hiring', 'Query'
        ])
        
        for i, company in enumerate(companies):
            if not active_package.unlimited_export and i >= 500:
                break
            writer.writerow([
                company.sales_navigator_company_url, company.company_name, company.company_description, company.company_id, 
                company.regular_company_url, company.company_industry, company.company_employee_count, 
                company.company_profile_picture, company.is_hiring, company.query
            ])
    elif scraping_info.input_type == "CDeep" or scraping_info.input_type == "CDeepCSV":
        writer.writerow([
            'Query', 'Company Name', 'Company ID', 'Sales Navigator Company URL', 'Company Profile Picture', 
            'Company Website', 'Company Industry', 'Company Employee Count', 'Company Employee Range', 
            'Company Year Founded', 'Company Number', 'Company Description', 'Regular Company URL', 
            'Company Revenue Min', 'Company Revenue Max', 'Company Location', 'City', 'Geographic Area', 'Country', 
            'Address', 'Postal Code', 'Decision Makers Search URL', 'Employee Search URL', 'Decision Makers Count'
        ])
        
        for i, company in enumerate(companies):
            if not active_package.unlimited_export and i >= 500:
                break
            writer.writerow([
                company.query, company.company_name, company.company_id, company.sales_navigator_company_url, 
                company.company_profile_picture, company.company_website, company.company_industry, 
                company.company_employee_count, company.company_employee_range, company.company_year_founded, 
                company.company_number, company.company_description, company.regular_company_url, 
                company.company_revenue_min, company.company_revenue_max, company.company_location, 
                company.city, company.geographicArea, company.country, company.address, company.postal_code, 
                company.decision_makers_search_url, company.employee_search_url, company.decision_makers_count
            ])
    
    return response