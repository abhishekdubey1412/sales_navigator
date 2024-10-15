import re
import csv
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
    chrome_options.add_argument("--disable-extensions")  # Disable extensions for performance
    chrome_options.add_argument("--disable-popup-blocking")  # Disable popup blocking
    chrome_options.add_argument("--disable-notifications")  # Disable notifications
    chrome_options.add_argument("--disable-infobars")  # Disable infobars
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Disable automation controlled
    chrome_options.add_argument("--disable-web-security")  # Disable web security
    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")  # Disable isolate origins and site per process

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

def extract_duration(duration_str):
    years_pattern = re.search(r'(\d+)\s*yrs?', duration_str)
    months_pattern = re.search(r'(\d+)\s*mos?', duration_str)
    years = int(years_pattern.group(1)) if years_pattern else 0
    months = int(months_pattern.group(1)) if months_pattern else 0
    return [years, months]
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
def extract_company_deep_data(driver, wait, is_csv=False):
    def safe_find_element_by_css_selector(selector):
        try:
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))).text
        except Exception as e:
            print(f"Error finding element by CSS selector {selector}: {e}")
            return "None"

    company_name = safe_find_element_by_css_selector('[data-anonymize="company-name"]')
    industry = safe_find_element_by_css_selector('[data-anonymize="industry"]')

    if is_csv:  
        employee_count_text = safe_find_element_by_css_selector('[data-anonymize="company-size"]')
        employee_count = employee_count_text.split('on')[0] if employee_count_text != "None" else "None"
    
    location = safe_find_element_by_css_selector('[data-anonymize="location"]')
    
    try:
        country = location.split(', ')[-1] if ', ' in location else "None"
    except Exception as e:
        print(f"Error extracting country: {e}")
        country = "None"
    
    try:
        geographic_area = location.split(', ')[1] if ', ' in location else "None"
    except Exception as e:
        print(f"Error extracting geographic area: {e}")
        geographic_area = "None"
    
    try:
        city = location.split(', ')[0] if ', ' in location else "None"
    except Exception as e:
        print(f"Error extracting city: {e}")
        city = "None"
    
    try:
        company_id = driver.current_url.split('/company/')[1].split('?')[0] if '/company/' in driver.current_url else "None"
    except Exception as e:
        print(f"Error extracting company ID: {e}")
        company_id = "None"

    try:
        sales_navigator_company_url = driver.current_url.split('?')[0] if '?' in driver.current_url else driver.current_url
    except Exception as e:
        print(f"Error extracting sales navigator company URL: {e}")
        sales_navigator_company_url = driver.current_url

    try:
        website_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-control-name="visit_company_website"]')))
        website = website_element.get_attribute('href') if website_element else "None"
    except Exception as e:
        print(f"Error extracting website: {e}")
        website = "None"

    try:
        domain = website.split('//')[1] if '//' in website else "None"
    except Exception as e:
        print(f"Error extracting domain: {e}")
        domain = "None"

    try:
        logo_url = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-anonymize="company-logo"]'))).get_attribute('src')
    except Exception as e:
        print(f"Error extracting logo URL: {e}")
        logo_url = "None"

    try:
        revenue = safe_find_element_by_css_selector('[data-anonymize="revenue"]')
    except Exception as e:
        print(f"Error extracting revenue: {e}")
        revenue = "None"
    
    if '$1B+' in revenue:
        min_revenue = "None"
        max_revenue = "None"
    else:
        min_revenue = revenue.split('-')[0].strip() if '-' in revenue else "None"
        max_revenue = revenue.split('-')[1].strip().split(' ')[0] if '-' in revenue else "None"

    try:
        more_options_button = driver.find_element(By.CSS_SELECTOR, '[aria-label="More options"]')
        more_options_button.click()
        linkedin_company_url = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#hue-web-menu-outlet div:nth-child(2) ul li:nth-child(1)'))
        ).get_attribute('href')
    except (NoSuchElementException, ElementClickInterceptedException, TimeoutException) as e:
        print(f"Error finding LinkedIn company URL: {e}")
        linkedin_company_url = "None"

    try:
        linkedin_company_url_button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#hue-web-menu-outlet div:nth-child(2) ul li:nth-child(3)'))
        )
        linkedin_company_url_button.click()
    except (NoSuchElementException, ElementClickInterceptedException, TimeoutException) as e:
        print(f"Error clicking LinkedIn company URL button: {e}")
        linkedin_company_url_button = None

    try:
        linkedin_company_url_element = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[7]/div/div')))
        description = linkedin_company_url_element.find_element(By.CSS_SELECTOR, '[data-anonymize="company-blurb"]').text
    except (NoSuchElementException, ElementClickInterceptedException, TimeoutException) as e:
        print(f"Error finding company description: {e}")
        description = "None"

    try:
        headquarters = linkedin_company_url_element.find_element(By.CSS_SELECTOR, '[data-anonymize="address"]').text
    except (NoSuchElementException, ElementClickInterceptedException, TimeoutException) as e:
        print(f"Error finding company headquarters: {e}")
        headquarters = "None"
    
    try:
        postal_code = re.search(r'\b\d{5}(?:-\d{4})?\b', headquarters)
        postal_code = postal_code.group() if postal_code else "None"
    except Exception as e:
        print(f"Error finding postal code: {e}")
        postal_code = "None"

    try:
        address = headquarters.split(city)[0].strip() if city in headquarters else "None"
    except Exception as e:
        print(f"Error finding address: {e}")
        address = "None"

    try:
        linkedin_company_details = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[7]/div/div/div[2]/div')))
    except Exception as e:
        print(f"Error finding LinkedIn company details: {e}")
        linkedin_company_details = None
        
    if linkedin_company_details:
        try:
            company_type_element = re.search(r'Type\n(.*?)\n', linkedin_company_details.text)
            company_type = company_type_element.group(1).strip() if company_type_element else "None"
        except Exception as e:
            print(f"Error finding company type: {e}")
            company_type = "None"

        try:
            founded_year_element = re.search(r'Founded\n(\d+)', linkedin_company_details.text)
            founded_year = founded_year_element.group(1).strip() if founded_year_element else "None"
        except Exception as e:
            print(f"Error finding company founded year: {e}")
            founded_year = "None"

        try:
            specialties_element = re.search(r'Specialties\n(.*?)\n', linkedin_company_details.text, re.DOTALL)
            specialties = specialties_element.group(1).strip() if specialties_element else "None"
        except Exception as e:
            print(f"Error finding company specialties: {e}")
            specialties = "None"

        try:
            phone_element = re.search(r'Phone\n(.*?)\n', linkedin_company_details.text)
            phone = phone_element.group(1).strip() if phone_element else "None"
        except Exception as e:
            print(f"Error finding company phone: {e}")
            phone = "None"
    else:
        company_type = "None"
        founded_year = "None"
        specialties = "None"
        phone = "None"

    try:
        dismiss_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Dismiss"]')))
        dismiss_button.click()
    except Exception as e:
        print(f"Error clicking dismiss button: {e}")
    
    if is_csv:
        try:
            all_employees_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='account']//a[contains(@aria-label, 'See all') and contains(@aria-label, 'employees on search results page')]")))
            employee_search_url = all_employees_element.get_attribute('href')
        except Exception as e:
            print(f"Error finding all employees link: {e}")
            employee_search_url = "None"

    try:
        decision_makers_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='account']//a[contains(@aria-label, 'See all') and contains(@aria-label, 'decision makers on search results page')]")))
        decision_makers_text = decision_makers_element.text
        decision_makers_search_url = decision_makers_element.get_attribute('href')
    except Exception as e:
        print(f"Error finding decision makers link: {e}")
        decision_makers_text = "None"
        decision_makers_search_url = "None"

    # Extract the count from the text
    try:
        decision_makers_count = re.search(r'\((\d+)\)', decision_makers_text).group(1)
    except Exception as e:
        print(f"Error extracting decision makers count: {e}")
        decision_makers_count = "None"

    employee_count_range = "None"

    if is_csv:
        return {
        'company_name': company_name, 'description': description, 'industry': industry,
        'employee_count': employee_count, 'location': location, 'country': country, 
        'geographic_area': geographic_area, 'city': city, 'postal_code': postal_code, 
        'address': address, 'headquarters': headquarters, 'company_id': company_id,
        'linkedin_company_url': linkedin_company_url, 'sales_navigator_company_url': sales_navigator_company_url, 
        'website': website, 'employee_count_range': employee_count_range, 'domain': domain, 
        'decision_makers_search_url': decision_makers_search_url, 'employee_search_url': employee_search_url,
        'decision_makers_count': decision_makers_count, 'logo_url': logo_url, 'founded_year': founded_year, 
        'company_type': company_type, 'specialties': specialties, 'min_revenue': min_revenue, 'max_revenue': max_revenue, 
        'phone': phone
        }

    return {
        'company_name': company_name, 'description': description, 'industry': industry,
        'location': location, 'country': country, 'geographic_area': geographic_area, 'city': city,
        'postal_code': postal_code, 'address': address, 'headquarters': headquarters, 'company_id': company_id,
        'linkedin_company_url': linkedin_company_url, 'sales_navigator_company_url': sales_navigator_company_url, 'website': website,
        'employee_count_range': employee_count_range, 'domain': domain, 'decision_makers_search_url': decision_makers_search_url,
        'decision_makers_count': decision_makers_count, 'logo_url': logo_url, 'founded_year': founded_year, 'company_type': company_type,
        'specialties': specialties, 'min_revenue': min_revenue, 'max_revenue': max_revenue, 'phone': phone
    }

