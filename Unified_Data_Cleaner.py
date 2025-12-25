"""
Unified Doctor Data Cleaner
============================
Cleans and standardizes scraped doctor data in one go

Features:
- Removes invalid profiles (BMDC, repeated values)
- Standardizes experience to numeric years
- Cleans and standardizes specialties
- Extracts country from location
- Fills missing data where possible
- Removes duplicates
"""

import pandas as pd
import numpy as np
import re

class DoctorDataCleaner:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.df = None
        
        # Standard specialties list
        self.standard_specialties = [
            "Aesthetic Dermatologist", "Allergy Skin-VD", "Andrologist",
            "Anesthesiologist", "Biochemist", "Cardiac Surgeon", "Cardiologist",
            "Cardiothoracic Surgeon", "Chest Specialist", "Clinical Nutritionist",
            "Colorectal Surgeon", "Cosmetic Dentist", "Cosmetologist",
            "Critical Care Specialist", "Dentist", "Dermatologist", "Dermatosurgeon",
            "Diabetes Specialist", "Diabetologist", "Dietician", "Endocrinologist",
            "Epidemiologist", "Family Medicine Specialist", "Gastroenterologist",
            "General Physician", "General Surgeon", "Geriatrician",
            "Gynecologic Oncologist", "Gynecologist", "Hair Transplant Surgeon",
            "Hematologist", "Hepatobiliary Surgeon", "Hepatologist", "Immunologist",
            "Infertility Specialist", "Internal Medicine", "Internal Medicine Specialist",
            "Interventional Cardiologist", "Laparoscopic Surgeon", "Laparoscopist",
            "Maxillofacial Surgeon", "Medicine Specialist", "Microbiologist",
            "Neonatologist", "Nephrologist", "Neurologist", "Neurosurgeon",
            "Nutritionist", "Obstetrician", "Oncologist", "Ophthalmologist",
            "Orthopedic Surgeon", "Orthopedist", "ENT", "Pain Management Specialist",
            "Pathologist", "Pediatric Cardiologist", "Pediatric Surgeon",
            "Pediatrician", "Physical Medicine", "Physiotherapist", "Plastic Surgeon",
            "Psychiatrist", "Psychologist", "Pulmonologist", "Radiologist",
            "Rheumatologist", "Sexual Medicine Specialist", "Sonologist",
            "Spine Surgeon", "Sports Physician", "Surgeon", "Thoracic Surgeon"
        ]
        
        # Country names for extraction
        self.country_names = [
            'Bangladesh', 'India', 'Pakistan', 'Sri Lanka', 'Nepal',
            'United States', 'USA', 'Canada', 'UK', 'United Kingdom',
            'Australia', 'Singapore', 'Malaysia', 'Thailand'
        ]
    
    def load_data(self):
        """Load CSV data"""
        print(f"📂 Loading data from {self.input_file}...")
        self.df = pd.read_csv(self.input_file)
        print(f"✅ Loaded {len(self.df)} records\n")
        return self
    
    def show_initial_stats(self):
        """Display initial data statistics"""
        print("=" * 80)
        print("📊 INITIAL DATA STATISTICS")
        print("=" * 80)
        print(f"Total records: {len(self.df)}")
        print(f"\nMissing values per column:")
        for col in self.df.columns:
            nan_count = self.df[col].isna().sum()
            if nan_count > 0:
                print(f"  • {col}: {nan_count} ({nan_count/len(self.df)*100:.1f}%)")
        print("\n")
    
    def remove_bmdc_profiles(self):
        """Remove profiles with BMDC-only qualifications"""
        print("🗑️  Removing BMDC-only profiles...")
        initial_count = len(self.df)
        
        bmdc_mask = self.df['qualifications'].astype(str).str.startswith('BMDC')
        self.df = self.df[~bmdc_mask]
        
        removed = initial_count - len(self.df)
        print(f"   Removed {removed} BMDC profiles")
        print(f"   Remaining: {len(self.df)} records\n")
        return self
    
    def remove_repeated_values(self):
        """Remove rows with repeated values across columns"""
        print("🗑️  Removing rows with repeated values...")
        
        def has_repeated_values(row):
            temp_row = row.copy()
            # Exclude certain columns
            for col in ['designation', 'designations']:
                if col in temp_row.index:
                    temp_row = temp_row.drop(col)
            non_nan = temp_row.dropna()
            return len(non_nan) != len(non_nan.unique())
        
        initial_count = len(self.df)
        repeated_mask = self.df.apply(has_repeated_values, axis=1)
        self.df = self.df[~repeated_mask]
        
        removed = initial_count - len(self.df)
        print(f"   Removed {removed} rows with repeated values")
        print(f"   Remaining: {len(self.df)} records\n")
        return self
    
    def clean_experience(self):
        """Convert experience to numeric years"""
        print("🔢 Cleaning experience column...")
        
        if 'experience' in self.df.columns:
            # Rename if needed
            self.df.rename(columns={'experience': 'experience(IN YEARS OVERALL)'}, inplace=True)
        
        exp_col = 'experience(IN YEARS OVERALL)'
        
        if exp_col in self.df.columns:
            # Fill NaN with 1
            self.df[exp_col] = self.df[exp_col].fillna('1')
            
            # Extract numeric part
            self.df[exp_col] = self.df[exp_col].astype(str).str.extract('(\d+)').astype(float)
            
            print(f"   ✅ Converted to numeric years")
            print(f"   Average experience: {self.df[exp_col].mean():.1f} years\n")
        return self
    
    def standardize_specialties(self):
        """Clean and standardize specialty field"""
        print("🏥 Standardizing specialties...")
        
        def clean_specialty(text):
            if not isinstance(text, str) or text == 'N/A':
                return text
            
            # Check against standard list
            for standard in self.standard_specialties:
                if standard.lower() in text.lower():
                    return standard
            
            return text
        
        initial_unique = self.df['specialty'].nunique()
        self.df['specialty'] = self.df['specialty'].apply(clean_specialty)
        final_unique = self.df['specialty'].nunique()
        
        print(f"   Unique specialties: {initial_unique} → {final_unique}")
        print(f"   ✅ Standardized specialties\n")
        return self
    
    def extract_country(self):
        """Extract country from location field"""
        print("🌍 Extracting country from location...")
        
        def find_country(location_text):
            if not isinstance(location_text, str):
                return None
            location_lower = location_text.lower()
            for country in self.country_names:
                if country.lower() in location_lower:
                    return country
            return None
        
        if 'country' not in self.df.columns:
            self.df['country'] = None
        
        self.df['country'] = self.df['location'].apply(find_country)
        
        country_counts = self.df['country'].value_counts()
        print(f"   Countries found:")
        for country, count in country_counts.items():
            print(f"     • {country}: {count}")
        print()
        return self
    
    def filter_countries(self, countries=['Bangladesh', 'India']):
        """Keep only specified countries"""
        print(f"🌍 Filtering for countries: {', '.join(countries)}...")
        
        initial_count = len(self.df)
        self.df = self.df[self.df['country'].isin(countries)]
        
        removed = initial_count - len(self.df)
        print(f"   Removed {removed} records from other countries")
        print(f"   Remaining: {len(self.df)} records\n")
        return self
    
    def remove_duplicates(self):
        """Remove duplicate profiles"""
        print("🗑️  Removing duplicates...")
        
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates(subset=['profile_url'], keep='first')
        
        removed = initial_count - len(self.df)
        if removed > 0:
            print(f"   Removed {removed} duplicate profiles")
        else:
            print(f"   No duplicates found")
        print(f"   Remaining: {len(self.df)} records\n")
        return self
    
    def drop_missing_critical(self):
        """Drop rows missing critical fields"""
        print("🗑️  Dropping rows with missing critical data...")
        
        initial_count = len(self.df)
        
        # Drop if missing hospital
        self.df = self.df.dropna(subset=['hospital'])
        print(f"   After removing missing hospital: {len(self.df)} records")
        
        # Drop if missing location
        self.df = self.df.dropna(subset=['location'])
        print(f"   After removing missing location: {len(self.df)} records")
        
        # Drop if missing specialty
        self.df = self.df.dropna(subset=['specialty'])
        print(f"   After removing missing specialty: {len(self.df)} records")
        
        removed = initial_count - len(self.df)
        print(f"   Total removed: {removed}\n")
        return self
    
    def clean_qualifications(self):
        """Clean qualifications field"""
        print("📚 Cleaning qualifications...")
        
        # Remove unwanted prefixes
        unwanted = "Domiciliary Services, Find Doctor, "
        self.df['qualifications'] = self.df['qualifications'].str.replace(unwanted, '', regex=False)
        
        print(f"   ✅ Cleaned qualifications\n")
        return self
    
    def reset_index(self):
        """Reset dataframe index"""
        self.df = self.df.reset_index(drop=True)
        return self
    
    def save(self):
        """Save cleaned data"""
        print(f"💾 Saving to {self.output_file}...")
        self.df.to_csv(self.output_file, index=False, encoding='utf-8-sig')
        print(f"✅ Saved {len(self.df)} records\n")
        return self
    
    def show_final_stats(self):
        """Display final statistics"""
        print("=" * 80)
        print("📊 FINAL DATA STATISTICS")
        print("=" * 80)
        print(f"Total records: {len(self.df)}")
        print(f"\nData completeness:")
        for col in self.df.columns:
            if col == 'profile_url':
                continue
            complete = (self.df[col] != 'N/A').sum() if col != 'experience(IN YEARS OVERALL)' else (~self.df[col].isna()).sum()
            print(f"  • {col}: {complete}/{len(self.df)} ({complete/len(self.df)*100:.1f}%)")
        
        if 'country' in self.df.columns:
            print(f"\nCountry distribution:")
            for country, count in self.df['country'].value_counts().items():
                print(f"  • {country}: {count}")
        
        if 'specialty' in self.df.columns:
            print(f"\nUnique specialties: {self.df['specialty'].nunique()}")
        
        print("=" * 80 + "\n")
    
    def run_full_cleaning(self, filter_countries=True):
        """Run complete cleaning pipeline"""
        print("=" * 80)
        print("🧹 DOCTOR DATA CLEANING PIPELINE")
        print("=" * 80 + "\n")
        
        (self.load_data()
             .show_initial_stats()
             .remove_bmdc_profiles()
             .remove_repeated_values()
             .clean_qualifications()
             .clean_experience()
             .standardize_specialties()
             .extract_country())
        
        if filter_countries:
            self.filter_countries(['Bangladesh', 'India'])
        
        (self.remove_duplicates()
             .drop_missing_critical()
             .reset_index()
             .save()
             .show_final_stats())
        
        print("✅ CLEANING COMPLETE!\n")
        return self.df


if __name__ == "__main__":
    # Example usage
    cleaner = DoctorDataCleaner(
        input_file="doctors_data.csv",
        output_file="doctors_cleaned.csv"
    )
    
    cleaned_df = cleaner.run_full_cleaning(filter_countries=True)
    
    # Optional: Further manual inspection
    print("Sample of cleaned data:")
    print(cleaned_df.head())