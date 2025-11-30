"""
Sasthyaseba.com Doctor Scraper
===============================
Scrapes all doctor profiles from sasthyaseba.com

Features:
- Scrapes all 355 pages of doctor listings
- Extracts: name, qualifications, specialty, experience, hospital, location
- Automatic pagination handling
- Progress saving every 25 records

"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import pandas as pd
import os

def setup_driver():
    """Initialize Chrome driver with options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(options=options)
    return driver

def extract_doctor_profiles_from_page(driver, page_num):
    """Extract all doctor profile URLs from a single search page"""
    url = f"https://sasthyaseba.com/search?type=doctor&page={page_num}"
    
    print(f"   📄 Loading page {page_num}...")
    driver.get(url)
    time.sleep(3)
    
    # Scroll down slowly to load all content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    doctor_profiles = []
    
    try:
        # Find all links that go to doctor profiles
        all_links = driver.find_elements(By.TAG_NAME, "a")
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                if href and '/doctors/' in href:
                    # Clean URL
                    href = href.split('?')[0].split('#')[0]
                    if href not in doctor_profiles:
                        doctor_profiles.append(href)
            except:
                continue
        
        print(f"      ✅ Found {len(doctor_profiles)} doctors on page {page_num}")
        
    except Exception as e:
        print(f"      ❌ Error on page {page_num}: {e}")
    
    return doctor_profiles

def scrape_doctor_profile_details(driver, profile_url):
    """Scrape detailed information from doctor's profile page"""
    try:
        driver.get(profile_url)
        time.sleep(2)
        
        # Scroll to load all content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        details = {
            'profile_url': profile_url,
            'name': 'N/A',
            'qualifications': 'N/A',
            'specialty': 'N/A',
            'experience': 'N/A',
            'hospital': 'N/A',
            'location': 'N/A'
        }
        
        # Get page text
        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
        
        # Extract NAME
        try:
            name_elem = driver.find_element(By.XPATH, 
                "//h1 | //h2[contains(@class, 'name')] | "
                "//div[contains(@class, 'doctor-name')] | "
                "//div[contains(@class, 'profile')]//h2")
            name_text = name_elem.text.strip()
            if name_text and len(name_text) < 100:
                details['name'] = name_text
        except:
            # Fallback: try to find name in first few lines
            for line in lines[:10]:
                if any(title in line for title in ['Dr.', 'Prof.', 'Assoc.', 'Asst.']):
                    if len(line) < 100 and not any(x in line for x in ['MBBS', 'FCPS', 'Experience', 'Specialist']):
                        details['name'] = line
                        break
        
        # Extract QUALIFICATIONS
        for line in lines[:20]:
            if any(qual in line for qual in ['MBBS', 'FCPS', 'MD', 'MS', 'BCS', 'MRCP', 'FRCS', 'MCPS']):
                if len(line) < 200 and 'Years' not in line:
                    details['qualifications'] = line
                    break
        
        # Extract SPECIALTY - IMPROVED VERSION
        specialty_keywords = [
            'Rheumatologist', 'Cardiologist', 'Neurologist', 'Dermatologist',
            'Nephrologist', 'Oncologist', 'Endocrinologist', 'Gastroenterologist',
            'Specialist', 'Surgeon', 'Pediatrician', 'Gynecologist', 'Urologist',
            'Psychiatrist', 'Orthopedic', 'ENT', 'Dentist'
        ]
        
        # Method 1: Look in first 15 lines
        for line in lines[:15]:
            if any(skip in line for skip in [
                'MBBS', 'FCPS', 'Years', 'Hospital', 'Doctor', 'Dhaka', 
                'Book', 'Get', 'Find', 'View'
            ]):
                continue
            
            line_lower = line.lower()
            for keyword in specialty_keywords:
                if keyword.lower() == line_lower or keyword.lower() in line_lower:
                    if len(line) < 100 and not any(qual in line for qual in ['MBBS', 'FCPS']):
                        details['specialty'] = line
                        break
            if details['specialty'] != 'N/A':
                break
        
        # Method 2: Look for single-word specialties
        if details['specialty'] == 'N/A':
            for line in lines[:20]:
                if (5 < len(line) < 40 and line[0].isupper() and
                    any(line.endswith(suffix) for suffix in ['ologist', 'ist', 'ian', 'Specialist', 'Surgeon'])):
                    if not any(skip in line for skip in ['MBBS', 'Years', 'Hospital', 'Book']):
                        details['specialty'] = line
                        break
        
        # Extract EXPERIENCE
        for line in lines[:30]:
            if 'Years of Experience' in line or 'Experience Overall' in line:
                details['experience'] = line
                break
        
        # Extract HOSPITAL and LOCATION - IMPROVED VERSION
        hospitals = []
        locations = []
        
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['Hospital', 'Medical Centre', 'Medical Center', 
                                                    'Clinic', 'Healthcare', 'Medical College']):
                # STRICT FILTERING
                if (len(line) < 200 and
                    'Find Hospital' not in line and
                    'Get Direction' not in line and
                    'Book Appointment' not in line and
                    'Availability' not in line and
                    'Work Experience' not in line and
                    'Education' not in line and
                    'Locations' not in line and
                    'View all' not in line):
                    
                    if (line not in hospitals and len(line) > 5 and
                        not line.startswith(('Book', 'View', 'Find', 'Get'))):
                        
                        hospitals.append(line)
                        
                        # Look for location in next few lines
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j]
                            
                            if (len(next_line) > 15 and
                                'Get Direction' not in next_line and
                                'Book Appointment' not in next_line and
                                'Availability' not in next_line and
                                any(loc in next_line for loc in [',', 'Road', 'Rd', 'Dhaka', 'Bangladesh',
                                                                  'Chittagong', 'Sylhet', 'Building'])):
                                
                                if next_line not in locations:
                                    locations.append(next_line)
                                break
                        
                        # Only get first valid hospital/location pair
                        if len(hospitals) >= 1:
                            break
        
        # Set hospital and location
        if hospitals:
            details['hospital'] = hospitals[0]
        if locations:
            details['location'] = locations[0]
        
        return details
        
    except Exception as e:
        print(f"      ❌ Error scraping profile: {e}")
        return None

