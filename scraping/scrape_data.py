import re
import time
import pickle
import logging
from selenium import webdriver
from django.utils import timezone
from users.models import UserProfile
from billing.models import Statement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from .models import ScrapingInfo, LinkedInProfile, LinkedInCompany
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException

# Start Helper Functions
def setup_driver(user_agent=None):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")  # Required for headless mode on some systems
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
    chrome_options.add_argument("--disable-software-rasterizer")  # Disable software rasterizer
    chrome_options.add_argument("--disable-extensions")  # Disable extensions for performance
    
    if user_agent:
        chrome_options.add_argument(f"user-agent={user_agent}")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(2048, 1536)
        return driver
    except:
        return None

def load_cookies(driver, li_at_value, scraping_id):
    scraping_info = ScrapingInfo.objects.get(pk=scraping_id)
    try:
        # Navigate to LinkedIn to set the domain context
        driver.get("https://www.linkedin.com")
        
        # Add the authentication cookie
        driver.add_cookie({'name': 'li_at', 'value': li_at_value, 'domain': '.linkedin.com'})
        driver.refresh()

        # Wait until the feed is loaded or timeout after 10 seconds
        WebDriverWait(driver, 10).until(EC.url_contains("feed"))

        scraping_info.authentication = 'successful'
        scraping_info.save()
        return True
    except (WebDriverException, pickle.UnpicklingError) as e:
        scraping_info.authentication = 'failed'
        scraping_info.save()
        driver.quit()  # Use quit to close the browser and end the WebDriver session
        return False

def scroll_down(search_results_container, driver, wait):
    search_results = search_results_container.find_elements(By.TAG_NAME, 'li')
    for result in search_results:
        wait.until(EC.element_to_be_clickable(result))
        driver.execute_script("arguments[0].scrollIntoView();", result)
        wait.until(EC.element_to_be_clickable(result))
        driver.execute_script("arguments[0].focus();", result)
        driver.execute_script("var event = new KeyboardEvent('keydown', {key: 'ArrowDown'}); arguments[0].dispatchEvent(event);", result)
    
    for result in search_results:
        wait.until(EC.element_to_be_clickable(result))
        driver.execute_script("arguments[0].scrollIntoView();", result)
        wait.until(EC.element_to_be_clickable(result))
        driver.execute_script("arguments[0].focus();", result)
        driver.execute_script("var event = new KeyboardEvent('keydown', {key: 'ArrowDown'}); arguments[0].dispatchEvent(event);", result)

def next_page(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button[aria-label="Next"]'))
        )
        next_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="Next"]')
        next_button_clicked = False
        for button in next_buttons:
            if not button.get_attribute("disabled") and "artdeco-button--disabled" not in button.get_attribute("class"):
                button.click()
                next_button_clicked = True
                return False

        if not next_button_clicked:
            print("No next button available or all buttons are disabled.")
            return True

    except (NoSuchElementException, TimeoutException) as e:
        print(f"An error occurred: {e}")
        return True

def open_new_tab(driver, url=None):
    # Open a new tab using JavaScript
    driver.execute_script("window.open('');")
    
    # Switch to the new tab
    driver.switch_to.window(driver.window_handles[-1])
    
    # Load the specified URL if provided
    if url:
        driver.get(url)

def close_current_tab(driver):
    # Close the current tab
    driver.close()
    
    # Switch back to the first tab (or another one if needed)
    if len(driver.window_handles) > 0:
        driver.switch_to.window(driver.window_handles[0])

def update_scraping_info(driver, scraping_info_id, status, active_package):
    driver.quit()
    try:
        scraping_info = ScrapingInfo.objects.get(id=scraping_info_id)
        end_time = timezone.now()
        duration = end_time - scraping_info.starting_time

        # Calculate hours, minutes, seconds
        total_seconds = int(duration.total_seconds())
        hours, minutes, seconds = total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60

        # Format the output
        formatted_duration = f"{hours}hr {minutes}min {seconds}sec"

        scraping_info.duration = formatted_duration
        scraping_info.status = status
        scraping_info.save()

        if active_package:
            active_package.execution_time_hours = timezone.timedelta(seconds=active_package.execution_time_hours.total_seconds() - duration.total_seconds())
            active_package.save()

        try:
            Statement.objects.create(
                user=UserProfile.objects.get(email=scraping_info.email),
                date=timezone.now(),
                order_id=scraping_info.scraping_id,
                details=f'Scraping duration for {scraping_info.scraping_name}',
                credit=formatted_duration
            )
        except Exception as e:
            print(f"An error occurred while creating the statement: {e}")

    except ScrapingInfo.DoesNotExist:
        logging.error(f"ScrapingInfo with id {scraping_info_id} does not exist.")
    except Exception as e:
        logging.error(f"An error occurred while updating scraping info: {e}")