def company_deep_scrape_and_save_data(url, li_at_value, scraping_info_id, user_agent, request, active_package):
    driver, wait, logged_in = initialize_scraping(user_agent, li_at_value, scraping_info_id, request, active_package)

    if logged_in:
        driver.get(url)
        try:
            while True:
                search_results_container = wait.until(EC.presence_of_element_located((By.ID, 'search-results-container'))).find_element(By.XPATH, 'div[2]/ol')
                scroll_down(search_results_container, driver, wait)

                search_results = search_results_container.find_elements(By.TAG_NAME, 'li')
                found_elements = [result for result in search_results if result.find_elements(By.CSS_SELECTOR, '[data-view-name="search-results-entity"]')]
                for result in found_elements:
                    regular_company_url = result.find_element(By.CSS_SELECTOR, '[data-view-name="search-results-account-name"]').get_attribute('href')
                    employee_count_element = result.find_element(By.CSS_SELECTOR, '[data-anonymize="company-size"]')
                    employee_count = employee_count_element.text
                    employee_search_url = employee_count_element.get_attribute('href')


                    # Open the company details page
                    open_new_tab(driver=driver, url=regular_company_url)
                    data1 = extract_company_deep_data(driver, wait)
                    close_current_tab(driver)

                    if data1:
                        # Create a new LinkedInCompanyDeep instance
                        LinkedInCompany.objects.create(
                            query=url,  # Assuming query is the URL you're scraping
                            company_name=data1['company_name'],
                            company_description=data1['description'],
                            company_industry=data1['industry'],
                            company_employee_count=employee_count,
                            company_location=data1['location'],
                            country=data1['country'],
                            geographicArea=data1['geographic_area'],
                            city=data1['city'],
                            postal_code=data1['postal_code'],
                            address=data1['address'],
                            company_headquarters=data1['headquarters'],
                            company_id=data1['company_id'],
                            regular_company_url=data1['linkedin_company_url'],
                            sales_navigator_company_url=data1['sales_navigator_company_url'],
                            company_website=data1['website'],
                            company_domain=data1['domain'],
                            decision_makers_search_url=data1['decision_makers_search_url'],
                            employee_search_url=employee_search_url,
                            decision_makers_count=data1['decision_makers_count'],
                            company_profile_picture=data1['logo_url'],
                            company_year_founded=data1['founded_year'],
                            company_number=data1['phone'],
                            company_revenue_min=data1['min_revenue'],
                            company_revenue_max=data1['max_revenue'],
                            company_specialties=data1['specialties'],
                            company_type=data1['company_type'],
                            scraping_id=ScrapingInfo.objects.get(id=scraping_info_id).scraping_id,
                        )

                if next_page(driver):
                    break

        except Exception as e:
            print(f"Error in company deep scrape: {e}")
            update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)

        update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)
    else:
        update_scraping_info(driver, scraping_info_id, status='failed', active_package=active_package)
