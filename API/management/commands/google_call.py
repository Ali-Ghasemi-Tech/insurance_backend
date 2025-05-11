from django.core.management.base import BaseCommand
from API.models import Hospitals
from django.db.models import Q
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus
import random
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async
import asyncio

class Command(BaseCommand):
    help = 'Load hospitals from a text file using async event loop'
    
    async def handle_hospital(self, hospital, semaphore):
        medical = [ "دکتر" ,'بیمارستان', 'دندانپزشکی', 'دندان پزشکی', 'درمانگاه', 
                  'آزمایشگاه', 'داروخانه', "چشم پزشک" , 'چشم پزشکی', "روانپزشکی", 
                  "روان پزشکی", "روانپزشكي" , "مرکز درمانی" , "مرکز پزشکی" , "مرکز آموزشی درمانی" , "آزمایشگاه" , "سی تی اسکن" , "کلینک" , "مرکز روماتیسم" , "کلینیک" , "درمانگاه" , "مرکز آموزشی درمانی" , "مرکز تصویربرداری" , "متخصص چشم‌پزشکی" , "مجتمع آموزشی درمانی"]
        medical = set(medical)
        
        async with semaphore:
            try:
                async with async_playwright() as p:
                    # Launch browser with Farsi language
                    browser = await p.chromium.launch(
                        headless=True,
                        channel="chrome",
                        args=["--disable-blink-features=AutomationControlled", "--lang=fa-IR"]
                    )
                    
                    context = await browser.new_context(
                        locale='fa-IR',
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
                    )
                    
                    page = await context.new_page()
                    
                    # Build search query
                    query = f"مرکز درمانی {hospital.name} {hospital.city} {hospital.address}"
                    url = f"https://www.bing.com/search?q={quote_plus(query)}&cc=IR&setlang=fa"
                    
                    # Add random delay between requests
                    await asyncio.sleep(random.uniform(1, 3))
                    
                    # Navigate to page
                    await page.goto(url, wait_until="domcontentloaded")
                    
                    # Wait for results or CAPTCHA
                    try:
                        await page.wait_for_selector('#b_results, #b_tween_captcha', timeout=15000)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Timeout waiting for results for {hospital.name}'))
                        return

                    content = await page.content()
                    
                    if "captcha" in content.lower():
                        self.stdout.write(self.style.WARNING(f'CAPTCHA blocked for {hospital.name}'))
                    else:
                        soup = BeautifulSoup(content, 'html.parser')
                        results = soup.select('li.b_algo')
                        
                        if results:
                            first_result = results[0]
                            title_element = first_result.select_one('h2 a')
                            title = title_element.get_text(strip=True) if title_element else ""
                            title = title.replace('ي' , 'ی')
                            title = title.replace('ك' , "ک")
                            facility = 'بیمارستان'
                            name = hospital.name
                            for i in medical:
                                try:
                                    index = title.index(i)
                                    if isinstance(index , int):
                                        facility = title[index:index + len(i)]
                                        print(f'facility updated to: {facility}')
                                        break
                                except:
                                    continue
                            print(facility)
                            print(name)
                            try:
                                facility = facility.strip()
                                # for i in name.split():
                                #     i = i.strip()
                                #     if i in title.split():
                                #         name = i
                                # name = name.strip()
                                # start_index = title.index(facility) 
                                # end_index = title.index(name)
                                
                                # if start_index < end_index:
                                #     substring = title[start_index:end_index + len(name)].strip()
                                # elif end_index < start_index:
                                #     substring = title[end_index:start_index + len(facility)].strip()
                                # else:
                                #     substring = hospital.name
                                if facility in title and facility not in hospital.name:
                                    substring = facility
                                # Async save to database
                                    hospital.name = substring + ' ' + hospital.name
                                    await sync_to_async(hospital.save)()
                                    self.stdout.write(self.style.SUCCESS(f"Updated record {hospital.id} , {hospital.name}"))
                                else:
                                    self.stdout.write(self.style.ERROR(f"facility not found{hospital.id} , {hospital.name} , {title}"))
                                
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"{e} - id {hospital.id} - title {title}"))
                    
                    await browser.close()
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {hospital.name}: {str(e)}'))
                if 'browser' in locals():
                    await browser.close()

    async def process_batch(self, batch, semaphore):
        tasks = []
        for hospital in batch:
            task = asyncio.create_task(self.handle_hospital(hospital, semaphore))
            tasks.append(task)
            # Add small delay between task creation
            await asyncio.sleep(random.uniform(0.1, 0.5))
        
        await asyncio.gather(*tasks)

    async def async_handle(self, **options):
        medical = ['بیمارستان', 'دندانپزشکی', 'دندان پزشکی', 'درمانگاه', 
                  'آزمایشگاه', 'داروخانه', 'چشم پزشکی', "روانپزشكي", 
                  "روان پزشکی", "روانپزشکی", "کلینیک", "دندانپ", 
                  "بیمارس", "آزمایش", "روان", "کلین", "مطب" , "چشم پزشک" ,"مرکز درمانی" , "مرکز پزشکی" , "مرکز آموزشی درمانی" , "آزمایشگاه" , "سی تی اسکن" , "کلینک" , "مرکز روماتیسم" , "دکتر"  , 'مرکز' , "دکتر" ,'بیمارستان', 'دندانپزشکی', 'دندان پزشکی', 'درمانگاه', 
                  'آزمایشگاه', 'داروخانه', 'چشم پزشکی', "روانپزشکی", 
                  "روان پزشکی", "روانپزشكي", "چشم پزشک" , "مرکز درمانی" , "مرکز پزشکی" , "مرکز آموزشی درمانی" , "آزمایشگاه" , "سی تی اسکن" , "کلینک" , "مرکز روماتیسم" , 'مرکز' , "کلینیک" , "درمانگاه" , "مرکز آموزشی درمانی"]
        
        query = Q()
        for term in medical:
            query |= Q(name__icontains=term)
        
        # Async database query
        qs = Hospitals.objects.exclude(query)
        hospitals = await sync_to_async(list)(qs)
        print(f"{len(hospitals)} medical facilities not verefied")
        BATCH_SIZE = 50
        MAX_CONCURRENT = 10
        LONG_DELAY = 10  # Seconds between batches
        
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
        for i in range(0, len(hospitals), BATCH_SIZE):
            batch = hospitals[i:i+BATCH_SIZE]
            self.stdout.write(f'Processing batch {i//BATCH_SIZE + 1}')
            
            await self.process_batch(batch, semaphore)
            
            # Delay between batches
            if i + BATCH_SIZE < len(hospitals):
                self.stdout.write(f'Waiting {LONG_DELAY} seconds before next batch...')
                await asyncio.sleep(LONG_DELAY)

    def handle(self, *args, **options):
        asyncio.run(self.async_handle(**options))