def initialize_scraping(user_agent, li_at_value, scraping_info_id, request, active_package):
    scraping_info = ScrapingInfo.objects.get(pk=scraping_info_id)
    scraping_info.status = 'in_process'
    scraping_info.starting_time = timezone.now()
    scraping_info.scraping_name += f' ({request.user.total_scraping})'
    scraping_info.save()

    active_package.used_slots += int(scraping_info.slots.split(' ')[0])
    active_package.save()

    driver = setup_driver(user_agent)
    wait = WebDriverWait(driver, 15)
    
    logged_in = load_cookies(driver, li_at_value, scraping_info_id)
    request.user.total_scraping += 1    
    request.user.save()

    return driver, wait, logged_in
# End Helper Functions


# Start People + Normal
def extract_profile_normal_data(result, driver, wait):
    data = {}
    try:
        a_tag = result.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__title.ember-view').find_element(By.TAG_NAME, 'a')
        data['profile_url'] = a_tag.get_attribute('href')
        data['vmid'] = data['profile_url'].split(',', 1)[0].split('/lead/')[1]
        data['linkedIn_profile_url'] = 'https://www.linkedin.com/in/' + data['vmid']
        person_full_name = a_tag.text
        data['full_name'] = person_full_name
        data['first_name'], data['last_name'] = person_full_name.split(' ', 1)

        # Extract company data
        try:
            company_name_element = result.find_element(By.CLASS_NAME, 'ember-view.t-black--light.t-bold.inline-block')
            data['company_name'] = company_name_element.text
            company_sales_link = company_name_element.get_attribute('href')
            data['company_id'] = re.search(r"/company/(\d+)", company_sales_link).group(1)
            data['company_url'] = f"https://www.linkedin.com/sales/company/{data['company_id']}"
            data['regular_company_url'] = f"https://www.linkedin.com/company/{data['company_id']}"
        except:
            data['company_name'] = "None"
            data['company_id'] = "None"
            data['company_url'] = "None"
            data['regular_company_url'] = "None"

        data['connection_degree'] = "None"
        connection_degree_element = driver.find_element(By.CSS_SELECTOR, 'span.artdeco-entity-lockup__degree')
        if connection_degree_element:
            data['connection_degree'] = connection_degree_element.text.split('· ')[1]

        data['summary'] = "None"
        try:
            summary_element = result.find_element(By.TAG_NAME, 'dl').find_element(By.TAG_NAME, 'dd')
            summary_element.click()  # Click to reveal the summary if necessary
            time.sleep(2)  # Wait for the summary to load, adjust if needed
            data['summary'] = summary_element.text
            if data['summary'] != "None" and '..see less' in data['summary']:
                data['summary'] = data['summary'].replace('..see less', '').strip()
        except:
            data['summary'] = "None"

        data['duration_in_role'] = "0"
        data['duration_in_company'] = "0"
        try:
            duration_element = result.find_element(By.CSS_SELECTOR, '[data-anonymize="job-title"]')
            data['duration_in_role'] = duration_element.text.split('in role')[0]
            data['duration_in_company'] = duration_element.text.split('in role')[1].split('in company')[0]
        except:
            data['duration_in_role'] = "0"
            data['duration_in_company'] = "0"

        data['profile_image_url'] = "None"
        try:
            profile_image_element = result.find_element(By.TAG_NAME, 'img')
            data['profile_image_url'] = profile_image_element.get_attribute('src')
        except:
            data['profile_image_url'] = "None"

        data['prospect_position'] = "None"
        try:
            prospect_position_element = result.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle.ember-view.t-14').find_element(By.XPATH, ".//span[@data-anonymize='title']")
            data['prospect_position'] = prospect_position_element.text
        except:
            data['prospect_position'] = "None"

        data['prospect_is_premium'] = False
        try:
            prospect_is_premium_element = result.find_element(By.XPATH, ".//li-icon[@type='linkedin-premium-gold-icon']")
            data['prospect_is_premium'] = True if prospect_is_premium_element else False
        except:
            data['prospect_is_premium'] = False

        data['location'] = "None"
        try:
            location_element = result.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__caption.ember-view')
            data['location'] = location_element.text
        except:
            data['location'] = "None"

        data['company_location'] = "None"
        data['industry'] = "None"
        
        try:
            hover_element = result.find_element(By.CLASS_NAME, 'ember-view.t-black--light.t-bold.inline-block')
            actions = ActionChains(driver)
            time.sleep(1)
            actions.move_to_element(hover_element).perform()
            time.sleep(3)
            howercard = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'entity-hovercard-container.ember-view')))
            data['company_location'] = howercard.find_element(By.CSS_SELECTOR, '[data-anonymize="location"]').text
            data['industry'] = howercard.find_element(By.CSS_SELECTOR, '[data-anonymize="industry"]').text
            driver.find_element(By.TAG_NAME, 'ol').click()
            driver.execute_script("arguments[0].scrollIntoView();", result)
            driver.execute_script("arguments[0].focus();", result)
            driver.execute_script("var event = new KeyboardEvent('keydown', {key: 'ArrowDown'}); arguments[0].dispatchEvent(event);", result)
        except:
            data['company_location'] = "None"
            data['industry'] = "None"
        
        # Extract employees count
        data['employees_count'] = "None"
        try:
            employees_count_element = result.find_element(By.CSS_SELECTOR, '[data-anonymize="company-size"]')
            data['employees_count'] = employees_count_element.text
        except:
            data['employees_count'] = "None"

        # Check if the company is hiring
        data['is_hiring'] = False
        try:
            is_hiring_element = result.find_element(By.CSS_SELECTOR, '[data-control-name="search_spotlight_hiring_on_linkedin"]')
            data['is_hiring'] = True if is_hiring_element else False
        except:
            data['is_hiring'] = False

    except Exception as e:
        logging.error("Error extracting data from result: %s", e)

    return data