# End Company + Deep


# Start People + Deep
def extract_profile_deep_data(driver, wait):
    data = {}
    def safe_find_element_by_css_selector(selector):
        try:
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))).text
        except:
            return "None"
    try:
        data['person_full_name'] = safe_find_element_by_css_selector("#profile-card-section [data-anonymize='person-name']")
        data['person_first_name'] = data['person_full_name'].split(' ')[0]
        data['person_last_name'] = data['person_full_name'].split(' ')[1]
    except:
        data['person_first_name'] = "None"
        data['person_last_name'] = "None"
    
    data['connections_degree'] = safe_find_element_by_css_selector('#profile-card-section > section:first-of-type > div:first-of-type > div:nth-of-type(2) > span')
    
    try:
        prospect_is_premium_element = driver.find_element(By.CSS_SELECTOR, '[aria-label="Premium Member"]')
        data['prospect_is_premium'] = True if prospect_is_premium_element else False
    except:
        data['prospect_is_premium'] = False
    
    data['prospect_headline'] = safe_find_element_by_css_selector('#profile-card-section [data-anonymize="headline"]')
    data['prospect_location'] = safe_find_element_by_css_selector('#profile-card-section > section:first-of-type > div:first-of-type > div:nth-of-type(4) > div:first-of-type')
    data['prospect_connections'] = safe_find_element_by_css_selector('#profile-card-section > section:first-of-type > div:first-of-type > div:nth-of-type(4) > div:nth-of-type(2)')
    
    try:
        prospect_linkedin_url_element = driver.find_element(By.CSS_SELECTOR, '[aria-label="Open actions overflow menu"]')
        prospect_linkedin_url_element.click()
        prospect_linkedin_url = driver.find_element(By.CSS_SELECTOR, '#hue-web-menu-outlet div:nth-child(2) ul li:nth-last-child(2)')
        data['prospect_linkedin_url'] = prospect_linkedin_url.get_attribute('href')
    except:
        data['prospect_linkedin_url'] = "None"
    
    try:
        prospect_address_element = driver.find_element(By.TAG_NAME, 'address').text

        contact_number_match = re.search(r'\b\d{10}\b', prospect_address_element)
        data['prospect_phone_no'] = contact_number_match.group() if contact_number_match else "None"

        gmail_match = re.search(r'\b[A-Za-z0-9._%+-]+@gmail\.com\b', prospect_address_element)
        data['prospect_email_address'] = gmail_match.group() if gmail_match else "None"
    except:
        data['prospect_phone_no'] = "None"
        data['prospect_email_address'] = "None"
    
    try:
        prospect_summary_element = driver.find_element(By.XPATH, '//*[@id="about-section"]//*[@data-anonymize="person-blurb"]')
        data['prospect_summary'] = prospect_summary_element.text.replace("… Show more", "")
    except:
        data['prospect_summary'] = "None"

    try:
        prospect_profile_picture_element = driver.find_element(By.XPATH, '//*[@data-anonymize="headshot-photo"]')
        data['prospect_profile_picture'] = prospect_profile_picture_element.get_attribute('src')
    except:
        data['prospect_profile_picture'] = "None"

    try:
        data['years_in_position'], data['months_in_position'] = extract_duration(
            wait.until(EC.presence_of_element_located((By.ID, 'experience-section')))
            .find_element(By.CSS_SELECTOR, '#scroll-to-experience-section > div > ul > li:nth-child(1) > ul > li:nth-child(1) > div > p:nth-child(2)').text
        )
    except:
        data['years_in_position'] = 0
        data['months_in_position'] = 0

    try:
        data['years_in_company'], data['months_in_company'] = extract_duration(
            wait.until(EC.presence_of_element_located((By.ID, 'experience-section')))
            .find_element(By.TAG_NAME, 'ul').find_element(By.TAG_NAME, 'li').find_elements(By.TAG_NAME, 'p')[1].text
        )
    except:
        data['years_in_company'] = 0
        data['months_in_company'] = 0

    try:
        expriance_section = driver.find_element(By.ID, 'experience-section')

        try:
            experience_section_button = driver.find_element(By.ID, 'scroll-to-experience-section').find_element(By.TAG_NAME, 'button')
            experience_section_button.click()
        except:
            pass

        try:    
            data['prospect_position'] = expriance_section.find_element(By.CSS_SELECTOR, '[data-anonymize="job-title"]').text
            data['regular_company_url'] = expriance_section.find_element(By.CSS_SELECTOR, 'ul > li:first-child > div:first-child > div:first-child > a').get_attribute('href')
        except:
            data['prospect_position'] = "None"
            data['regular_company_url'] = "None"
            
        try:
            present_elements = expriance_section.find_elements(By.CSS_SELECTOR, 'div > ul > li')
            data['prospect_current_positions'] = sum(1 for present in present_elements if '–present' in present.text.lower())
        except:
            data['prospect_current_positions'] = 0
    except:
        data['prospect_current_positions'] = 0  
    
    return data

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
                found_elements = [result for result in search_results if result.find_elements(By.CSS_SELECTOR, '[data-view-name="search-results-entity"]')]
                for result in found_elements:
                    prospect_sales_navigator_url = result.find_element(By.CSS_SELECTOR, '[data-view-name="search-results-lead-name"]').get_attribute('href')
                    open_new_tab(driver, prospect_sales_navigator_url)
                    data = extract_profile_deep_data(driver, wait)
                    close_current_tab(driver)

                    if data['regular_company_url'] != "None":
                        open_new_tab(driver, data['regular_company_url'])
                        company_data = extract_company_deep_data(driver, wait, is_csv=True)
                        close_current_tab(driver)
                    else:
                        company_data_keys = ["company_name", "description", "industry", "employee_count", "location", "country", "geographic_area", 
                         "city", "postal_code", "address", "headquarters", "company_id", "linkedin_company_url", 
                         "sales_navigator_company_url", "website", "domain", "decision_makers_search_url", "employee_search_url", 
                         "decision_makers_count", "logo_url", "founded_year", "phone", "min_revenue", "max_revenue", "specialties", 
                         "company_type"]
                        company_data = {key: "None" for key in company_data_keys}

                    LinkedInProfile.objects.create(
                        query=url, sales_navigator_url=prospect_sales_navigator_url, full_name=data['person_full_name'], first_name=data['person_first_name'], last_name=data['person_last_name'],       
                        profile_picture=data['prospect_profile_picture'], job_title=data['prospect_position'], is_premium=data['prospect_is_premium'], location=data['prospect_location'],
                        headline=data['prospect_headline'], connections=data['connections_degree'], linkedin_url=data['prospect_linkedin_url'], summary=data['prospect_summary'], 
                        years_in_company=data['years_in_company'], months_in_company=data['months_in_company'], years_in_position=data['years_in_position'], months_in_position=data['months_in_position'],
                        current_positions=data['prospect_current_positions'], scraping_id = ScrapingInfo.objects.get(id=scraping_info_id).scraping_id
                    )

                    LinkedInCompany.objects.create(
                        query=url, company_name=company_data['company_name'], company_description=company_data['description'], company_industry=company_data['industry'], 
                        company_employee_count=company_data['employee_count'], company_location=company_data['location'], country=company_data['country'],
                        geographicArea=company_data['geographic_area'], city=company_data['city'], postal_code=company_data['postal_code'], address=company_data['address'],
                        company_headquarters=company_data['headquarters'], company_id=company_data['company_id'], regular_company_url=company_data['linkedin_company_url'],
                        sales_navigator_company_url=company_data['sales_navigator_company_url'], company_website=company_data['website'], company_domain=company_data['domain'],
                        decision_makers_search_url=company_data['decision_makers_search_url'], employee_search_url=company_data['employee_search_url'],
                        decision_makers_count=company_data['decision_makers_count'], company_profile_picture=company_data['logo_url'],
                        company_year_founded=company_data['founded_year'], company_number=company_data['phone'], company_revenue_min=company_data['min_revenue'],
                        company_revenue_max=company_data['max_revenue'], company_specialties=company_data['specialties'], company_type=company_data['company_type'],
                        scraping_id=ScrapingInfo.objects.get(id=scraping_info_id).scraping_id,
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
def profile_deep_scrape_and_save_data_csv(csv_file, li_at_value, scraping_info_id, user_agent, request, active_package):
    with open(csv_file.path, 'r') as file:
        links = file.read().splitlines()

    if not links:
        update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)
    driver, wait, logged_in = initialize_scraping(user_agent, li_at_value, scraping_info_id, request, active_package)

    if logged_in:
        for url in links:
            driver.get(url)
            try:
                data = extract_profile_deep_data(driver, wait)
                if data['regular_company_url'] != "None":
                        open_new_tab(driver, data['regular_company_url'])
                        company_data = extract_company_deep_data(driver, wait, is_csv=True)
                        close_current_tab(driver)
                else:
                    company_data_keys = ["company_name", "description", "industry", "employee_count", "location", "country", "geographic_area", 
                        "city", "postal_code", "address", "headquarters", "company_id", "linkedin_company_url", 
                        "sales_navigator_company_url", "website", "domain", "decision_makers_search_url", "employee_search_url", 
                        "decision_makers_count", "logo_url", "founded_year", "phone", "min_revenue", "max_revenue", "specialties", 
                        "company_type"]
                    company_data = {key: "None" for key in company_data_keys}

                LinkedInProfile.objects.create(
                    query=url, sales_navigator_url=url, full_name=data['person_full_name'], first_name=data['person_first_name'], last_name=data['person_last_name'],       
                    profile_picture=data['prospect_profile_picture'], job_title=data['prospect_position'], is_premium=data['prospect_is_premium'], location=data['prospect_location'],
                    headline=data['prospect_headline'], connections=data['connections_degree'], linkedin_url=data['prospect_linkedin_url'], summary=data['prospect_summary'], 
                    years_in_company=data['years_in_company'], months_in_company=data['months_in_company'], years_in_position=data['years_in_position'], months_in_position=data['months_in_position'],
                    current_positions=data['prospect_current_positions'], scraping_id = ScrapingInfo.objects.get(id=scraping_info_id).scraping_id
                )

                LinkedInCompany.objects.create(
                    query=url, company_name=company_data['company_name'], company_description=company_data['description'], company_industry=company_data['industry'], 
                    company_employee_count=company_data['employee_count'], company_location=company_data['location'], country=company_data['country'],
                    geographicArea=company_data['geographic_area'], city=company_data['city'], postal_code=company_data['postal_code'], address=company_data['address'],
                    company_headquarters=company_data['headquarters'], company_id=company_data['company_id'], regular_company_url=company_data['linkedin_company_url'],
                    sales_navigator_company_url=company_data['sales_navigator_company_url'], company_website=company_data['website'], company_domain=company_data['domain'],
                    decision_makers_search_url=company_data['decision_makers_search_url'], employee_search_url=company_data['employee_search_url'],
                    decision_makers_count=company_data['decision_makers_count'], company_profile_picture=company_data['logo_url'],
                    company_year_founded=company_data['founded_year'], company_number=company_data['phone'], company_revenue_min=company_data['min_revenue'],
                    company_revenue_max=company_data['max_revenue'], company_specialties=company_data['specialties'], company_type=company_data['company_type'],
                    scraping_id=ScrapingInfo.objects.get(id=scraping_info_id).scraping_id,
                )
            except:
                pass
        if links:
            update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)
        else:
            update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)
    else:
        update_scraping_info(driver, scraping_info_id, status='failed', active_package=active_package)
