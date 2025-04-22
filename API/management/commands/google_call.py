from django.core.management.base import BaseCommand
from API.models import Hospitals
from django.db.models import Q
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse , quote_plus
from requests_html import HTMLSession
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium_stealth import stealth
import time
from googleapiclient.discovery import build
class Command(BaseCommand):
    help = 'Load hospitals from a text file'
    
    def handle_hospital(self, hospital):
        medical = ['بیمارستان' ,'بیمارستان', 'دندانپزشکی' , 'دندان پزشکی' , 'درمانگاه' , 'آزمایشگاه' , 'داروخانه' , 'چشم پزشکی' , "روانپزشکی" , "روان پزشکی" ,"روانپزشكي"]
        """Process a single hospital with its own browser instance"""
        try:
            # Configure browser options
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            
            # Create dedicated driver instance per thread
            driver = webdriver.Chrome(options=options)
            stealth(driver,
                    languages=["fa-IR"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True)
            
            # Build search query
            query = f"مرکز درمانی {hospital.name} {hospital.city} {hospital.address}"
            url = f"https://www.bing.com/search?q={query}&cc=IR&setlang=fa"
            
            # Execute search
            driver.get(url)
            
            # Wait for results or CAPTCHA
            WebDriverWait(driver, 15).until(
                lambda d: d.find_element(By.ID, "b_results") or d.find_element(By.ID, "b_tween_captcha")
            )
            
            # Process results
            if "captcha" in driver.page_source.lower():
                self.stdout.write(self.style.WARNING(f'CAPTCHA blocked for {hospital.name}'))
            else:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                results = soup.select('li.b_algo')
                if results:
                    first_result = results[0]
                    title = first_result.select_one('h2 a').get_text(strip=True)
                    facility = 'بیمارستان'
                    name = hospital.name
                    for i in title.split():
                        if i in medical:
                            facility = i
                            break
                    
                    try:
                        start_index = title.index(facility) 
                        end_index = title.index(name) + len(name) 
                        substring = title[start_index:end_index].strip()
                        print(name + f"at index : {end_index}")
                        print(facility + f"at index : {start_index}")
                        print(substring)
                    except Exception as e:
                        print(f'error for {hospital.name}' + str(e))
                        print(title)

                    
                    # self.stdout.write(f'{title}')
                    
            
            driver.quit()
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing {hospital.name}: {str(e)}'))
            if driver:
                driver.quit()
            return False
        
    def handle(self, *args, **options):
        medical = ['بیمارستان' ,'بیمارستان' ,  'دندانپزشکی' , 'دندان پزشکی' , 'درمانگاه' , 'آزمایشگاه' , 'داروخانه' , 'چشم پزشکی' , "روانپزشكي" , "روان پزشکی" , "روانپزشکی" , "دکتر" , "کلینیک"]
        hospitals = Hospitals.objects.filter(~Q(name__icontains = medical))
        
        MIN_DELAY = 2  # Minimum delay between requests in seconds
        MAX_DELAY = 5  # Maximum delay between requests
        BATCH_SIZE = 5  # Number of requests before longer delay
        LONG_DELAY = 30  # 2 minutes delay after each batch
        MAX_WORKERS = 3
        BATCH_SIZE = 10
        
    #    
        for i in range(0, len(hospitals), BATCH_SIZE):
            batch = hospitals[i:i+BATCH_SIZE]
            
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {}
                
                # Submit batch tasks
                for hospital in batch:
                    # Add random delay before submission
                    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                    future = executor.submit(self.handle_hospital, hospital)
                    futures[future] = hospital.name
                
                # Monitor progress
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Thread error for {name}: {str(e)}'))
            
            # Long delay between batches
            self.stdout.write(f'Completed batch {i//BATCH_SIZE + 1}, waiting {LONG_DELAY}s...')
            time.sleep(LONG_DELAY)