def people_normal_scrape_and_save_data(url, li_at_value, scraping_info_id, user_agent, request, active_package):
    driver, wait, logged_in = initialize_scraping(user_agent, li_at_value, scraping_info_id, request, active_package)

    if logged_in:
        driver.get(url)
        try:
            try:
                collapse_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Collapse filter panel"]')))
                collapse_button.click()
            except Exception as e:
                logging.error("Error collapsing filter panel: %s", e)
            while True:
                search_results_container = wait.until(EC.presence_of_element_located((By.ID, 'search-results-container'))).find_element(By.XPATH, 'div[2]/ol')
                scroll_down(search_results_container, driver, wait)


                search_results = search_results_container.find_elements(By.TAG_NAME, 'li')
                for result in search_results:
                    try:
                        found = result.find_element(By.CSS_SELECTOR, '[data-view-name="search-results-entity"]')
                        found = True
                    except:
                        found =  False
                    
                    if found:
                        data = extract_profile_normal_data(result, driver, wait)
                        if data:
                            LinkedInProfile.objects.create(
                                full_name=data['full_name'], first_name=data['first_name'], last_name=data['last_name'], 
                                connection_degree=data['connection_degree'], summary=data['summary'], query=url, location=data['location'], 
                                is_premium=data['prospect_is_premium'], sales_navigator_url=data['profile_url'], 
                                linkedin_url=data['linkedIn_profile_url'], profile_picture=data['profile_image_url'], 
                                job_title=data['prospect_position'], scraping_id = ScrapingInfo.objects.get(id=scraping_info_id).scraping_id
                            )
                            
                            LinkedInCompany.objects.create(
                                company_name=data['company_name'],  company_id=data['company_id'], sales_navigator_company_url=data['company_url'], 
                                regular_company_url=data['regular_company_url'], vmid=data['vmid'], company_location=data['company_location'], 
                                company_industry=data['industry'], scraping_id = ScrapingInfo.objects.get(id=scraping_info_id).scraping_id
                                # duration_in_role=data['duration_in_role'], 
                                # duration_in_company=data['duration_in_company'], 
                            )

                if next_page(driver):
                    break           
        except:
            update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)

        update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)
    else:
        update_scraping_info(driver, scraping_info_id, status='failed', active_package=active_package)
# End People + Normal


