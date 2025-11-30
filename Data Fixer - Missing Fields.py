"""
Sasthyaseba.com Data Fixer
===========================
Fixes missing specialty, hospital, and location fields in scraped data

Features:
- Re-visits profiles with missing data
- Improved extraction algorithms
- Processes only records with N/A values
- Progress saving every 50 records
- Interrupt-safe

"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def setup_driver():
    """Initialize Chrome driver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(options=options)
    return driver

def extract_missing_fields(driver, profile_url):
    """Extract specialty, hospital, and location from a doctor's profile"""
    try:
        driver.get(profile_url)
        time.sleep(2)
        
        # Scroll to load content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # Get page text
        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
        
        result = {
            'specialty': 'N/A',
            'hospital': 'N/A',
            'location': 'N/A'
        }
        
        # ========== EXTRACT SPECIALTY ==========
        specialty_keywords = [
            # -ologist types
            'Rheumatologist', 'Cardiologist', 'Neurologist', 'Dermatologist',
            'Nephrologist', 'Oncologist', 'Endocrinologist', 'Gastroenterologist',
            'Pulmonologist', 'Hematologist', 'Radiologist', 'Pathologist',
            'Anesthesiologist', 'Ophthalmologist', 'Neonatologist', 'Gynecologist',
            'Urologist', 'Immunologist',
            
            # Specialist types
            'Specialist', 'Medicine Specialist', 'Chest Specialist',
            'Respiratory Specialist', 'Critical Care Medicine Specialist',
            'Diabetes Specialist', 'Family Medicine Specialist',
            
            # Surgeon types
            'Surgeon', 'General Surgeon', 'Neurosurgeon', 'Cardiovascular Surgeon',
            'Thoracic Surgeon', 'Vascular Surgeon', 'Plastic Surgeon',
            'Colorectal Surgeon', 'Hepatobiliary Surgeon', 'Orthopedic Surgeon',
            'Maxillofacial Surgeon', 'Dental Surgeon',
            
            # Other types
            'Pediatrician', 'Obstetrician', 'Psychiatrist', 'Dentist', 'ENT'
        ]
        
        # Method 1: Look in first 15 lines
        for line in lines[:15]:
            if any(skip in line for skip in [
                'MBBS', 'FCPS', 'BCS', 'MD', 'MS', 'Years', 'Hospital',
                'Dhaka', 'Bangladesh', 'Book', 'Get', 'Find', 'View', 'Doctor'
            ]):
                continue
            
            line_lower = line.lower()
            for keyword in specialty_keywords:
                if keyword.lower() == line_lower:
                    result['specialty'] = line
                    break
                elif keyword.lower() in line_lower and len(line) < 100:
                    if not any(qual in line for qual in ['MBBS', 'FCPS', 'MD', 'MS']):
                        result['specialty'] = line
                        break
            if result['specialty'] != 'N/A':
                break
        
        # Method 2: Look for single-word specialties
        if result['specialty'] == 'N/A':
            for line in lines[:20]:
                if (5 < len(line) < 40 and line[0].isupper()):
                    if any(line.endswith(suffix) for suffix in [
                        'ologist', 'logist', 'ist', 'ian', 'ician',
                        'Specialist', 'Surgeon', 'Consultant'
                    ]):
                        if not any(skip in line for skip in ['MBBS', 'FCPS', 'Years', 'Hospital']):
                            result['specialty'] = line
                            break
        
        # ========== EXTRACT HOSPITAL & LOCATION ==========
        hospitals = []
        locations = []
        
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['Hospital', 'Medical Centre', 'Medical Center',
                                                    'Clinic', 'Healthcare', 'Medical College']):
                # STRICT EXCLUSIONS
                if (len(line) < 200 and
                    'Find Hospital' not in line and
                    'Get Direction' not in line and
                    'Book Appointment' not in line and
                    'Availability' not in line and
                    'Work Experience' not in line and
                    'Education' not in line and
                    'Locations' not in line and
                    'Book appointment' not in line and
                    'View all' not in line and
                    'Info' not in line):
                    
                    # Must be a real hospital name
                    if (line not in hospitals and
                        len(line) > 5 and
                        not line.startswith(('Book', 'View', 'Find', 'Get'))):
                        
                        hospitals.append(line)
                        
                        # Look for location in next few lines
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j]
                            
                            # Check if it's a location/address
                            if (len(next_line) > 15 and
                                'Get Direction' not in next_line and
                                'Book Appointment' not in next_line and
                                'Availability' not in next_line and
                                'Find Hospital' not in next_line and
                                'Info' not in next_line and
                                any(loc in next_line for loc in [',', 'Road', 'Rd', 'Dhaka', 'Bangladesh',
                                                                  'No.', 'Street', 'Avenue', 'Chittagong',
                                                                  'Sylhet', 'Rajshahi', 'Khulna', 'Barisal',
                                                                  'City Bazar', 'Building', 'Circular'])):
                                
                                if next_line not in locations:
                                    locations.append(next_line)
                                break
                        
                        # Only get first valid hospital/location pair
                        if len(hospitals) >= 1:
                            break
        
        if hospitals:
            result['hospital'] = hospitals[0]
        if locations:
            result['location'] = locations[0]
        
        return result
        
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return {'specialty': 'N/A', 'hospital': 'N/A', 'location': 'N/A'}