# End PDeepCSV

# Start CDeepCSV
def company_deep_scrape_and_save_data_csv(csv_file, li_at_value, scraping_info_id, user_agent, request, active_package):
    with open(csv_file.path, 'r') as file:
        reader = csv.reader(file)
        links = [row[0] for row in reader]

    if not links:
        update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)
    driver, wait, logged_in = initialize_scraping(user_agent, li_at_value, scraping_info_id, request, active_package)

    if logged_in:
        for url in links:
            driver.get(url)
            try:
                data = extract_company_deep_data(driver, wait, is_csv=True)
                if data:
                    LinkedInCompany.objects.create(
                        query=url, company_name=data['company_name'], company_description=data['description'], company_industry=data['industry'], 
                        company_employee_count=data['employee_count'], company_location=data['location'], country=data['country'],
                        geographicArea=data['geographic_area'], city=data['city'], postal_code=data['postal_code'], address=data['address'],
                        company_headquarters=data['headquarters'], company_id=data['company_id'], regular_company_url=data['linkedin_company_url'],
                        sales_navigator_company_url=data['sales_navigator_company_url'], company_website=data['website'], company_domain=data['domain'],
                        decision_makers_search_url=data['decision_makers_search_url'], employee_search_url=data['employee_search_url'],
                        decision_makers_count=data['decision_makers_count'], company_profile_picture=data['logo_url'],
                        company_year_founded=data['founded_year'], company_number=data['phone'], company_revenue_min=data['min_revenue'],
                        company_revenue_max=data['max_revenue'], company_specialties=data['specialties'], company_type=data['company_type'],
                        scraping_id=ScrapingInfo.objects.get(id=scraping_info_id).scraping_id,
                    )
            except:
                pass
        if links:
            update_scraping_info(driver, scraping_info_id, status='completed', active_package=active_package)
    else:
        update_scraping_info(driver, scraping_info_id, status='failed', active_package=active_package)   
# End CDeepCSV