# Start Company + Normal
def extract_company_normal_data(result, driver, wait):
    data = {}
    try:
        # Extract company URL and ID
        a_tag = result.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__title.ember-view').find_element(By.TAG_NAME, 'a')
        data['company_url'] = a_tag.get_attribute('href').split('?', 1)[0]
        data['company_id'] = data['company_url'].split('/company/')[1]
        data['regular_company_url'] = f"https://www.linkedin.com/company/{data['company_id']}"

        # Extract company name
        data['company_name'] = a_tag.text

        # Extract company description
        data['description'] = "None"
        try:
            description_element = result.find_element(By.TAG_NAME, 'dl').find_element(By.TAG_NAME, 'dd')
            description_element.click()  # Click to reveal the description if necessary
            data['description'] = description_element.text
            if data['description'] != "None" and 'Show less' in data['description']:
                data['description'] = data['description'].replace('Show less', '').strip()
        except:
            data['description'] = "None"

        # Extract company logo URL
        data['logo_url'] = "None"
        try:
            logo_element = result.find_element(By.TAG_NAME, 'img')
            data['logo_url'] = logo_element.get_attribute('src')
        except:
            data['logo_url'] = "None"

        # Extract company industry
        data['industry'] = "None"
        try:
            industry_element = result.find_element(By.CSS_SELECTOR, '[data-anonymize="industry"]')
            data['industry'] = industry_element.text
        except:
            data['industry'] = "None"

        # Extract company employees count
        data['employees_count'] = "None"
        try:
            employees_count_element = result.find_element(By.CSS_SELECTOR, '[data-anonymize="company-size"]')
            data['employees_count'] = employees_count_element.text
        except:
            data['employees_count'] = "None"

        # Check if the company is hiring
        data['is_hiring'] = False
        try:
            is_hiring_element = result.find_element(By.CSS_SELECTOR, '[data-control-name="search_spotlight_hiring_on_linkedin"]')
            data['is_hiring'] = True if is_hiring_element else False
        except:
            data['is_hiring'] = False

    except Exception as e:
        pass

    return data

def company_normal_scrape_and_save_data(url, li_at_value, scraping_info_id, user_agent, request, active_package):
    driver, wait, logged_in = initialize_scraping(user_agent, li_at_value, scraping_info_id, request, active_package)

    if logged_in:
        driver.get(url)
        try:
            while True:
                search_results_container = wait.until(EC.presence_of_element_located((By.ID, 'search-results-container'))).find_element(By.XPATH, 'div[2]/ol')
                scroll_down(search_results_container, driver, wait)

                search_results = search_results_container.find_elements(By.TAG_NAME, 'li')
            
                for result in search_results:
                    try:
                        found = result.find_element(By.CSS_SELECTOR, '[data-view-name="search-results-entity"]')
                        found = True
                    except:
                        found =  False
                    
                    if found:
                        data = extract_company_normal_data(result, driver, wait)
                        if data:
                            LinkedInCompany.objects.create(
                                sales_navigator_company_url=data['company_url'], company_name=data['company_name'], company_description=data['description'],
                                company_id=data['company_id'], regular_company_url=data['regular_company_url'], company_industry=data['industry'], scraping_id = ScrapingInfo.objects.get(id=scraping_info_id).scraping_id,
                                company_employee_count=data['employees_count'], company_profile_picture=data['logo_url'], is_hiring=data['is_hiring'], query=url
                            )

                if next_page(driver):
                    break

        except:
            update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)

        update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)  
    else:
        update_scraping_info(driver, scraping_info_id, status='failed', active_package=active_package)
# End Company + Normal


# Start Company + Deep
def get_company_details(driver, wait):
    try:
        content_element = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "artdeco-card.org-page-details-module__card-spacing.artdeco-card.org-about-module__margin-bottom"))
        )
        data2 = content_element.text

        overview_pattern = r'Overview\n(.*?)\n(?=Website|Phone|Industry|Company size|$)'
        match = re.search(overview_pattern, data2, re.DOTALL)
        overview = match.group(1).strip() if match else "None"

        patterns = {
            "company_employee_range": r"Company size\n(.*?) employees",
            "company_year_founded": r"Founded\n(\d+)",
            "phone": r"Phone\n(.*?)\n"
        }
        
        def extract_info(data, patterns):
            extracted_info = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, data, re.DOTALL)
                if match:
                    extracted_info[key] = match.group(1).strip()
                else:
                    extracted_info[key] = "None"  # Or handle the missing information as needed
            return extracted_info

        # Use the function
        info = extract_info(data2, patterns)

        data2 = info

        # data2 = {key: re.search(pattern, data2).group(1).strip() if re.search(pattern, data2) else "None" for key, pattern in patterns.items()}

        # Constructing the final list with the extracted data2, including website, city, and state
        data2["overview"] = overview
        data2["linkedin_company_url"] = driver.current_url.split('/about')[0]
        
        return data2
    except Exception as e:
        print(f"Linkdin Data Nhi hai {e}", driver.current_url.split('/about')[0])
        data2 = {
            "company_employee_range": "None",
            "company_year_founded": "None",
            "phone": "None",
            "overview": "None",
            "linkedin_company_url": driver.current_url.split('/about')[0]
        }
        return data2

