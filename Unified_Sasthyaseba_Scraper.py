"""
Unified Sasthyaseba.com Doctor Scraper
======================================
One script to scrape all doctors from sasthyaseba.com with smart extraction

Features:
- Scrapes doctors by country (Bangladesh: 18, India: 103, or All)
- Intelligent extraction of ALL qualifications
- Auto-fixes missing fields on first pass
- Resume capability
- Progress saving every 25 records
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd
import os

class SasthyasebaScraper:
    def __init__(self, output_file="doctors_data.csv", country_id=None):
        """
        Initialize scraper
        country_id: None (all countries), 18 (Bangladesh), 103 (India)
        """
        self.output_file = output_file
        self.country_id = country_id
        self.driver = None
        self.existing_urls = set()
        self.all_data = []
        
    def setup_driver(self):
        """Initialize Chrome driver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver = webdriver.Chrome(options=options)
        
    def load_existing_data(self):
        """Load existing data to avoid re-scraping"""
        if os.path.exists(self.output_file):
            try:
                df = pd.read_csv(self.output_file)
                self.existing_urls = set(df['profile_url'].tolist())
                self.all_data = df.to_dict('records')
                print(f"📂 Loaded {len(self.existing_urls)} existing records\n")
            except Exception as e:
                print(f"⚠️ Could not load existing file: {e}\n")
    
    def get_total_pages(self):
        """Determine total pages for the country"""
        if self.country_id == 18:  # Bangladesh
            return 310
        elif self.country_id == 103:  # India
            return 45
        else:  # All countries
            return 355
    
    def build_search_url(self, page_num):
        """Build search URL based on country filter"""
        base = "https://sasthyaseba.com/search?type=doctor"
        if self.country_id:
            return f"{base}&country_id={self.country_id}&page={page_num}"
        return f"{base}&page={page_num}"
    
    def extract_profile_urls(self, page_num):
        """Extract all doctor profile URLs from a search page"""
        url = self.build_search_url(page_num)
        
        print(f"   📄 Loading page {page_num}...")
        self.driver.get(url)
        time.sleep(3)
        
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        doctor_profiles = []
        all_links = self.driver.find_elements(By.TAG_NAME, "a")
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                if href and '/doctors/' in href:
                    href = href.split('?')[0].split('#')[0]
                    if href not in doctor_profiles and href not in self.existing_urls:
                        doctor_profiles.append(href)
            except:
                continue
        
        print(f"      ✅ Found {len(doctor_profiles)} new doctors on page {page_num}")
        return doctor_profiles
    
    def extract_all_qualifications(self, lines):
        """Extract ALL qualifications (handles multiple degrees)"""
        qual_keywords = [
            'MBBS', 'BDS', 'FCPS', 'MD', 'MS', 'FRCS', 'MRCP', 'MCPS',
            'BCS', 'MPH', 'MPhil', 'PhD', 'DM', 'MCh', 'DNB',
            'FRCOG', 'MRCOG', 'FACS', 'DOMS', 'DO', 'DCH', 'DGO', 'DA',
            'Diploma', 'Fellowship', 'FACC', 'FRCP', 'FICS', 'MNAMS'
        ]
        
        found_quals = []
        
        for line in lines[:30]:
            # Skip non-qualification lines
            if any(skip in line for skip in [
                'Years of Experience', 'Experience Overall', 'Doctor Reg',
                'BMDC', 'Specialist', 'Surgeon', 'Consultant',
                'Hospital', 'Medical Centre', 'Clinic', 'Get Direction',
                'Book Appointment', 'Dhaka', 'Bangladesh', 'India'
            ]):
                continue
            
            line_upper = line.upper()
            has_qual = any(qual.upper() in line_upper for qual in qual_keywords)
            
            if has_qual:
                line_clean = line.strip()
                
                # Remove common prefixes
                for prefix in ['Qualifications:', 'Degrees:', 'Education:']:
                    if line_clean.startswith(prefix):
                        line_clean = line_clean.replace(prefix, '').strip()
                
                # Skip if part of name/title
                if any(title in line for title in ['Dr.', 'Prof.', 'Assoc.', 'Asst.']) and len(line) < 50:
                    continue
                
                if line_clean and 3 < len(line_clean) < 250:
                    if line_clean not in found_quals:
                        found_quals.append(line_clean)
        
        if found_quals:
            all_quals = ', '.join(found_quals)
            all_quals = ' '.join(all_quals.split())
            all_quals = all_quals.replace(' ,', ',').replace(',,', ',')
            return all_quals
        
        return 'N/A'
    
    def extract_specialty(self, lines):
        """Extract specialty with improved logic"""
        keywords = [
            'Rheumatologist', 'Cardiologist', 'Neurologist', 'Dermatologist',
            'Nephrologist', 'Oncologist', 'Endocrinologist', 'Gastroenterologist',
            'Pulmonologist', 'Hematologist', 'Radiologist', 'Pathologist',
            'Anesthesiologist', 'Ophthalmologist', 'Neonatologist', 'Gynecologist',
            'Urologist', 'Immunologist', 'Pediatrician', 'Obstetrician',
            'Psychiatrist', 'Dentist', 'ENT', 'Specialist', 'Medicine Specialist',
            'Chest Specialist', 'Respiratory Specialist', 'Critical Care Medicine Specialist',
            'Diabetes Specialist', 'Family Medicine Specialist', 'Surgeon',
            'General Surgeon', 'Neurosurgeon', 'Cardiovascular Surgeon',
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
            for keyword in keywords:
                if keyword.lower() == line_lower:
                    return line
                elif keyword.lower() in line_lower and len(line) < 100:
                    if not any(qual in line for qual in ['MBBS', 'FCPS', 'MD', 'MS']):
                        return line
        
        # Method 2: Look for specialty suffixes
        for line in lines[:20]:
            if 5 < len(line) < 40 and line[0].isupper():
                if any(line.endswith(suffix) for suffix in [
                    'ologist', 'logist', 'ist', 'ian', 'ician',
                    'Specialist', 'Surgeon', 'Consultant'
                ]):
                    if not any(skip in line for skip in ['MBBS', 'FCPS', 'Years', 'Hospital']):
                        return line
        
        return 'N/A'
    
    def extract_experience(self, lines):
        """Extract years of experience"""
        for line in lines[:30]:
            if 'Years of Experience' in line or 'Experience Overall' in line or 'Year of Experience' in line:
                return line
        return 'N/A'
    
    def extract_hospital_location(self, lines):
        """Extract hospital and location (returns tuple)"""
        hospitals = []
        locations = []
        
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in [
                'Hospital', 'Medical Centre', 'Medical Center',
                'Clinic', 'Healthcare', 'Medical College'
            ]):
                # Strict filtering
                if (len(line) < 200 and
                    'Find Hospital' not in line and
                    'Get Direction' not in line and
                    'Book Appointment' not in line and
                    'Availability' not in line and
                    'Work Experience' not in line and
                    'Education' not in line and
                    'Locations' not in line and
                    'View all' not in line and
                    'Info' not in line):
                    
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
                                'Find Hospital' not in next_line and
                                'Info' not in next_line and
                                any(loc in next_line for loc in [
                                    ',', 'Road', 'Rd', 'Dhaka', 'Bangladesh', 'India',
                                    'No.', 'Street', 'Avenue', 'Chittagong', 'Sylhet',
                                    'Rajshahi', 'Khulna', 'Barisal', 'Mumbai', 'Delhi',
                                    'Bangalore', 'Kolkata', 'Chennai', 'Hyderabad',
                                    'City', 'Building', 'Circular'
                                ])):
                                
                                if next_line not in locations:
                                    locations.append(next_line)
                                break
                        
                        if len(hospitals) >= 1:
                            break
        
        hospital = hospitals[0] if hospitals else 'N/A'
        location = locations[0] if locations else 'N/A'
        return hospital, location
    
    def scrape_profile(self, profile_url):
        """Scrape all details from a doctor's profile"""
        try:
            self.driver.get(profile_url)
            time.sleep(2)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
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
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            
            # Extract NAME
            try:
                name_elem = self.driver.find_element(By.XPATH, 
                    "//h1 | //h2[contains(@class, 'name')] | "
                    "//div[contains(@class, 'doctor-name')] | "
                    "//div[contains(@class, 'profile')]//h2")
                name_text = name_elem.text.strip()
                if name_text and len(name_text) < 100:
                    details['name'] = name_text
            except:
                for line in lines[:10]:
                    if any(title in line for title in ['Dr.', 'Prof.', 'Assoc.', 'Asst.']):
                        if len(line) < 100 and not any(x in line for x in ['MBBS', 'FCPS', 'Experience', 'Specialist']):
                            details['name'] = line
                            break
            
            # Extract all other fields
            details['qualifications'] = self.extract_all_qualifications(lines)
            details['specialty'] = self.extract_specialty(lines)
            details['experience'] = self.extract_experience(lines)
            details['hospital'], details['location'] = self.extract_hospital_location(lines)
            
            return details
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return None
    
    def save_progress(self):
        """Save current data to CSV"""
        df = pd.DataFrame(self.all_data)
        df.to_csv(self.output_file, index=False, encoding='utf-8-sig')
    
    def run(self):
        """Main scraping process"""
        country_name = {None: "All Countries", 18: "Bangladesh", 103: "India"}
        
        print("=" * 80)
        print("🏥 SASTHYASEBA.COM UNIFIED SCRAPER")
        print("=" * 80)
        print(f"📊 Output file: {self.output_file}")
        print(f"🌍 Country: {country_name.get(self.country_id)}")
        print(f"📄 Total pages: {self.get_total_pages()}")
        print("=" * 80 + "\n")
        
        self.setup_driver()
        self.load_existing_data()
        
        try:
            # PHASE 1: Collect URLs
            print("PHASE 1: Collecting Profile URLs")
            print("=" * 80)
            
            all_urls = []
            total_pages = self.get_total_pages()
            
            for page_num in range(1, total_pages + 1):
                print(f"\n[Page {page_num}/{total_pages}]")
                
                try:
                    urls = self.extract_profile_urls(page_num)
                    all_urls.extend(urls)
                    print(f"      📊 Total new profiles: {len(all_urls)}")
                    
                    if page_num % 50 == 0:
                        print(f"\n      💾 Checkpoint: {len(all_urls)} profiles collected")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"      ⚠️ Error on page {page_num}: {e}")
                    continue
            
            print(f"\n✅ Phase 1 Complete: {len(all_urls)} new profiles to scrape")
            
            if not all_urls:
                print("✅ No new doctors to scrape!")
                return
            
            # PHASE 2: Scrape Profiles
            print("\n" + "=" * 80)
            print("PHASE 2: Scraping Profile Details")
            print("=" * 80)
            
            for idx, url in enumerate(all_urls, 1):
                print(f"\n[{idx}/{len(all_urls)}] {url}")
                
                try:
                    details = self.scrape_profile(url)
                    
                    if details:
                        self.all_data.append(details)
                        print(f"      ✅ {details['name']}")
                        print(f"      📚 {details['qualifications'][:60]}...")
                        print(f"      🏥 {details['hospital']}")
                    
                    # Save every 25 records
                    if idx % 25 == 0:
                        self.save_progress()
                        print(f"\n      💾 Progress saved: {len(self.all_data)} total records")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    continue
            
            # Final save
            self.save_progress()
            
            print("\n" + "=" * 80)
            print("✅ SCRAPING COMPLETE!")
            print("=" * 80)
            print(f"📊 Total records: {len(self.all_data)}")
            print(f"💾 Saved to: {self.output_file}")
            
            # Data quality stats
            df = pd.DataFrame(self.all_data)
            print("\n📈 DATA QUALITY:")
            print(f"   ✅ Name: {(df['name'] != 'N/A').sum()}/{len(df)}")
            print(f"   ✅ Qualifications: {(df['qualifications'] != 'N/A').sum()}/{len(df)}")
            print(f"   ✅ Specialty: {(df['specialty'] != 'N/A').sum()}/{len(df)}")
            print(f"   ✅ Experience: {(df['experience'] != 'N/A').sum()}/{len(df)}")
            print(f"   ✅ Hospital: {(df['hospital'] != 'N/A').sum()}/{len(df)}")
            print(f"   ✅ Location: {(df['location'] != 'N/A').sum()}/{len(df)}")
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user")
            self.save_progress()
            print(f"💾 Saved {len(self.all_data)} records")
        
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.driver.quit()
            print("\n🚪 Driver closed")


if __name__ == "__main__":
    # Usage examples:
    
    # Scrape Bangladesh doctors only
    scraper = SasthyasebaScraper(
        output_file="bangladesh_doctors.csv",
        country_id=18
    )
    scraper.run()
    
    # Scrape India doctors only
    # scraper = SasthyasebaScraper(
    #     output_file="india_doctors.csv", 
    #     country_id=103
    # )
    # scraper.run()
    
    # Scrape all countries
    # scraper = SasthyasebaScraper(
    #     output_file="all_doctors.csv",
    #     country_id=None
    # )
    # scraper.run()