# 🏥 Doctor Data Scraping & Analysis Project

A comprehensive data scraping and cleaning pipeline for extracting and analyzing doctor profiles from Sasthyaseba.com, with a focus on medical professionals in Bangladesh and India.

## 📊 Project Overview

This project collects, cleans, and analyzes data on doctors from South Asia, providing insights into medical specialization availability, experience distribution, and healthcare provider information. The final analysis is visualized through an interactive Tableau dashboard.

**[View Live Tableau Dashboard →](https://public.tableau.com/app/profile/shihab.musa/viz/MedicalSpecializationAvailabilityAnalysisofBangladeshiandIndianDoctors/Dashboard2?publish=yes)**

## 🚀 Features

### Web Scraping (`Unified_Sasthyaseba_Scraper.py`)
- **Country-Specific Scraping**: Target Bangladesh (310 pages), India (45 pages), or all countries (355 pages)
- **Intelligent Data Extraction**: Automatically extracts name, qualifications, specialty, experience, hospital, and location
- **Smart Qualification Detection**: Captures ALL degrees and certifications (MBBS, FCPS, MD, MS, etc.)
- **Resume Capability**: Avoids re-scraping existing profiles
- **Auto-Save**: Progress saved every 25 records to prevent data loss
- **Error Handling**: Continues scraping even if individual profiles fail

### Data Cleaning (`Unified_Data_Cleaner.py`)
- **Quality Filtering**: Removes invalid profiles (BMDC-only, repeated values)
- **Data Standardization**: 
  - Converts experience to numeric years
  - Standardizes 60+ medical specialties
  - Extracts country from location data
- **Completeness Checks**: Drops records missing critical fields (hospital, location, specialty)
- **Duplicate Removal**: Ensures unique doctor profiles
- **Statistical Reporting**: Before/after cleaning metrics

## 📁 Project Structure

```
doctor-data-project/
│
├── Unified_Sasthyaseba_Scraper.py   # Web scraping script
├── Unified_Data_Cleaner.py          # Data cleaning pipeline
├── doctors_data.csv                  # Raw scraped data
├── doctors_cleaned.csv               # Cleaned dataset
└── README.md                         # This file
```

## 🛠️ Installation

### Prerequisites
- Python 3.7+
- Google Chrome browser
- ChromeDriver (compatible with your Chrome version)

### Required Libraries
```bash
pip install selenium pandas numpy
```

## 📖 Usage

### 1. Scraping Doctor Data

```python
from Unified_Sasthyaseba_Scraper import SasthyasebaScraper

# Scrape Bangladesh doctors only (recommended)
scraper = SasthyasebaScraper(
    output_file="bangladesh_doctors.csv",
    country_id=18  # 18=Bangladesh, 103=India, None=All
)
scraper.run()
```

**Country IDs:**
- `18` - Bangladesh (310 pages, ~6,000+ doctors)
- `103` - India (45 pages, ~900+ doctors)
- `None` - All countries (355 pages)

### 2. Cleaning the Data

```python
from Unified_Data_Cleaner import DoctorDataCleaner

# Clean the scraped data
cleaner = DoctorDataCleaner(
    input_file="doctors_data.csv",
    output_file="doctors_cleaned.csv"
)

cleaned_df = cleaner.run_full_cleaning(filter_countries=True)
```

## 📊 Data Schema

### Output Fields

| Field | Description | Example |
|-------|-------------|---------|
| `profile_url` | Doctor's profile URL | `https://sasthyaseba.com/doctors/...` |
| `name` | Full name with title | `Dr. Ahmed Rahman` |
| `qualifications` | All degrees and certifications | `MBBS, FCPS (Medicine), MD` |
| `specialty` | Medical specialization | `Cardiologist` |
| `experience(IN YEARS OVERALL)` | Years of practice | `15` |
| `hospital` | Primary affiliated hospital | `Dhaka Medical College Hospital` |
| `location` | Hospital address | `Dhaka, Bangladesh` |
| `country` | Extracted country | `Bangladesh` |

## 🧹 Data Cleaning Process

The cleaning pipeline performs these operations in sequence:

1. **Load Data** - Imports raw CSV
2. **Remove BMDC Profiles** - Filters out incomplete profiles
3. **Remove Repeated Values** - Eliminates corrupted data
4. **Clean Qualifications** - Removes unwanted prefixes
5. **Standardize Experience** - Converts to numeric years
6. **Standardize Specialties** - Maps to 60+ standard categories
7. **Extract Country** - Parses location for country
8. **Filter Countries** - Keeps only Bangladesh & India (optional)
9. **Remove Duplicates** - Ensures unique profiles
10. **Drop Missing Critical Data** - Removes incomplete records
11. **Save & Report** - Exports cleaned data with statistics

## 📈 Analysis & Visualization

The cleaned data powers an interactive Tableau dashboard featuring:

- **Specialization Distribution**: Compare medical specialties across countries
- **Experience Analysis**: Average years of experience by specialty
- **Geographic Coverage**: Hospital and doctor distribution by location
- **Data Quality Metrics**: Completeness and coverage statistics

**[Explore the Dashboard →](https://public.tableau.com/app/profile/shihab.musa/viz/MedicalSpecializationAvailabilityAnalysisofBangladeshiandIndianDoctors/Dashboard2?publish=yes)**

## ⚙️ Configuration

### Scraper Settings

Modify these parameters in `Unified_Sasthyaseba_Scraper.py`:

```python
# Adjust scraping delay (seconds)
time.sleep(2)  # Between pages
time.sleep(0.5)  # Between profiles

# Change save frequency
if idx % 25 == 0:  # Save every 25 records
    self.save_progress()
```

### Cleaner Settings

Customize specialty standardization in `Unified_Data_Cleaner.py`:

```python
self.standard_specialties = [
    "Cardiologist", "Neurologist", "Dermatologist",
    # Add more specialties here
]

self.country_names = [
    'Bangladesh', 'India', 'Pakistan',
    # Add more countries here
]
```

## 🔧 Troubleshooting

### Common Issues

**Scraper not finding doctors:**
- Ensure ChromeDriver version matches your Chrome browser
- Check internet connection
- Verify website structure hasn't changed

**Cleaning removes too many records:**
- Adjust `filter_countries` parameter to `False`
- Modify `drop_missing_critical()` to be less strict
- Check initial data quality

**Encoding errors in CSV:**
- Files use UTF-8 with BOM (`utf-8-sig`)
- Open in Excel or modern text editors

## 📊 Sample Statistics

Based on recent scraping runs:

- **Total Doctors Scraped**: ~7,000+
- **Bangladesh**: ~6,000 profiles (310 pages)
- **India**: ~900 profiles (45 pages)
- **Data Completeness**: 85-95% across fields
- **Unique Specialties**: 60+ standardized categories

## 🤝 Contributing

Improvements welcome! Areas for enhancement:

- Add more specialty standardization rules
- Implement parallel scraping for faster collection
- Add data validation and quality checks
- Expand country coverage
- Create automated reporting

## ⚠️ Disclaimer

This tool is for educational and research purposes. Please:
- Respect website terms of service
- Use reasonable scraping delays
- Don't overload servers
- Verify data accuracy before use

## 📝 License

This project is open source. Use responsibly and ethically.

## 📧 Contact

For questions or collaboration:
- **Author**: Shihab Musa
- **Tableau Profile**: [View Profile](https://public.tableau.com/app/profile/shihab.musa)

---

**Made with ❤️ for healthcare data transparency**