def extract_company_deep_data(result, driver, wait):
    data = {}
    try:
        # Extract company URL and ID
        a_tag = result.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__title.ember-view').find_element(By.TAG_NAME, 'a')
        data['company_url'] = a_tag.get_attribute('href').split('?', 1)[0]
        data['company_id'] = data['company_url'].split('/company/')[1]
        data['regular_company_url'] = f"https://www.linkedin.com/company/{data['company_id']}"

        # Extract company name
        data['company_name'] = a_tag.text

        # Extract company logo URL
        data['logo_url'] = "None"
        try:
            logo_element = result.find_element(By.TAG_NAME, 'img')
            data['logo_url'] = logo_element.get_attribute('src')
        except:
            data['logo_url'] = "None"

        # Extract company industry
        data['industry'] = "None"
        try:
            industry_element = result.find_element(By.CSS_SELECTOR, '[data-anonymize="industry"]')
            data['industry'] = industry_element.text
        except:
            data['industry'] = "None"

        # Extract company employees count
        data['employees_count'] = "None"
        try:
            employees_count_element = result.find_element(By.CSS_SELECTOR, '[data-anonymize="company-size"]')
            data['employees_count'] = employees_count_element.text
        except:
            data['employees_count'] = "None"

    except Exception as e:
        pass

    return data

def extract_company_deep_all_data(company_data, driver, wait):
    additional_data = {}

    if company_data.get('regular_company_url') != "None" and company_data.get('regular_company_url'):
        regular_company_url = company_data.pop('regular_company_url') + '/about/'

        # Open the company details page
        open_new_tab(driver=driver, url=regular_company_url)
        company_details = get_company_details(driver, wait)
        additional_data.update(company_details)
        close_current_tab(driver)

    else:
        additional_data.update({
            "company_employee_range": "None",
            "company_year_founded": "None",
            "phone": "None",
            "overview": "None",
            "linkedin_company_url": "None"
        })

    if company_data.get('company_url') != "None" and company_data.get('company_url'):
        open_new_tab(driver=driver, url=company_data['company_url'])

        min_revenue = "Not available"
        max_revenue = "Not available"
        location = "None"
        city = "None"
        geographic_area = "None"
        country = "None"
        website = "Not available"
        
        try:
            revenue_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-anonymize="revenue"]'))
            )
            revenue = revenue_element.text.split('-')
            if len(revenue) == 2:
                min_revenue = revenue[0].strip()
                max_revenue = revenue[1].strip()
        except Exception as e:
            print(f"Error extracting revenue: {e}")
        
        try:
            location_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-anonymize="location"]'))
            )
            location = location_element.text
            if location:
                parts = location.split(',')
                if len(parts) >= 3:
                    city, geographic_area, country = [part.strip() for part in parts[:3]]
                else:
                    city = geographic_area = country = "None"
                    location = "None"
        except Exception as e:
            print(f"Error extracting location: {e}")

        try:
            website_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-control-name="visit_company_website"]'))
            )
            website = website_element.get_attribute('href')
        except:
            website = "Not available"
        
        additional_data.update({
            "min_revenue": min_revenue,
            "max_revenue": max_revenue,
            "location": location,
            "city": city,
            "geographic_area": geographic_area,
            "country": country,
            "website": website
        })
        close_current_tab(driver)
    else:
        additional_data.update({
            "min_revenue": "None",
            "max_revenue": "None",
            "location": "None",
            "city": "None",
            "geographic_area": "None",
            "country": "None",
            "website": "Not available"
        })

    return additional_data

def company_deep_scrape_and_save_data(url, li_at_value, scraping_info_id, user_agent, request, active_package):
    driver, wait, logged_in = initialize_scraping(user_agent, li_at_value, scraping_info_id, request, active_package)

    if logged_in:
        driver.get(url)
        try:
            while True:
                search_results_container = wait.until(EC.presence_of_element_located((By.ID, 'search-results-container'))).find_element(By.XPATH, 'div[2]/ol')
                scroll_down(search_results_container, driver, wait)

                search_results = search_results_container.find_elements(By.TAG_NAME, 'li')
                for result in search_results:
                    try:
                        found = result.find_element(By.CSS_SELECTOR, '[data-view-name="search-results-entity"]')
                        found = True
                    except:
                        found =  False
                    
                    if found:
                        data1 = extract_company_deep_data(result, driver, wait)
                        if data1:
                            additional_data = extract_company_deep_all_data(data1, driver, wait)
                            data1.update(additional_data)

                            # Create a new LinkedInCompanyDeep instance
                            LinkedInCompany.objects.create(
                                query=url,  # Assuming query is the URL you're scraping
                                company_name=data1['company_name'],
                                company_id=data1['company_id'],
                                sales_navigator_company_url=data1['company_url'],
                                company_profile_picture=data1['logo_url'],
                                company_website=data1['website'],
                                company_industry=data1['industry'],
                                company_employee_count=data1['employees_count'],
                                company_employee_range=data1['company_employee_range'],
                                company_year_founded=data1['company_year_founded'],
                                company_number=data1['phone'],
                                company_description=data1['overview'],
                                regular_company_url=data1['linkedin_company_url'],
                                company_revenue_min=data1['min_revenue'],
                                company_revenue_max=data1['max_revenue'],
                                company_location=data1['location'],
                                city=data1['city'],
                                geographicArea=data1['geographic_area'],
                                country=data1['country'],
                                scraping_id = ScrapingInfo.objects.get(id=scraping_info_id).scraping_id
                            )

                if next_page(driver):
                    break

        except:
            update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)

        update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)
    else:
        update_scraping_info(driver, scraping_info_id, status='failed', active_package=active_package)