def main():
    """Main scraping function"""
    output_file = "sasthyaseba_doctors.csv"
    
    # Configuration
    START_PAGE = 1
    END_PAGE = 355  # Total pages on the website
    
    print("=" * 80)
    print("🏥 SASTHYASEBA.COM DOCTOR SCRAPER")
    print("=" * 80)
    print(f"📊 Output file: {output_file}")
    print(f"📄 Scraping pages {START_PAGE} to {END_PAGE}")
    print("=" * 80 + "\n")
    
    driver = setup_driver()
    
    try:
        all_doctors_data = []
        
        # Load existing data if file exists (for resume capability)
        existing_urls = set()
        if os.path.exists(output_file):
            try:
                existing_df = pd.read_csv(output_file)
                existing_urls = set(existing_df['profile_url'].tolist())
                all_doctors_data = existing_df.to_dict('records')
                print(f"📂 Loaded {len(existing_urls)} existing records\n")
            except:
                pass
        
        # PHASE 1: Collect all doctor URLs
        print("PHASE 1: Collecting doctor profile URLs")
        print("=" * 80)
        
        all_doctor_urls = set()
        
        for page_num in range(START_PAGE, END_PAGE + 1):
            print(f"\n[Page {page_num}/{END_PAGE}]")
            
            try:
                urls = extract_doctor_profiles_from_page(driver, page_num)
                new_urls = [url for url in urls if url not in existing_urls]
                before_count = len(all_doctor_urls)
                all_doctor_urls.update(new_urls)
                after_count = len(all_doctor_urls)
                
                print(f"      ➕ Added {after_count - before_count} new doctors")
                print(f"      📊 Total unique doctors collected: {len(all_doctor_urls)}")
                
                if page_num % 50 == 0:
                    print(f"\n      💾 Checkpoint: Collected {len(all_doctor_urls)} unique doctors")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"      ⚠️ Error on page {page_num}: {e}")
                continue
        
        all_doctor_urls = list(all_doctor_urls)
        print(f"\n✅ Phase 1 Complete: Found {len(all_doctor_urls)} unique new doctor profiles")
        
        if not all_doctor_urls:
            print("❌ No new doctors to scrape!")
            return
        
        # PHASE 2: Scrape each doctor's profile
        print("\n" + "=" * 80)
        print("PHASE 2: Scraping doctor details")
        print("=" * 80)
        
        for idx, url in enumerate(all_doctor_urls, 1):
            print(f"\n[{idx}/{len(all_doctor_urls)}] {url}")
            
            try:
                details = scrape_doctor_profile_details(driver, url)
                
                if details:
                    all_doctors_data.append(details)
                    print(f"      ✅ {details['name']} | {details['hospital']}")
                
                # Save progress every 25 doctors
                if idx % 25 == 0:
                    df = pd.DataFrame(all_doctors_data)
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                    print(f"\n      💾 Progress saved: {len(all_doctors_data)} total records")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
                continue
        
        # Final save
        if all_doctors_data:
            df = pd.DataFrame(all_doctors_data)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            print("\n" + "=" * 80)
            print("✅ SCRAPING COMPLETE!")
            print("=" * 80)
            print(f"📊 Total records: {len(all_doctors_data)}")
            print(f"💾 Saved to: {output_file}")
            
            # Show data quality stats
            print("\n📈 DATA QUALITY:")
            print(f"   ✅ Records with name: {(df['name'] != 'N/A').sum()}")
            print(f"   ✅ Records with qualifications: {(df['qualifications'] != 'N/A').sum()}")
            print(f"   ✅ Records with specialty: {(df['specialty'] != 'N/A').sum()}")
            print(f"   ✅ Records with hospital: {(df['hospital'] != 'N/A').sum()}")
            print(f"   ✅ Records with location: {(df['location'] != 'N/A').sum()}")
        else:
            print("\n❌ No data collected")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrupted by user")
        if all_doctors_data:
            df = pd.DataFrame(all_doctors_data)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"💾 Saved {len(all_doctors_data)} records before exit")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("\n🔚 Driver closed")

if __name__ == "__main__":
    main()