def main():
    """Fix missing fields in doctor data"""
    input_file = 'sasthyaseba_doctors.csv'
    output_file = 'sasthyaseba_doctors_fixed.csv'
    
    print("=" * 80)
    print("🔧 SASTHYASEBA.COM DATA FIXER")
    print("=" * 80)
    print(f"📂 Input: {input_file}")
    print(f"💾 Output: {output_file}")
    print("=" * 80 + "\n")
    
    # Read CSV
    try:
        df = pd.read_csv(input_file)
        print(f"✅ Loaded {len(df)} total records\n")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return
    
    # Identify records needing fixes
    needs_specialty = df['specialty'].isna() | (df['specialty'] == 'N/A')
    needs_hospital = df['hospital'].isna() | (df['hospital'] == 'N/A')
    needs_location = df['location'].isna() | (df['location'] == 'N/A')
    
    needs_fixing = needs_specialty | needs_hospital | needs_location
    records_to_fix = df[needs_fixing]
    
    print("📊 RECORDS NEEDING FIXES:")
    print(f"   🔍 Missing specialty: {needs_specialty.sum()}")
    print(f"   🏥 Missing hospital: {needs_hospital.sum()}")
    print(f"   📍 Missing location: {needs_location.sum()}")
    print(f"   📋 Total records to process: {len(records_to_fix)}")
    print("=" * 80 + "\n")
    
    if len(records_to_fix) == 0:
        print("✅ No records need fixing!")
        return
    
    driver = setup_driver()
    
    try:
        fixed_counts = {'specialty': 0, 'hospital': 0, 'location': 0}
        
        for idx, row in records_to_fix.iterrows():
            print(f"\n[{fixed_counts['specialty'] + fixed_counts['hospital'] + 1}/{len(records_to_fix)}] {row['name']}")
            print(f"   Profile: {row['profile_url']}")
            print(f"   Needs: ", end="")
            if pd.isna(row['specialty']) or row['specialty'] == 'N/A':
                print("specialty ", end="")
            if pd.isna(row['hospital']) or row['hospital'] == 'N/A':
                print("hospital ", end="")
            if pd.isna(row['location']) or row['location'] == 'N/A':
                print("location", end="")
            print()
            
            try:
                # Extract missing fields
                extracted = extract_missing_fields(driver, row['profile_url'])
                
                # Update only if we found better data
                if (pd.isna(row['specialty']) or row['specialty'] == 'N/A') and extracted['specialty'] != 'N/A':
                    df.at[idx, 'specialty'] = extracted['specialty']
                    print(f"   ✅ Specialty: {extracted['specialty']}")
                    fixed_counts['specialty'] += 1
                
                if (pd.isna(row['hospital']) or row['hospital'] == 'N/A') and extracted['hospital'] != 'N/A':
                    df.at[idx, 'hospital'] = extracted['hospital']
                    print(f"   ✅ Hospital: {extracted['hospital']}")
                    fixed_counts['hospital'] += 1
                
                if (pd.isna(row['location']) or row['location'] == 'N/A') and extracted['location'] != 'N/A':
                    df.at[idx, 'location'] = extracted['location']
                    print(f"   ✅ Location: {extracted['location']}")
                    fixed_counts['location'] += 1
                
                # Save progress every 50 records
                if (fixed_counts['specialty'] + fixed_counts['hospital']) % 50 == 0:
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                    print(f"\n   💾 Progress saved")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        # Final save
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print("\n" + "=" * 80)
        print("✅ FIXING COMPLETE!")
        print("=" * 80)
        print(f"📊 FIXES APPLIED:")
        print(f"   ✅ Fixed specialty: {fixed_counts['specialty']}/{needs_specialty.sum()}")
        print(f"   ✅ Fixed hospital: {fixed_counts['hospital']}/{needs_hospital.sum()}")
        print(f"   ✅ Fixed location: {fixed_counts['location']}/{needs_location.sum()}")
        print(f"💾 Results saved to: {output_file}")
        
        # Show remaining issues
        final_df = pd.read_csv(output_file)
        still_missing_specialty = (final_df['specialty'].isna() | (final_df['specialty'] == 'N/A')).sum()
        still_missing_hospital = (final_df['hospital'].isna() | (final_df['hospital'] == 'N/A')).sum()
        still_missing_location = (final_df['location'].isna() | (final_df['location'] == 'N/A')).sum()
        
        print("\n📈 REMAINING ISSUES:")
        print(f"   ⚠️ Still missing specialty: {still_missing_specialty}")
        print(f"   ⚠️ Still missing hospital: {still_missing_hospital}")
        print(f"   ⚠️ Still missing location: {still_missing_location}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Fixing interrupted by user")
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"💾 Saved partial results")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("\n🔚 Driver closed")

if __name__ == "__main__":
    main()