# End Company + Deep


# Start People + Deep
class LinkedInScraper:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def extract_duration(self, duration_str):
        years_pattern = re.search(r'(\d+)\s*yrs?', duration_str)
        months_pattern = re.search(r'(\d+)\s*mos?', duration_str)
        years = int(years_pattern.group(1)) if years_pattern else 0
        months = int(months_pattern.group(1)) if months_pattern else 0
        return [years, months]
    
    def get_headline(self):
        try:
            headline_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-anonymize="headline"]')))
            return headline_element.text
        except:
            return "None"

    def get_connections(self):
        try:
            connections_element = self.driver.find_element(By.CLASS_NAME, '_header_sqh8tm')
            match = re.search(r'(\d+\+?)\s+connections', connections_element.text)
            return match.group(0) if match else 0
        except:
            return 0

    def click_button_and_get_profile_link(self):
        try:
            button_element = self.driver.find_element(By.CLASS_NAME, '_overflow-menu--trigger_1xow7n')
            self.driver.execute_script("arguments[0].click();", button_element)
            profile_link = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a.ember-view._item_1xnv7i[href*="linkedin.com"]'))
            ).get_attribute('href')
            self.driver.find_element(By.CSS_SELECTOR, '[data-sn-view-name="lead-current-role"]').click()
            return profile_link
        except (NoSuchElementException, ElementClickInterceptedException, TimeoutException):
            return "None"

    def get_about_section(self):
        try:
            self.driver.find_element(By.CLASS_NAME, '_content-width_1dtbsb._bodyText_1e5nen._default_1i6ulk._sizeSmall_1e5nen').click()
        except:
            pass

        try:
            about_section = self.driver.find_element(By.CSS_SELECTOR, '[data-anonymize="person-blurb"]')
            prospect_summary_element = about_section.text
            return prospect_summary_element
        except:
            return "None"

    def prospect_current_positions(self):
        try:
            expriance_section = self.driver.find_element(By.ID, 'experience-section')
            present_elements = expriance_section.find_elements(By.CLASS_NAME, '_bodyText_1e5nen._default_1i6ulk._sizeXSmall_1e5nen._lowEmphasis_1i6ulk')
            return sum(1 for present in present_elements if 'present' in present.text.lower())
        except:
            return 0

    def years_and_months_in_position(self):
        try:
            expriance_section = self.wait.until(EC.presence_of_element_located((By.ID, 'experience-section')))
            present_elements = expriance_section.find_element(By.CSS_SELECTOR, 'p._bodyText_1e5nen._default_1i6ulk._sizeXSmall_1e5nen._lowEmphasis_1i6ulk')
            return self.extract_duration(present_elements.text)
        except:
            return [0, 0]
        
    def years_and_months_in_company(self):
        try:
            expriance_section = self.wait.until(EC.presence_of_element_located((By.ID, 'experience-section')))
            present_elements = expriance_section.find_element(By.TAG_NAME, 'ul').find_element(By.TAG_NAME, 'li').find_elements(By.TAG_NAME, 'p')
            return self.extract_duration(present_elements[1].text)
        except:
            return [0, 0]

    def get_company_details(self):
        extracted_data = {
            "company_profile_picture": "None",
            "company_website": "None",
            "company_domain": "None",
            "overview": "None",
            "industry": "None",
            "specialties": "None",
            "company_employee_count": "None",
            "company_employee_range": "None",
            "company_location": "None",
            "company_year_founded": "None",
            "phone": "None"
        }

        try:
            # Extract the company profile picture
            try:
                profile_picture_element = self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'org-top-card-primary-content__logo-container')
                )).find_element(By.TAG_NAME, 'img')
                # profile_picture_element = self.driver.find_element(By.CLASS_NAME, 'org-top-card-primary-content__logo-container')
                extracted_data["company_profile_picture"] = profile_picture_element.get_attribute('src')
            except Exception as e:
                print(f"Error extracting profile picture: {e}")

            # Extract the company website and domain
            try:
                website_element = self.driver.find_element(By.TAG_NAME, 'dl').find_element(By.TAG_NAME, 'a')
                extracted_data["company_website"] = website_element.get_attribute('href')
                if extracted_data["company_website"] != "None":
                    extracted_data["company_domain"] = extracted_data["company_website"].split('//', 1)[1]
            except Exception as e:
                print(f"Error extracting website: {e}")

            # Extract the company overview and other details
            data = self.driver.find_element(By.CLASS_NAME, "org-grid__content-height-enforcer").text
            overview_pattern = r'Overview\n(.*?)\n(?=Website|Phone|Verified page|Industry|Company size|$)'
            overview_match = re.search(overview_pattern, data, re.DOTALL)
            extracted_data["overview"] = overview_match.group(1).strip() if overview_match else "None"

            patterns = {
                "phone": r"Phone\n(.*?)\n",
                "industry": r"Industry\n(.*?)\n",
                "specialties": r"Specialties\n(.*?)\n",
                "company_employee_count": r"(\d+,?\d*) associated members",
                "company_employee_range": r"Company size\n(.*?) employees",
                "company_location": r"Headquarters\n(.*?)\n",
                "company_year_founded": r"Founded\n(\d+)",
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, data)
                extracted_data[key] = match.group(1).strip() if match else "None"

        except Exception as e:
            pass

        return extracted_data

