"""
Sasthyaseba.com India Doctors Scraper
======================================
Scrapes Indian doctor profiles from sasthyaseba.com (country_id=103)

Features:
- Scrapes pages 1-45 for India
- Extracts MULTIPLE qualifications per doctor
- Appends to existing CSV file
- All fields: profile_url, name, qualifications, specialty, experience, hospital, location

Author: Your Name
Repository: https://github.com/yourusername/sasthyaseba-scraper
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
    """Extract all doctor profile URLs from a single India search page"""
    url = f"https://sasthyaseba.com/search?type=doctor&country_id=103&page={page_num}"
    
    print(f"   📄 Loading page {page_num}...")
    driver.get(url)
    time.sleep(3)
    
    # Scroll down to load all content
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

def extract_all_qualifications(lines):
    """
    Extract ALL qualifications from page text (handles multiple degrees)
    Returns a comma-separated string of all qualifications
    """
    qualification_keywords = [
        'MBBS', 'BDS', 'FCPS', 'MD', 'MS', 'FRCS', 'MRCP', 'MCPS',
        'BCS', 'MPH', 'M.Phil', 'MPhil', 'PhD', 'DM', 'MCh', 'DNB',
        'FRCOG', 'MRCOG', 'FACS', 'DOMS', 'DO', 'DCH', 'DGO', 'DA',
        'Diploma', 'Fellowship', 'FACC', 'FRCP', 'FICS'
    ]
    
    found_qualifications = []
    
    # Search in first 30 lines (qualifications usually appear early)
    for line in lines[:30]:
        # Skip lines that are clearly not qualifications
        if any(skip in line for skip in [
            'Years of Experience', 'Experience Overall', 'Year of Experience',
            'Doctor Reg', 'BMDC', 'Specialist', 'Surgeon', 'Consultant',
            'Hospital', 'Medical Centre', 'Clinic', 'Get Direction',
            'Book Appointment', 'Dhaka', 'Bangladesh', 'India'
        ]):
            continue
        
        # Check if line contains any qualification keywords
        line_upper = line.upper()
        has_qualification = any(qual.upper() in line_upper for qual in qualification_keywords)
        
        if has_qualification:
            # This line likely contains qualifications
            # Clean it up and add to list
            line_clean = line.strip()
            
            # Remove common prefixes
            for prefix in ['Qualifications:', 'Degrees:', 'Education:']:
                if line_clean.startswith(prefix):
                    line_clean = line_clean.replace(prefix, '').strip()
            
            # Skip if it's part of a doctor's name or title
            if any(title in line for title in ['Dr.', 'Prof.', 'Assoc.', 'Asst.']) and len(line) < 50:
                continue
            
            # Add if not already in list and reasonable length
            if line_clean and 3 < len(line_clean) < 250:
                if line_clean not in found_qualifications:
                    found_qualifications.append(line_clean)
    
    # Join all qualifications with comma
    if found_qualifications:
        # If we found multiple lines, join them intelligently
        all_quals = ', '.join(found_qualifications)
        # Clean up double commas and extra spaces
        all_quals = ' '.join(all_quals.split())
        all_quals = all_quals.replace(' ,', ',').replace(',,', ',')
        return all_quals
    
    return 'N/A'

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
        
        # ========== EXTRACT NAME ==========
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
        
        # ========== EXTRACT ALL QUALIFICATIONS (IMPROVED) ==========
        details['qualifications'] = extract_all_qualifications(lines)
        
        # ========== EXTRACT SPECIALTY ==========
        specialty_keywords = [
            'Rheumatologist', 'Cardiologist', 'Neurologist', 'Dermatologist',
            'Nephrologist', 'Oncologist', 'Endocrinologist', 'Gastroenterologist',
            'Pulmonologist', 'Hematologist', 'Radiologist', 'Pathologist',
            'Anesthesiologist', 'Ophthalmologist', 'Neonatologist', 'Gynecologist',
            'Urologist', 'Immunologist', 'Pediatrician', 'Obstetrician',
            'Psychiatrist', 'Dentist', 'ENT',
            'Specialist', 'Medicine Specialist', 'Chest Specialist',
            'Respiratory Specialist', 'Critical Care Medicine Specialist',
            'Diabetes Specialist', 'Family Medicine Specialist',
            'Surgeon', 'General Surgeon', 'Neurosurgeon', 'Cardiovascular Surgeon',
            'Thoracic Surgeon', 'Vascular Surgeon', 'Plastic Surgeon',
            'Colorectal Surgeon', 'Hepatobiliary Surgeon', 'Orthopedic Surgeon',
            'Maxillofacial Surgeon', 'Dental Surgeon'
        ]
        
        # Method 1: Look in first 15 lines
        for line in lines[:15]:
            if any(skip in line for skip in [
                'MBBS', 'FCPS', 'BCS', 'MD', 'MS', 'Years', 'Hospital',
                'Dhaka', 'Bangladesh', 'India', 'Book', 'Get', 'Find', 'View', 'Doctor'
            ]):
                continue
            
            line_lower = line.lower()
            for keyword in specialty_keywords:
                if keyword.lower() == line_lower:
                    details['specialty'] = line
                    break
                elif keyword.lower() in line_lower and len(line) < 100:
                    if not any(qual in line for qual in ['MBBS', 'FCPS', 'MD', 'MS']):
                        details['specialty'] = line
                        break
            if details['specialty'] != 'N/A':
                break
        
        # Method 2: Look for single-word specialties
        if details['specialty'] == 'N/A':
            for line in lines[:20]:
                if (5 < len(line) < 40 and line[0].isupper()):
                    if any(line.endswith(suffix) for suffix in [
                        'ologist', 'logist', 'ist', 'ian', 'ician',
                        'Specialist', 'Surgeon', 'Consultant'
                    ]):
                        if not any(skip in line for skip in ['MBBS', 'FCPS', 'Years', 'Hospital']):
                            details['specialty'] = line
                            break
        
        # ========== EXTRACT EXPERIENCE ==========
        for line in lines[:30]:
            if 'Years of Experience' in line or 'Experience Overall' in line or 'Year of Experience' in line:
                details['experience'] = line
                break
        
        # ========== EXTRACT HOSPITAL & LOCATION ==========
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
                                any(loc in next_line for loc in [',', 'Road', 'Rd', 'India', 
                                                                  'No.', 'Street', 'Avenue',
                                                                  'Mumbai', 'Delhi', 'Bangalore', 'Kolkata',
                                                                  'Chennai', 'Hyderabad', 'Pune', 'City'])):
                                
                                if next_line not in locations:
                                    locations.append(next_line)
                                break
                        
                        # Only get first valid hospital/location pair
                        if len(hospitals) >= 1:
                            break
        
        if hospitals:
            details['hospital'] = hospitals[0]
        if locations:
            details['location'] = locations[0]
        
        return details
        
    except Exception as e:
        print(f"      ❌ Error scraping profile: {e}")
        return None

def main():
    """Main scraping function for India doctors"""
    output_file = r"C:\Users\shiha\bd-docs\data\Bangladeshi and Indian Doctors.csv"
    
    # Configuration
    START_PAGE = 1
    END_PAGE = 45  # India has 45 pages
    COUNTRY = "India"
    COUNTRY_ID = 103
    
    print("=" * 80)
    print("🇮🇳 SASTHYASEBA.COM INDIA DOCTORS SCRAPER")
    print("=" * 80)
    print(f"📊 Output file: {output_file}")
    print(f"📄 Scraping pages {START_PAGE} to {END_PAGE}")
    print(f"🌍 Country: {COUNTRY} (ID: {COUNTRY_ID})")
    print("=" * 80 + "\n")
    
    driver = setup_driver()
    
    try:
        all_doctors_data = []
        
        # Load existing data if file exists
        existing_urls = set()
        if os.path.exists(output_file):
            try:
                existing_df = pd.read_csv(output_file)
                existing_urls = set(existing_df['profile_url'].tolist())
                all_doctors_data = existing_df.to_dict('records')
                print(f"📂 Loaded {len(existing_urls)} existing records from file\n")
            except Exception as e:
                print(f"⚠️ Could not load existing file: {e}")
                print("   Starting fresh...\n")
        
        # PHASE 1: Collect all doctor URLs
        print("PHASE 1: Collecting India doctor profile URLs")
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
                print(f"      📊 Total unique India doctors collected: {len(all_doctor_urls)}")
                
                if page_num % 10 == 0:
                    print(f"\n      💾 Checkpoint: Collected {len(all_doctor_urls)} unique doctors")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"      ⚠️ Error on page {page_num}: {e}")
                continue
        
        all_doctor_urls = list(all_doctor_urls)
        print(f"\n✅ Phase 1 Complete: Found {len(all_doctor_urls)} unique new India doctor profiles")
        
        if not all_doctor_urls:
            print("❌ No new doctors to scrape!")
            print(f"   (Already have {len(existing_urls)} doctors in file)")
            return
        
        # PHASE 2: Scrape each doctor's profile
        print("\n" + "=" * 80)
        print("PHASE 2: Scraping India doctor details")
        print("=" * 80)
        
        for idx, url in enumerate(all_doctor_urls, 1):
            print(f"\n[{idx}/{len(all_doctor_urls)}] {url}")
            
            try:
                details = scrape_doctor_profile_details(driver, url)
                
                if details:
                    all_doctors_data.append(details)
                    print(f"      ✅ {details['name']}")
                    print(f"      📚 Quals: {details['qualifications'][:80]}...")
                    print(f"      🏥 Hospital: {details['hospital']}")
                
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
            print(f"📊 Total records in file: {len(all_doctors_data)}")
            print(f"   🇮🇳 New India doctors added: {len(all_doctor_urls)}")
            print(f"💾 Saved to: {output_file}")
            
            # Show data quality stats for NEW records only
            new_df = df.tail(len(all_doctor_urls))
            print("\n📈 DATA QUALITY (New India Records):")
            print(f"   ✅ Records with name: {(new_df['name'] != 'N/A').sum()}")
            print(f"   ✅ Records with qualifications: {(new_df['qualifications'] != 'N/A').sum()}")
            print(f"   ✅ Records with specialty: {(new_df['specialty'] != 'N/A').sum()}")
            print(f"   ✅ Records with hospital: {(new_df['hospital'] != 'N/A').sum()}")
            print(f"   ✅ Records with location: {(new_df['location'] != 'N/A').sum()}")
            
            # Sample of qualifications to verify multiple degrees
            print("\n📚 SAMPLE QUALIFICATIONS (verify multiple degrees):")
            sample_quals = new_df[new_df['qualifications'] != 'N/A']['qualifications'].head(5)
            for i, qual in enumerate(sample_quals, 1):
                print(f"   {i}. {qual}")
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