def extract_profile_deep_data(result, driver, wait):
    data = {}
    try:
        a_tag = result.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__title.ember-view').find_element(By.TAG_NAME, 'a')
        data['prospect_sales_navigator_url'] = a_tag.get_attribute('href')
        person_full_name = a_tag.text
        data['full_name'] = person_full_name
        data['first_name'], data['last_name'] = person_full_name.split(' ', 1)

        # Extract company data
        try:
            company_name_element = result.find_element(By.CLASS_NAME, 'ember-view.t-black--light.t-bold.inline-block')
            data['company_name'] = company_name_element.text
            company_sales_link = company_name_element.get_attribute('href')
            data['company_id'] = re.search(r"/company/(\d+)", company_sales_link).group(1)
            data['company_url'] = f"https://www.linkedin.com/sales/company/{data['company_id']}"
            data['regular_company_url'] = f"https://www.linkedin.com/company/{data['company_id']}"
        except:
            data['company_name'] = "None"
            data['company_id'] = "None"
            data['company_url'] = "None"
            data['regular_company_url'] = "None"

        data['profile_image_url'] = "None"
        try:
            profile_image_element = result.find_element(By.TAG_NAME, 'img')
            data['profile_image_url'] = profile_image_element.get_attribute('src')
        except:
            data['profile_image_url'] = "None"

        data['prospect_position'] = "None"
        try:
            prospect_position_element = result.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle.ember-view.t-14').find_element(By.XPATH, ".//span[@data-anonymize='title']")
            data['prospect_position'] = prospect_position_element.text
        except:
            data['prospect_position'] = "None"

        data['prospect_is_premium'] = False
        try:
            prospect_is_premium_element = result.find_element(By.XPATH, ".//li-icon[@type='linkedin-premium-gold-icon']")
            data['prospect_is_premium'] = True if prospect_is_premium_element else False
        except:
            data['prospect_is_premium'] = False

        data['location'] = "None"
        try:
            location_element = result.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__caption.ember-view')
            data['location'] = location_element.text
        except:
            data['location'] = "None"
    except Exception as e:
        logging.error("Error extracting data from result: %s", e)
    return data

def scrape_profile_data(driver):
    # Initialize the LinkedInScraper with the Selenium driver
    scraper = LinkedInScraper(driver)
    
    # Extract data from the LinkedIn profile
    extract_data = {}
    extract_data['prospect_headline'] = scraper.get_headline()
    extract_data['prospect_connections'] = scraper.get_connections()
    
    # Get the profile link and other sections
    extract_data['prospect_linkedin_url'] = scraper.click_button_and_get_profile_link()
    extract_data['prospect_summary'] = scraper.get_about_section()
    
    # Extract years and months in company
    years_and_months_in_company = scraper.years_and_months_in_company()
    extract_data['years_in_company'] = years_and_months_in_company[0]
    extract_data['months_in_company'] = years_and_months_in_company[1]
    
    # Extract years and months in position
    years_and_months_in_position = scraper.years_and_months_in_position()
    extract_data['years_in_position'] = years_and_months_in_position[0]  # Fixed: Changed from years_and_months_in_company to years_and_months_in_position
    extract_data['months_in_position'] = years_and_months_in_position[1]  # Fixed: Changed from years_and_months_in_company to years_and_months_in_position
    
    # Extract current positions
    extract_data['prospect_current_positions'] = scraper.prospect_current_positions()
    
    return extract_data

def scrape_company_data(driver):
    # Initialize the LinkedInScraper with the Selenium driver
    scraper = LinkedInScraper(driver)

    return scraper.get_company_details()

def profile_deep_scrape_and_save_data(url, li_at_value, scraping_info_id, user_agent, request, active_package):
    driver, wait, logged_in = initialize_scraping(user_agent, li_at_value, scraping_info_id, request, active_package)
    
    if logged_in:
        driver.get(url)
        try:
            try:
                collapse_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Collapse filter panel"]')))
                collapse_button.click()
            except Exception as e:
                logging.error("Error collapsing filter panel: %s", e)
            while True:
                search_results_container = wait.until(EC.presence_of_element_located((By.ID, 'search-results-container'))).find_element(By.XPATH, 'div[2]/ol')
                scroll_down(search_results_container, driver, wait)

                search_results = search_results_container.find_elements(By.TAG_NAME, 'li')
                for result in search_results:
                    try:
                        found = result.find_element(By.CSS_SELECTOR, '[data-view-name="search-results-entity"]')
                        found = True
                    except:
                        found =  False
                    
                    if found:
                        data = extract_profile_deep_data(result, driver, wait)
                        if data:
                            open_new_tab(driver, data['prospect_sales_navigator_url'])
                            profile_data = scrape_profile_data(driver)
                            close_current_tab(driver)
                            data.update(profile_data)

                            if data['regular_company_url'] != "None":
                                open_new_tab(driver, data['regular_company_url'] + '/about/')
                                company_data = scrape_company_data(driver)
                                close_current_tab(driver)
                                data.update(company_data)
                            else:
                                company_data = {
                                    "company_profile_picture": "None",
                                    "company_website": "None",
                                    "company_domain": "None",
                                    "overview": "None",
                                    "industry": "None",
                                    "specialties": "None",
                                    "company_employee_count": "None",
                                    "company_employee_range": "None",
                                    "company_location": "None",
                                    "company_year_founded": "None",
                                    "phone": "None"
                                }
                                data.update(company_data)

                            LinkedInProfile.objects.create(
                                query=url, sales_navigator_url=data['prospect_sales_navigator_url'], full_name=data['full_name'], first_name=data['first_name'], last_name=data['last_name'],       
                                profile_picture=data['profile_image_url'], job_title=data['prospect_position'], is_premium=data['prospect_is_premium'], location=data['location'],
                                headline=data['prospect_headline'], connections=data['prospect_connections'], linkedin_url=data['prospect_linkedin_url'], summary=data['prospect_summary'], 
                                years_in_company=data['years_in_company'], months_in_company=data['months_in_company'], years_in_position=data['years_in_position'], months_in_position=data['months_in_position'],
                                current_positions=data['prospect_current_positions'], scraping_id = ScrapingInfo.objects.get(id=scraping_info_id).scraping_id
                            )

                            LinkedInCompany.objects.create(
                                company_name=data['company_name'], scraping_id = ScrapingInfo.objects.get(id=scraping_info_id).scraping_id, query=url,
                                company_linkedin_id_url=data['company_url'], company_website=data['company_website'], company_domain=data['company_domain'], 
                                company_industry=data['industry'], company_specialties=data['specialties'], company_employee_count=data['company_employee_count'], 
                                company_employee_range=data['company_employee_range'], company_location=data['company_location'], company_year_founded=data['company_year_founded'], 
                                company_description=data['overview'],company_profile_picture=data['company_profile_picture'], company_number=data['phone'],   
                            )

                if next_page(driver):
                    break

        except:
            update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)

        update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)
    else:
        update_scraping_info(driver, scraping_info_id, status='failed', active_package=active_package)
# End People + Deep


# Start PDeepCSV
def profile_deep_scrape_and_save_data_csv(url, li_at_value, scraping_info_id, user_agent, request, active_package):
    pass
# End PDeepCSV

# Start CDeepCSV
def company_deep_scrape_and_save_data_csv(url, li_at_value, scraping_info_id, user_agent, request, active_package):
    pass
# End CDeepCSV
