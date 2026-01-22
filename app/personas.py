"""
Persona definitions and configurations for WorkbenchIQ.

This module defines different industry personas (Underwriting, Claims, Mortgage)
with their specific field schemas, prompts, and analyzer configurations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class PersonaType(str, Enum):
    """Available persona types in WorkbenchIQ."""
    UNDERWRITING = "underwriting"
    LIFE_HEALTH_CLAIMS = "life_health_claims"
    AUTOMOTIVE_CLAIMS = "automotive_claims"  # New multimodal automotive claims persona
    MORTGAGE = "mortgage"
    # Legacy aliases for backward compatibility
    CLAIMS = "claims"  # Maps to life_health_claims
    PROPERTY_CASUALTY_CLAIMS = "property_casualty_claims"  # Alias for automotive_claims


@dataclass
class PersonaConfig:
    """Configuration for a specific persona."""
    id: str
    name: str
    description: str
    icon: str  # Emoji or icon identifier
    color: str  # Primary color for UI theming
    field_schema: Dict[str, Any]
    default_prompts: Dict[str, Dict[str, str]]
    custom_analyzer_id: str
    enabled: bool = True  # Whether this persona is fully implemented
    # Multimodal analyzer support (for automotive claims)
    image_analyzer_id: Optional[str] = None
    video_analyzer_id: Optional[str] = None


# =============================================================================
# UNDERWRITING PERSONA CONFIGURATION
# =============================================================================

UNDERWRITING_FIELD_SCHEMA = {
    "name": "UnderwritingFields",
    "fields": {
        # ===== Personal Information =====
        "ApplicantName": {
            "type": "string",
            "description": "Full legal name of the insurance applicant, typically found at the top of the application form in Section 1 or Personal Details section. May be labeled as 'Name', 'Applicant Name', 'Proposed Insured', 'Insured Name', or 'Full Name'. Format is usually FirstName MiddleName LastName or LastName, FirstName.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "DateOfBirth": {
            "type": "date",
            "description": "Applicant's date of birth, typically found near the top of the application in the personal information section. May be labeled as 'Date of Birth', 'DOB', 'Birth Date', or 'D.O.B.'. Accepts formats like MM/DD/YYYY, DD-MM-YYYY, or Month DD, YYYY.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Age": {
            "type": "number",
            "description": "Current age of the applicant in years, typically found in the personal details section. May be labeled as 'Age', 'Current Age', 'Age at Application', or 'Age Last Birthday'. Should be a whole number.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Gender": {
            "type": "string",
            "description": "Biological sex or gender of the applicant, typically found in personal information section near name and date of birth. May be labeled as 'Sex', 'Gender', 'M/F', or shown as checkboxes. Common values: Male, Female, M, F, or Other.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Nationality": {
            "type": "string",
            "description": "Nationality or citizenship of the applicant, often found in personal or residency information section. May be labeled as 'Nationality', 'Citizenship', 'Country of Citizenship', or 'Citizen of'. Extract the country name.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Residency": {
            "type": "string",
            "description": "Current country, province/state, or city of residence, typically found in contact information or address section. May be labeled as 'Residence', 'Country of Residence', 'Residential Address', 'Province/State', or 'Place of Residence'. Include city and country/state if available.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Occupation": {
            "type": "string",
            "description": "Current occupation, job title, or profession of the applicant, typically found in occupation/employment section. May be labeled as 'Occupation', 'Profession', 'Employment', 'Job Title', 'Current Position', or 'Nature of Work'. Extract the specific job title or description.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Height": {
            "type": "string",
            "description": "Height of the applicant, typically found in physical examination or medical information section. May be labeled as 'Height', 'Ht.', or 'Stature'. Include units such as feet/inches (e.g., 5'10\"), centimeters (e.g., 178 cm), or meters.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Weight": {
            "type": "string",
            "description": "Body weight of the applicant, typically found in physical examination section near height. May be labeled as 'Weight', 'Wt.', 'Body Weight', or 'Current Weight'. Include units such as pounds (lb), kilograms (kg), or lbs.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Policy Information =====
        "PolicyProduct": {
            "type": "string",
            "description": "Name or type of the insurance product being applied for, typically found at the top of the application or in product selection section. May be labeled as 'Policy Type', 'Product Name', 'Plan Name', 'Insurance Product', 'Coverage Type', or 'Policy Applied For'. Examples: Term Life, Whole Life, Universal Life, Critical Illness.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "CoverageAmount": {
            "type": "string",
            "description": "Total sum insured or face amount of coverage requested, typically found in policy details section near product name. May be labeled as 'Coverage Amount', 'Sum Insured', 'Face Amount', 'Death Benefit', 'Amount of Insurance', or 'Coverage'. Include currency symbol (e.g., $500,000, CAD 1,000,000).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PremiumAmount": {
            "type": "string",
            "description": "Premium amount to be paid, typically found in policy details or premium calculation section. May be labeled as 'Premium', 'Monthly Premium', 'Annual Premium', 'Premium Amount', or 'Payment Amount'. Include currency and payment frequency (e.g., $150/month, $1,800 annually).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "RatingClass": {
            "type": "string",
            "description": "Underwriting risk classification or rating class assigned, typically found in underwriting decision or rating section. May be labeled as 'Rating', 'Risk Class', 'Rating Class', 'Classification', 'Underwriting Class', or 'Health Rating'. Common values: Preferred Plus, Preferred, Standard Plus, Standard, Substandard, Table Rating (A-J).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Family History =====
        "FamilyHistory": {
            "type": "array",
            "description": "Family medical history information, typically found in family history section or medical questionnaire. May be labeled as 'Family History', 'Family Medical History', 'History of Parents/Siblings', or 'Hereditary Conditions'.",
            "items": {
                "type": "object",
                "properties": {
                    "relationship": {
                        "type": "string",
                        "description": "Relationship to applicant (Father, Mother, Brother, Sister, Paternal Grandfather, etc.)"
                    },
                    "condition": {
                        "type": "string",
                        "description": "Medical condition or cause of death (Heart Disease, Cancer, Diabetes, Stroke, etc.)"
                    },
                    "ageAtDiagnosis": {
                        "type": "string",
                        "description": "Age when condition was diagnosed or age at death"
                    },
                    "livingStatus": {
                        "type": "string",
                        "description": "Living or Deceased"
                    }
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "FamilyHistorySummary": {
            "type": "string",
            "description": "Summary of family medical history in text format, found in section 2 (Family history) or family history questionnaire. Include for each family member: relationship (Father, Mother, Brother, Sister), current age or age at death, state of health or cause of death, and any hereditary conditions (heart disease, cancer, diabetes, kidney disease, mental illness, neurological conditions). Format as semicolon-separated entries like 'Father: Age at death 65, Cause: heart disease; Mother: Age 70, Living, Healthy'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Blood Pressure =====
        "BloodPressureReadings": {
            "type": "array",
            "description": "Blood pressure measurements, typically found in examination results or vital signs section. May be labeled as 'Blood Pressure', 'BP', 'B/P', 'Systolic/Diastolic', or 'Pressure'.",
            "items": {
                "type": "object",
                "properties": {
                    "systolic": {
                        "type": "number",
                        "description": "Systolic blood pressure (top number, typically 90-140)"
                    },
                    "diastolic": {
                        "type": "number",
                        "description": "Diastolic blood pressure (bottom number, typically 60-90)"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date and/or time of reading if available"
                    },
                    "position": {
                        "type": "string",
                        "description": "Position during reading (Sitting, Standing, Supine) if specified"
                    }
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "HypertensionDiagnosis": {
            "type": "string",
            "description": "Diagnosis or history of high blood pressure/hypertension, typically found in medical history section. May be labeled as 'Hypertension', 'High Blood Pressure', 'HTN', 'Elevated BP', or 'Blood Pressure Condition'. Include diagnosis date, duration (e.g., 'diagnosed 2019'), treatment details, and medication names if mentioned.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Cholesterol / Lipid Panel =====
        "LipidPanelResults": {
            "type": "object",
            "description": "Lipid panel or cholesterol test results, typically found in laboratory results or blood test section. May be labeled as 'Lipid Profile', 'Cholesterol Panel', 'Lipid Test', 'Blood Lipids', or 'Cholesterol Results'.",
            "properties": {
                "totalCholesterol": {
                    "type": "string",
                    "description": "Total cholesterol value with units (e.g., 200 mg/dL, 5.2 mmol/L)"
                },
                "ldl": {
                    "type": "string",
                    "description": "LDL (bad cholesterol) value with units. May be labeled 'LDL', 'LDL-C', or 'Low Density Lipoprotein'"
                },
                "hdl": {
                    "type": "string",
                    "description": "HDL (good cholesterol) value with units. May be labeled 'HDL', 'HDL-C', or 'High Density Lipoprotein'"
                },
                "triglycerides": {
                    "type": "string",
                    "description": "Triglycerides value with units. May be labeled 'Triglycerides', 'TG', or 'TRIG'"
                },
                "testDate": {
                    "type": "string",
                    "description": "Date when lipid panel was performed"
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "CholesterolMedications": {
            "type": "array",
            "description": "Medications for cholesterol management, typically found in current medications or treatment section. May be labeled as 'Cholesterol Medications', 'Lipid-lowering drugs', 'Statins', or within general medication list.",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Medication name (e.g., Atorvastatin, Lipitor, Crestor, Simvastatin)"
                    },
                    "dosage": {
                        "type": "string",
                        "description": "Dosage strength and frequency (e.g., 20mg daily, 40mg once daily)"
                    }
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Current Medications =====
        "CurrentMedications": {
            "type": "array",
            "description": "All current medications being taken by the applicant, typically found in medications section or medical history. May be labeled as 'Current Medications', 'Prescriptions', 'Medication List', 'Drugs Currently Taking', or 'Present Medications'.",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Medication name (brand or generic)"
                    },
                    "dosage": {
                        "type": "string",
                        "description": "Dosage strength and frequency (e.g., 10mg twice daily, 50mg as needed)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Medical condition or reason for taking (e.g., high blood pressure, diabetes, pain)"
                    },
                    "startDate": {
                        "type": "string",
                        "description": "When medication was started, if available"
                    }
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "CurrentMedicationsList": {
            "type": "string",
            "description": "Summary list of all current medications in text format, found in medication sections, treatment records, or question 7. Include for each medication: name (brand or generic), dosage, frequency, and condition being treated. Format as semicolon-separated entries like 'Metformin 500mg twice daily for diabetes; Lisinopril 10mg daily for hypertension'. May be labeled as 'Current Medications', 'Prescriptions', 'Medication List', or 'Drugs Currently Taking'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Medical Conditions Summary =====
        "MedicalConditionsSummary": {
            "type": "string",
            "description": "Summary of all disclosed medical conditions, diagnoses, and health issues throughout the document. Extract information from medical history section (question 3), physician statements, examination findings, and questionnaires. Include: condition name, diagnosis date or duration, current status (resolved/ongoing/chronic), treatments received, and outcomes. Format as semicolon-separated entries. May be labeled as 'Medical History', 'Health Conditions', 'Illnesses', 'Diagnoses', or found in affirmative answers section.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Diagnostic Tests =====
        "DiagnosticTests": {
            "type": "array",
            "description": "Diagnostic procedures and tests performed, typically found in medical history, test results, or examination sections. May be labeled as 'Tests', 'Diagnostic Procedures', 'Investigations', 'Medical Tests', or 'Examinations'.",
            "items": {
                "type": "object",
                "properties": {
                    "testType": {
                        "type": "string",
                        "description": "Type of test (ECG/EKG, Echocardiogram, Stress Test, X-Ray, CT Scan, MRI, Ultrasound, Blood Test, Biopsy)"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date when test was performed"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Medical reason or symptoms prompting the test"
                    },
                    "result": {
                        "type": "string",
                        "description": "Test outcome or findings (Normal, Abnormal, specific findings)"
                    }
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "DiagnosticTestsSummary": {
            "type": "string",
            "description": "Summary of diagnostic procedures and tests performed, found in section 21 (Diagnostic Tests), question 6c, or scattered in medical history. Include: test type (ECG/EKG, Echocardiogram, Mammogram, Ultrasound, X-Ray, CT Scan, MRI, Blood Test), date performed, reason/indication, and result/finding. Format as semicolon-separated entries. May be labeled as 'Tests', 'Diagnostic Procedures', 'Investigations', or 'Medical Tests'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Surgeries and Hospitalizations =====
        "SurgeriesAndHospitalizations": {
            "type": "array",
            "description": "Past surgical procedures and hospital admissions, typically found in medical history or surgical history section. May be labeled as 'Surgeries', 'Operations', 'Surgical History', 'Hospitalizations', 'Hospital Admissions', or 'Procedures'.",
            "items": {
                "type": "object",
                "properties": {
                    "procedure": {
                        "type": "string",
                        "description": "Name of surgery or reason for hospitalization"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date or year of procedure/admission"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Medical reason or diagnosis requiring procedure"
                    },
                    "outcome": {
                        "type": "string",
                        "description": "Result or recovery status (Fully recovered, Complications, Ongoing treatment)"
                    }
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Lifestyle - Tobacco =====
        "SmokingStatus": {
            "type": "string",
            "description": "Tobacco and smoking history, typically found in lifestyle habits or tobacco use section. May be labeled as 'Smoking', 'Tobacco Use', 'Cigarette Use', 'Smoker', or 'Nicotine Use'. Indicate status: Non-smoker (never smoked), Ex-smoker/Former smoker (include quit date if available, e.g., 'quit 2020'), or Current smoker (include type such as cigarettes/cigars/pipe/chewing tobacco and quantity per day/week).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Lifestyle - Alcohol =====
        "AlcoholUse": {
            "type": "string",
            "description": "Alcohol consumption habits, typically found in lifestyle or substance use section. May be labeled as 'Alcohol Use', 'Alcohol Consumption', 'Drinking Habits', 'Alcoholic Beverages', or 'Social Drinking'. Include frequency (daily/weekly/monthly/occasional/none), type of beverage (beer/wine/spirits), and quantity (drinks per day/week, e.g., '2 beers per week', '1 glass wine daily').",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Lifestyle - Drug Use =====
        "DrugUse": {
            "type": "string",
            "description": "History of recreational or illegal drug use, typically found in lifestyle or substance abuse section. May be labeled as 'Drug Use', 'Substance Abuse', 'Recreational Drugs', 'Narcotics Use', or 'Controlled Substances'. Include type of substance, frequency, dates of use, and whether past or current. If none, may state 'No' or 'None'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Existing Policies =====
        "ExistingPoliciesSummary": {
            "type": "string",
            "description": "Summary of all existing life insurance policies with the same or other insurers, found in existing insurance section and replacement/disclosure forms. May be labeled as 'Existing Insurance', 'Current Policies', 'Insurance in Force', or 'Other Coverage'. Include: insurance company name, policy type/product, coverage amount/face value, policy status (active/lapsed/terminated), issue date, and any claims history or lapses. Format as semicolon-separated entries.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Physician Information =====
        "FamilyPhysician": {
            "type": "string",
            "description": "Primary care physician or family doctor information, typically found in physician information or medical attendant section. May be labeled as 'Family Doctor', 'Primary Physician', 'Personal Physician', 'Attending Physician', or 'Regular Doctor'. Include: full name (Dr. FirstName LastName), clinic/practice name, phone number, complete address (street, city, state/province), date of last visit, and reason for last visit if mentioned.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Administrative Fields =====
        "ApplicationDate": {
            "type": "date",
            "description": "Date when the application was signed, submitted, or completed, typically found at bottom of application near signature section or in administrative header. May be labeled as 'Application Date', 'Date of Application', 'Date Signed', 'Signature Date', or 'Completion Date'. Accepts formats MM/DD/YYYY, DD-MM-YYYY, or written dates.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ExaminationDate": {
            "type": "date",
            "description": "Date when the medical examination or paramedical exam was conducted, typically found at top or bottom of examination report or medical form. May be labeled as 'Exam Date', 'Examination Date', 'Date of Examination', 'Test Date', or 'Physical Date'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ExaminerName": {
            "type": "string",
            "description": "Name of medical examiner, paramedic, or nurse who conducted the physical examination, typically found on examination report near signature or at bottom of form. May be labeled as 'Examiner', 'Examiner Name', 'Paramedic', 'Medical Examiner', 'Examined By', or 'Nurse Name'. Extract full name.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "AgentName": {
            "type": "string",
            "description": "Name of the insurance agent, broker, or financial advisor handling the application, typically found on first page or in agent information section. May be labeled as 'Agent', 'Agent Name', 'Broker', 'Financial Advisor', 'Writing Agent', 'Producer', or 'Representative'. Include full name and agent code/number if present.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Urinalysis Results =====
        "UrinalysisResults": {
            "type": "object",
            "description": "Urinalysis or urine test results, typically found in laboratory results or examination findings section. May be labeled as 'Urinalysis', 'Urine Test', 'U/A', 'Urine Screen', or 'Urine Analysis'.",
            "properties": {
                "protein": {
                    "type": "string",
                    "description": "Protein level in urine. May show as Negative, Trace, 1+, 2+, 3+, or specific value"
                },
                "glucose": {
                    "type": "string",
                    "description": "Glucose/sugar level in urine. May be labeled 'Glucose', 'Sugar', or 'GLU'. Values: Negative, Trace, or positive findings"
                },
                "blood": {
                    "type": "string",
                    "description": "Blood in urine (hematuria). Values: Negative, Trace, Small, Moderate, Large, or specific value"
                },
                "other": {
                    "type": "string",
                    "description": "Any other urinalysis findings (pH, specific gravity, ketones, leukocytes, etc.)"
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Pulse =====
        "PulseRate": {
            "type": "number",
            "description": "Resting heart rate or pulse measurement in beats per minute, typically found in vital signs or physical examination section. May be labeled as 'Pulse', 'Heart Rate', 'HR', 'Pulse Rate', or 'Beats Per Minute'. Should be a whole number typically between 40-120 bpm.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Risk Factors =====
        "ForeignTravelPlans": {
            "type": "string",
            "description": "Plans for international travel or residence outside home country, typically found in lifestyle, travel, or risk factors section. May be labeled as 'Foreign Travel', 'International Travel', 'Travel Plans', 'Residence Abroad', or 'Extended Travel'. Include destination countries, duration (number of months), purpose (business/leisure/residence), and planned dates. Focus on trips exceeding 2 months or permanent relocation.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "HazardousActivities": {
            "type": "array",
            "description": "Participation in high-risk sports or hazardous activities, typically found in avocations, hobbies, or risk activities section. May be labeled as 'Hazardous Activities', 'Aviation', 'Sports', 'Hobbies', 'Dangerous Activities', or 'High-Risk Pursuits'.",
            "items": {
                "type": "object",
                "properties": {
                    "activity": {
                        "type": "string",
                        "description": "Name of activity (Scuba Diving, Skydiving, Rock Climbing, Racing, Flying, Mountaineering, etc.)"
                    },
                    "frequency": {
                        "type": "string",
                        "description": "How often engaged in (times per year, monthly, weekly)"
                    },
                    "details": {
                        "type": "string",
                        "description": "Additional details like certifications, safety equipment, professional vs amateur"
                    }
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "DrivingViolations": {
            "type": "string",
            "description": "Motor vehicle violations, accidents, or license suspensions within past 5 years, typically found in driving history or motor vehicle section. May be labeled as 'Driving Record', 'Traffic Violations', 'MVR', 'Motor Vehicle History', 'License Suspensions', or 'DUI/DWI'. Include type of violation (speeding, reckless driving, DUI/DWI), date, and any license suspensions or revocations.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "CriminalRecord": {
            "type": "string",
            "description": "Criminal charges, convictions, or pending legal matters, typically found in legal history or background section. May be labeled as 'Criminal Record', 'Criminal History', 'Convictions', 'Legal History', or 'Charges'. Include nature of charge/conviction, date, and disposition (convicted, pending, dismissed).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        }
    }
}

UNDERWRITING_DEFAULT_PROMPTS = {
    "application_summary": {
        "customer_profile": """
You are an expert life insurance underwriter.

Given the full underwriting application converted to Markdown, extract a concise, factual view of the customer profile and application details.

Focus on:
- Name, age, gender, smoking status
- Nationality and residency
- Occupation if present
- Policy illustration (product, coverage amount, premium, rating class)
- Any automated initial decision (risk type, reason, action)

Return STRICT JSON with this exact shape:

{
  "summary": "2–4 sentence narrative of the overall profile.",
  "key_fields": [
    {"label": "Age", "value": "48"},
    {"label": "Smoking status", "value": "Non-smoker"}
  ],
  "risk_assessment": "Low | Moderate | High",
  "underwriting_action": "Free text recommendation for next steps."
}
        """,
        "existing_policies": """
You are an expert life insurance underwriter.

Given the underwriting application in Markdown, summarise all existing policies with the same insurer.

For each existing policy capture:
- Product name
- Sum insured and currency
- Effective date
- Medical rating and exclusions, if any
- Claim history (dates, diagnoses, amounts)
- Whether the policy is active, lapsed, or surrendered

Return STRICT JSON:

{
  "summary": "Short narrative of current in-force cover and history.",
  "policies": [
    {
      "product": "Heirloom (II)",
      "status": "In force",
      "sum_insured": "SGD 500k",
      "effective_date": "2016-10-27",
      "medical_rating": "Standard",
      "exclusions": "MCC excl. severe asthma",
      "claims_summary": "e.g. rib fracture 2022, amount 6,729, claim ratio 1440%"
    }
  ],
  "total_cover_summary": "Short text describing overall cover across policies.",
  "risk_assessment": "Low | Moderate | High",
  "underwriting_action": "Free text recommendation (e.g. accept, load, or request more info)."
}
        """
    },
    "medical_summary": {
        "family_history": """
You are an expert life insurance medical underwriter.

From the Markdown document, extract details on FAMILY MEDICAL HISTORY only.

Look for:
- Conditions in first-degree relatives (e.g. heart disease, cancer, stroke)
- Age at onset and age at death when available
- Relationship to the proposed insured
- Any mention that full details are not available

Return STRICT JSON:

{
  "summary": "2–3 sentence overview of family history relevance.",
  "relatives": [
    {
      "relationship": "Father",
      "condition": "Heart disease",
      "age_at_onset": "Unknown or number",
      "age_at_death": "Over 80",
      "notes": "Any additional comments."
    }
  ],
  "risk_assessment": "Low | Moderate | High",
  "underwriting_action": "Comment on whether further clarification is needed."
}
        """,
        "hypertension": """
You are an expert life insurance medical underwriter.

Using the Markdown, focus ONLY on hypertension / raised blood pressure.

Capture:
- Diagnosis details and duration, if present
- Most recent 3–4 blood pressure readings with dates
- Any medication history (drug, dose, compliance)
- Relevant lab results (lipids, renal function) that affect HTN risk
- Previous underwriting notes or decisions related to blood pressure

Return STRICT JSON:

{
  "summary": "3–5 sentence clinical underwriting summary for hypertension.",
  "bp_readings": [
    {"date": "2024-03-15", "systolic": 134, "diastolic": 81},
    {"date": "2024-03-15", "systolic": 123, "diastolic": 76}
  ],
  "medications": [
    {"name": "Drug name", "dose": "5 mg od", "status": "Current | Past | Never"}
  ],
  "labs": [
    {"name": "Glucose (fasting)", "value": "83 mg/dL", "comment": "Within reference range"}
  ],
  "risk_assessment": "Low | Moderate | High",
  "underwriting_action": "Recommendation (e.g. standard, mild loading, defer, request APS)."
}
        """,
        "high_cholesterol": """
You are an expert life insurance medical underwriter.

Using the Markdown, focus ONLY on dyslipidaemia / hyperlipidaemia / high cholesterol.

Capture:
- Diagnosis details and duration, if available
- Latest lipid profile (Total, LDL, HDL, Triglycerides) with dates and reference ranges
- Any treatment (statins or other agents)
- Previous underwriting decisions linked to cholesterol

Return STRICT JSON:

{
  "summary": "3–4 sentence overview of cholesterol control and trend.",
  "lipid_panels": [
    {
      "date": "2024-03-15",
      "total_cholesterol": "254 mg/dL (high)",
      "ldl": "169 mg/dL",
      "hdl": "64 mg/dL",
      "triglycerides": "109 mg/dL"
    }
  ],
  "medications": [
    {"name": "Statin", "dose": "10 mg nocte", "status": "Current | Past | Never"}
  ],
  "risk_assessment": "Low | Moderate | High",
  "underwriting_action": "Recommendation regarding terms or further information."
}
        """,
        "other_medical_findings": """
You are an expert life insurance medical underwriter.

Using the Markdown, summarise OTHER MEDICAL FINDINGS not already captured in hypertension or cholesterol.

Include:
- Past medical history (e.g. reflux, slipped disc, asthma, surgeries)
- Smoking, alcohol use, and any substance use
- Any investigations (endoscopy, colonoscopy) and their outcomes
- Negative findings that are reassuring (e.g. no AIDS diagnosis)

Return STRICT JSON:

{
  "summary": "High-level narrative of other relevant medical history.",
  "conditions": [
    {
      "name": "Reflux",
      "onset": "2007",
      "status": "Resolved | Ongoing",
      "details": "Omeprazole in 2007, now recovered."
    }
  ],
  "lifestyle": {
    "smoking_status": "Non-smoker | Ex-smoker | Smoker",
    "alcohol": "Description if available",
    "other": "Any other lifestyle notes."
  },
  "risk_assessment": "Low | Moderate | High",
  "underwriting_action": "Notes on whether any additional evidence is required."
}
        """,
        "other_risks": """
You are an expert life insurance new business underwriter.

Using the Markdown, list any ADMINISTRATIVE or NON-MEDICAL RISKS and FINDINGS, such as:
- Discrepancies in signatures or dates
- Missing pages or incomplete answers
- Suspicious information requiring clarification

Return STRICT JSON:

{
  "summary": "Short description of admin / non-medical concerns.",
  "issues": [
    {
      "type": "Signature mismatch",
      "detail": "Signature on page 6 of medical exam form differs from page 20 of application.",
      "recommended_follow_up": "Request clarification from adviser and client."
    }
  ],
  "risk_assessment": "Low | Moderate | High",
  "underwriting_action": "Suggested operational next steps."
}
        """
    },
    "requirements": {
        "requirements_summary": """
You are an expert life insurance underwriter.

From the Markdown application, extract any REQUIREMENTS or PENDING ITEMS for underwriting, such as:
- Attending physician statements (APS) and for what conditions
- Additional forms or questionnaires
- Financial and AML documentation
- Any system-suggested requirements

Return STRICT JSON:

{
  "summary": "Short narrative of the requirement set.",
  "requirements": [
    {"type": "APS", "detail": "APS for slipped disc"},
    {"type": "APS", "detail": "APS for irregular / delayed period"},
    {"type": "Financial", "detail": "Proof of income and net worth"}
  ],
  "priority": "Low | Medium | High",
  "underwriting_action": "Guidance on sequencing and what to chase first."
}
        """
    }
}


# =============================================================================
# LIFE & HEALTH CLAIMS PERSONA CONFIGURATION
# =============================================================================

LIFE_HEALTH_CLAIMS_FIELD_SCHEMA = {
    "name": "LifeHealthClaimsFields",
    "fields": {
        # ===== Member/Claimant Information =====
        "MemberName": {
            "type": "string",
            "description": "Full name of the insured member or patient filing the claim.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "MemberID": {
            "type": "string",
            "description": "Member ID or subscriber ID for the insurance plan.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "DateOfBirth": {
            "type": "date",
            "description": "Member's date of birth.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Gender": {
            "type": "string",
            "description": "Member's gender (Male, Female, Other).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Policy Information =====
        "PolicyNumber": {
            "type": "string",
            "description": "Insurance policy number, often labeled as 'Policy #', 'Policy ID', 'Subscriber ID', or found near the member name. Format is typically alphanumeric.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PlanName": {
            "type": "string",
            "description": "Name of the insurance plan or product (e.g., 'HealthPlus Gold', 'Silver PPO'). Often found in the header or member information section.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "CoverageDates": {
            "type": "string",
            "description": "Coverage effective dates (start and end date). Look for 'Coverage Period', 'Effective Date', or date ranges.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "GroupNumber": {
            "type": "string",
            "description": "Employer or group number for group insurance. Labeled as 'Group #', 'Group ID'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Claim Information =====
        "ClaimNumber": {
            "type": "string",
            "description": "Unique claim reference number. Labeled as 'Claim #', 'Claim ID', or 'Reference Number'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "DateOfService": {
            "type": "date",
            "description": "Date when the medical service was provided. Labeled as 'Date of Service', 'DOS', 'Service Date'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "DateOfClaim": {
            "type": "date",
            "description": "Date when the claim was filed or submitted.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ClaimStatus": {
            "type": "string",
            "description": "Current status of the claim (Pending, Under Review, Approved, Denied).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Provider Information =====
        "ProviderName": {
            "type": "string",
            "description": "Name of the healthcare provider, physician, or clinic rendering services. Look for 'Provider', 'Physician', 'Doctor', or letterhead.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ProviderSpecialty": {
            "type": "string",
            "description": "Medical specialty of the provider (e.g., Cardiology, Orthopedics).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ProviderNPI": {
            "type": "string",
            "description": "National Provider Identifier (NPI) number.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "FacilityName": {
            "type": "string",
            "description": "Name of the hospital or medical facility.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "FacilityType": {
            "type": "string",
            "description": "Type of facility (Hospital, Clinic, Urgent Care, etc.).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Clinical Information =====
        "PrimaryDiagnosis": {
            "type": "object",
            "description": "Primary diagnosis with ICD-10 code.",
            "properties": {
                "code": {"type": "string", "description": "ICD-10 diagnosis code"},
                "description": {"type": "string", "description": "Diagnosis description"}
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "SecondaryDiagnoses": {
            "type": "array",
            "description": "Secondary and additional diagnosis codes.",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "ICD-10 code"},
                    "description": {"type": "string", "description": "Diagnosis description"}
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ProcedureCodes": {
            "type": "array",
            "description": "CPT/HCPCS procedure codes billed.",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "CPT or HCPCS code"},
                    "description": {"type": "string", "description": "Procedure description"},
                    "units": {"type": "number", "description": "Number of units"},
                    "modifier": {"type": "string", "description": "Modifier if applicable"}
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ReasonForVisit": {
            "type": "string",
            "description": "Chief complaint or reason for the medical visit.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "AdmissionDate": {
            "type": "date",
            "description": "Hospital admission date if applicable.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "DischargeDate": {
            "type": "date",
            "description": "Hospital discharge date if applicable.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "LengthOfStay": {
            "type": "number",
            "description": "Number of days in hospital.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Financial Information =====
        "BilledAmount": {
            "type": "string",
            "description": "Total amount billed by the provider. Labeled as 'Billed Amount', 'Total Charges', 'Submitted Charges'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "AllowedAmount": {
            "type": "string",
            "description": "Amount allowed by the insurance plan for the service. Labeled as 'Allowed Amount', 'Negotiated Rate'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PlanLiability": {
            "type": "string",
            "description": "Amount the insurance plan pays. Labeled as 'Plan Pays', 'Benefit Amount', 'Net Payment'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "MemberOOP": {
            "type": "string",
            "description": "Member's out-of-pocket responsibility (Deductible + Co-pay + Co-insurance). Labeled as 'Member Responsibility', 'Patient Pays', 'You Pay'.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Copay": {
            "type": "string",
            "description": "Copay amount if applicable.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Deductible": {
            "type": "string",
            "description": "Deductible amount applied.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Coinsurance": {
            "type": "string",
            "description": "Coinsurance percentage or amount.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Benefits & Limits =====
        "EligibilityStatus": {
            "type": "string",
            "description": "Member eligibility status at time of service.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "BenefitLimits": {
            "type": "array",
            "description": "Applicable benefit limits and remaining amounts.",
            "items": {
                "type": "object",
                "properties": {
                    "benefit_type": {"type": "string", "description": "Type of benefit"},
                    "limit": {"type": "string", "description": "Maximum benefit amount"},
                    "used": {"type": "string", "description": "Amount already used"},
                    "remaining": {"type": "string", "description": "Remaining benefit"}
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Exclusions": {
            "type": "array",
            "description": "Policy exclusions that may apply.",
            "items": {
                "type": "string",
                "description": "Exclusion description"
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PreExistingConditions": {
            "type": "string",
            "description": "Pre-existing conditions and their impact on coverage.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Prior Authorization =====
        "PriorAuthRequired": {
            "type": "boolean",
            "description": "Whether prior authorization was required.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PriorAuthNumber": {
            "type": "string",
            "description": "Prior authorization reference number if obtained.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PriorAuthStatus": {
            "type": "string",
            "description": "Status of prior authorization (Approved, Denied, Pending).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        }
    }
}

LIFE_HEALTH_CLAIMS_DEFAULT_PROMPTS = {
    "clinical_case_notes": {
        "reason_for_visit": """
You are an expert health insurance claims adjuster reviewing a medical claim.

From the claim documents in Markdown, analyze the REASON FOR VISIT and chief complaint.

Focus on:
- Primary complaint or symptoms reported
- Duration and severity of symptoms
- Relevant history leading to the visit
- Urgency level of the presentation

Return STRICT JSON:

{
  "summary": "2-3 sentence overview of the reason for visit.",
  "chief_complaint": "Primary complaint in patient's terms",
  "symptom_duration": "How long symptoms were present",
  "severity": "Mild | Moderate | Severe | Critical",
  "urgency": "Routine | Urgent | Emergent",
  "history_of_present_illness": "Brief HPI summary",
  "processing_notes": "Any concerns or flags for claims processing"
}
        """,
        "key_diagnoses": """
You are an expert health insurance claims adjuster reviewing a medical claim.

From the claim documents, extract and analyze all DIAGNOSES with their clinical context.

Focus on:
- Primary and secondary diagnosis codes (ICD-10)
- Clinical justification for each diagnosis
- Relationship between diagnoses
- Consistency with documented symptoms

Return STRICT JSON:

{
  "summary": "Overview of diagnostic picture.",
  "primary_diagnosis": {
    "code": "ICD-10 code",
    "description": "Full description",
    "clinical_support": "Evidence supporting this diagnosis"
  },
  "secondary_diagnoses": [
    {
      "code": "ICD-10 code",
      "description": "Description",
      "relationship_to_primary": "How it relates to primary diagnosis"
    }
  ],
  "diagnosis_consistency": "Consistent | Inconsistent | Unclear",
  "coding_accuracy": "Assessment of coding accuracy",
  "processing_notes": "Flags or concerns for claims review"
}
        """,
        "medical_necessity": """
You are an expert health insurance medical reviewer assessing medical necessity.

From the claim documents, evaluate the MEDICAL NECESSITY of the services provided.

Consider:
- Clinical appropriateness of treatments
- Alignment with standard of care
- Documentation supporting necessity
- Alternative treatment options considered

Return STRICT JSON:

{
  "summary": "Overall medical necessity assessment.",
  "necessity_determination": "Medically Necessary | Partially Necessary | Not Necessary | Insufficient Documentation",
  "clinical_rationale": "Explanation of the determination",
  "services_reviewed": [
    {
      "service": "Service or procedure",
      "code": "CPT/HCPCS code",
      "necessity_status": "Necessary | Questionable | Not Necessary",
      "rationale": "Specific rationale"
    }
  ],
  "documentation_quality": "Adequate | Inadequate | Missing",
  "recommended_action": "Approve | Deny | Request Additional Info | Peer Review"
}
        """
    },
    "clinical_timeline": {
        "treatment_timeline": """
You are an expert health insurance claims analyst reviewing treatment chronology.

From the claim documents, construct a detailed CLINICAL TIMELINE of events.

Include:
- All dates of service
- Sequence of treatments and procedures
- Provider encounters
- Key clinical milestones

Return STRICT JSON:

{
  "summary": "Overview of treatment timeline.",
  "timeline_events": [
    {
      "date": "YYYY-MM-DD or MM/DD format",
      "event_type": "ER Visit | Office Visit | Procedure | Lab | Imaging | Hospitalization | Discharge",
      "description": "What occurred",
      "provider": "Provider name if known",
      "tags": ["chest pain", "causal", "treatment"],
      "significance": "Why this event matters for the claim"
    }
  ],
  "total_duration": "Duration from first to last event",
  "treatment_pattern": "Appropriate | Concerning | Excessive | Insufficient",
  "processing_notes": "Timeline concerns or patterns"
}
        """
    },
    "benefits_policy": {
        "eligibility_verification": """
You are an expert health insurance benefits specialist.

From the claim documents, verify ELIGIBILITY AND ENROLLMENT status.

CRITICAL:
- EXTRACT ONLY information explicitly present in the documents.
- DO NOT INFER coverage dates or status if not visible.
- If eligibility information is missing, state "Not Documented".

Check:
- Member enrollment status at date of service
- Coverage effective dates
- Plan type and benefits tier
- Any coverage gaps or issues

Return STRICT JSON:

{
  "summary": "Eligibility verification summary based on available documents.",
  "eligibility_status": "Eligible | Not Eligible | Partially Eligible | Verification Needed",
  "member_info": {
    "name": "Member name",
    "member_id": "ID number",
    "group": "Group name/number"
  },
  "coverage_dates": {
    "effective_date": "Start date (or 'Not Documented')",
    "termination_date": "End date (or 'Not Documented')"
  },
  "plan_details": {
    "plan_name": "Plan name",
    "plan_type": "HMO | PPO | EPO | POS | Other",
    "network_status": "In-Network | Out-of-Network | Mixed | Unknown"
  },
  "eligibility_issues": ["List any issues found or 'Missing Eligibility Document'"],
  "processing_action": "Proceed | Hold | Deny - Not Eligible | Request Eligibility Info"
}
        """,
        "benefit_limits": """
You are an expert health insurance benefits analyst.

From the claim documents, analyze BENEFIT LIMITS and their application.

CRITICAL:
- EXTRACT ONLY data explicitly present in the provided documents.
- DO NOT INFER, GUESS, or SIMULATE benefit limits, deductibles, or accumulators.
- If the documents do not contain specific dollar amounts (e.g. "Deductible: $500"), return "Not Documented" or null.
- Do not assume standard plan features based on the Plan Name.

Review:
- Annual/lifetime maximums
- Service-specific limits
- Remaining benefits
- Accumulator status

Return STRICT JSON:

{
  "summary": "Benefit limits analysis based ONLY on provided text.",
  "applicable_limits": [
    {
      "benefit_type": "Type of benefit",
      "limit_amount": "Maximum allowed (or 'Not Documented')",
      "amount_used": "Already utilized (or 'Not Documented')",
      "amount_remaining": "Still available (or 'Not Documented')",
      "status": "Within Limits | Approaching Limit | Exceeded | Unknown"
    }
  ],
  "deductible_status": {
    "annual_deductible": "Amount (or 'Not Documented')",
    "met_to_date": "Amount met (or 'Not Documented')",
    "remaining": "Amount remaining (or 'Not Documented')"
  },
  "oop_maximum": {
    "annual_max": "Amount (or 'Not Documented')",
    "met_to_date": "Amount met (or 'Not Documented')",
    "remaining": "Amount remaining (or 'Not Documented')"
  },
  "limit_concerns": ["Any concerns about limits or missing data"],
  "processing_action": "Apply standard benefits | Apply limit | Review with member | Request Benefit Info"
}
        """,
        "exclusions_limitations": """
You are an expert health insurance policy analyst.

From the claim documents, identify any EXCLUSIONS OR LIMITATIONS that may apply.

CRITICAL:
- Only list exclusions explicitly mentioned in the provided documents.
- Do not list general exclusions unless found in the text.

Check:
- Policy exclusions
- Pre-existing condition clauses
- Waiting periods
- Service limitations

Return STRICT JSON:

{
  "summary": "Exclusions and limitations review based on available documents.",
  "applicable_exclusions": [
    {
      "exclusion_type": "Type of exclusion",
      "description": "What is excluded",
      "applies_to_claim": true,
      "rationale": "Why it applies or doesn't"
    }
  ],
  "pre_existing_review": {
    "condition_identified": "Condition if any",
    "lookback_period": "Time period reviewed",
    "determination": "Applies | Does Not Apply | Under Review | Unknown"
  },
  "waiting_periods": {
    "applicable": true,
    "period": "Duration if applicable",
    "status": "Satisfied | Not Satisfied | N/A | Unknown"
  },
  "processing_action": "No exclusions apply | Apply exclusion | Request records | Medical review needed"
}
        """
    },
    "claim_line_evaluation": {
        "line_item_review": """
You are an expert health insurance claims examiner reviewing claim lines.

From the claim documents, evaluate each CLAIM LINE for processing.

CRITICAL:
- Use Billed Amounts from the claim form.
- Use the provided "POLICY REFERENCE DATA" (if available) to determine the "Allowed Amount" for each CPT code from the "fee_schedule".
- If the CPT code is in the fee_schedule, use that value.
- If the CPT code is NOT in the fee_schedule, state "Unknown".
- Do not calculate member liability without known deductible/coinsurance data.

For each line item assess:
- CPT/HCPCS code accuracy
- Billed vs allowed amounts (using fee_schedule)
- Modifier appropriateness
- Bundle/unbundle issues

IMPORTANT: All monetary fields must be SHORT values like "$520.00" or "Unknown". Never include explanations in monetary fields.

Return STRICT JSON:

{
  "summary": "Overall claim line evaluation.",
  "total_billed": "$X.XX (dollar amount only)",
  "total_allowed": "$X.XX or 'Unknown'",
  "total_plan_pays": "$X.XX or 'Unknown'",
  "total_member_pays": "$X.XX or 'Unknown'",
  "claim_lines": [
    {
      "line_number": 1,
      "code": "CPT/HCPCS code",
      "description": "Service description",
      "billed": "$X.XX",
      "allowed": "$X.XX or 'Unknown'",
      "ai_opinion": "Approve | Deny | Review | Adjust",
      "adjustment_reason": "Reason if adjusting",
      "notes": "Processing notes"
    }
  ],
  "coding_issues": ["Any coding concerns identified"],
  "bundling_flags": ["Any bundling issues"],
  "recommended_action": "Pay as submitted | Adjust and pay | Deny | Request documentation | Pend for Fee Schedule"
}
        """
    },
    "tasks_decisions": {
        "final_decision": """
You are an expert health insurance claims adjudicator making a final determination.

Based on all claim information reviewed, provide a FINAL DECISION recommendation.

CRITICAL:
- Do not fabricate payment amounts.
- If benefits/pricing data is missing, the decision should be "Pend" or "Request Information".

Consider:
- Medical necessity determination
- Benefits and eligibility verification
- Policy exclusions and limitations
- Coding accuracy
- Documentation completeness

IMPORTANT: All monetary fields in payment_summary must be SHORT values like "$520.00" or "Unknown". Never include explanations in monetary fields.

Return STRICT JSON:

{
  "summary": "Final decision summary.",
  "decision": "Approve | Approve with Adjustment | Pend | Deny",
  "decision_rationale": "Detailed explanation of the decision",
  "payment_summary": {
    "total_billed": "$X.XX",
    "total_allowed": "$X.XX or 'Unknown'",
    "plan_pays": "$X.XX or 'Unknown'",
    "member_pays": "$X.XX or 'Unknown'",
    "adjustment_amount": "$X.XX or '$0.00'"
  },
  "denial_reasons": ["If denying, list specific reasons"],
  "pend_reasons": ["If pending, what additional info needed"],
  "appeal_rights": "Standard appeal rights notice",
  "next_steps": ["Required follow-up actions"],
  "reviewer_notes": "Additional notes for the claims processor"
}
        """
    }
}


# =============================================================================
# PROPERTY & CASUALTY CLAIMS PERSONA CONFIGURATION
# =============================================================================

PROPERTY_CASUALTY_CLAIMS_FIELD_SCHEMA = {
    "name": "PropertyCasualtyClaimsFields",
    "fields": {
        # ===== Claim Identification =====
        "ClaimNumber": {
            "type": "string",
            "description": "Unique claim reference number.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PolicyNumber": {
            "type": "string",
            "description": "Insurance policy number.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "LineOfBusiness": {
            "type": "string",
            "description": "Line of business (Auto BI, Auto PD, GL, Property, WC, etc.).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ClaimStatus": {
            "type": "string",
            "description": "Current claim status (Open, Closed, Litigation, etc.).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ClaimPhase": {
            "type": "string",
            "description": "Current phase (Investigation, Evaluation, Negotiation, Litigation, Closed).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Insured Information =====
        "InsuredName": {
            "type": "string",
            "description": "Name of the insured party.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "InsuredType": {
            "type": "string",
            "description": "Type of insured (Individual, Corporation, LLC, etc.).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "InsuredContact": {
            "type": "string",
            "description": "Contact information for the insured.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Claimant Information =====
        "ClaimantName": {
            "type": "string",
            "description": "Name of the claimant (third party if liability claim).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ClaimantType": {
            "type": "string",
            "description": "Type of claimant (Driver, Passenger, Pedestrian, Property Owner, etc.).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ClaimantAttorney": {
            "type": "string",
            "description": "Claimant's attorney name and firm if represented.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "AttorneyRepresented": {
            "type": "boolean",
            "description": "Whether claimant is represented by attorney.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Incident/Loss Information =====
        "DateOfLoss": {
            "type": "date",
            "description": "Date when the loss/incident occurred.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "TimeOfLoss": {
            "type": "string",
            "description": "Time when the incident occurred.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "LossLocation": {
            "type": "string",
            "description": "Location where the incident occurred.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "CauseOfLoss": {
            "type": "string",
            "description": "Primary cause of the loss (Rear-end collision, Slip and fall, Fire, etc.).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "LossDescription": {
            "type": "string",
            "description": "Detailed description of how the loss occurred.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "WeatherConditions": {
            "type": "string",
            "description": "Weather conditions at time of loss if applicable.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PoliceReportNumber": {
            "type": "string",
            "description": "Police report number if applicable.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Liability Assessment =====
        "LiabilityDetermination": {
            "type": "string",
            "description": "Liability percentage assessment (e.g., Insured 80%, Claimant 20%).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ComparativeNegligence": {
            "type": "string",
            "description": "Comparative/contributory negligence assessment.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "LiabilityDisputed": {
            "type": "boolean",
            "description": "Whether liability is disputed.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Coverage Information =====
        "CoverageType": {
            "type": "string",
            "description": "Type of coverage applicable (Liability, Collision, Comprehensive, etc.).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PolicyLimits": {
            "type": "string",
            "description": "Policy limits for the applicable coverage.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "Deductible": {
            "type": "string",
            "description": "Applicable deductible amount.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "CoverageIssues": {
            "type": "array",
            "description": "Any coverage issues or exclusions identified.",
            "items": {"type": "string"},
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Injury Information (for BI claims) =====
        "InjuryDescription": {
            "type": "array",
            "description": "List of injuries claimed.",
            "items": {
                "type": "object",
                "properties": {
                    "injury": {"type": "string", "description": "Type of injury"},
                    "body_part": {"type": "string", "description": "Body part affected"},
                    "severity": {"type": "string", "description": "Severity level"},
                    "treatment": {"type": "string", "description": "Treatment received"}
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PreExistingConditions": {
            "type": "array",
            "description": "Pre-existing conditions that may affect the claim.",
            "items": {"type": "string"},
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "TreatingProviders": {
            "type": "array",
            "description": "Healthcare providers treating the claimant.",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Provider name"},
                    "specialty": {"type": "string", "description": "Medical specialty"},
                    "treatment_dates": {"type": "string", "description": "Dates of treatment"}
                }
            },
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "WorkStatus": {
            "type": "string",
            "description": "Claimant's work status (Working, Modified Duty, Off Work, Returned to Work).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "LostWages": {
            "type": "string",
            "description": "Lost wages claimed.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Financial Information =====
        "PaidIndemnity": {
            "type": "string",
            "description": "Total indemnity payments made to date.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PaidExpense": {
            "type": "string",
            "description": "Total expenses paid (legal, medical, investigation).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "TotalIncurred": {
            "type": "string",
            "description": "Total incurred (paid + reserves).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "CurrentReserve": {
            "type": "string",
            "description": "Current reserve amount set for the claim.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "MedicalSpecials": {
            "type": "string",
            "description": "Total medical special damages claimed.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "GeneralDamages": {
            "type": "string",
            "description": "General damages (pain and suffering) estimated or demanded.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PropertyDamage": {
            "type": "string",
            "description": "Property damage amount if applicable.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Litigation/Subrogation =====
        "LitigationStatus": {
            "type": "string",
            "description": "Whether the claim is in litigation.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "SuitFiled": {
            "type": "boolean",
            "description": "Whether a lawsuit has been filed.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "SubrogationPotential": {
            "type": "string",
            "description": "Subrogation potential and status.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "FraudIndicators": {
            "type": "array",
            "description": "Any fraud indicators or red flags identified.",
            "items": {"type": "string"},
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        
        # ===== Severity Assessment =====
        "SeverityRating": {
            "type": "string",
            "description": "Overall severity rating (Low, Medium, High, Critical).",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "ComplexityRating": {
            "type": "string",
            "description": "Claim complexity rating.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        }
    }
}

PROPERTY_CASUALTY_CLAIMS_DEFAULT_PROMPTS = {
    "liability_case_notes": {
        "accident_overview": """
You are an expert property and casualty claims adjuster.

From the claim documents in Markdown, provide a comprehensive ACCIDENT OVERVIEW.

Focus on:
- Detailed description of the incident
- Parties involved and their roles
- Location and environmental factors
- Timeline of events
- Initial liability indicators

Return STRICT JSON:

{
  "summary": "3-4 sentence narrative of the accident.",
  "incident_details": {
    "date": "Date of loss",
    "time": "Time if known",
    "location": "Specific location",
    "description": "Detailed description of what happened"
  },
  "parties": [
    {
      "name": "Party name",
      "role": "Insured | Claimant | Witness | Other",
      "involvement": "How they were involved"
    }
  ],
  "environmental_factors": {
    "weather": "Weather conditions",
    "road_conditions": "If applicable",
    "visibility": "Visibility conditions",
    "other": "Other relevant factors"
  },
  "initial_liability_indicators": "Preliminary liability assessment",
  "inline_links": ["References to supporting documents"]
}
        """,
        "coverage_triggers": """
You are an expert property and casualty coverage analyst.

From the claim documents, analyze COVERAGE TRIGGERS and policy application.

Evaluate:
- Applicable coverage(s) under the policy
- Policy limits and deductibles
- Coverage exclusions or limitations
- Potential coverage issues

Return STRICT JSON:

{
  "summary": "Coverage analysis summary.",
  "applicable_coverages": [
    {
      "coverage_type": "Type of coverage",
      "policy_limit": "Limit amount",
      "deductible": "Deductible if any",
      "applies": true,
      "rationale": "Why it applies"
    }
  ],
  "potential_exclusions": [
    {
      "exclusion": "Exclusion language or type",
      "applies": "Yes | No | Possibly",
      "analysis": "Explanation"
    }
  ],
  "coverage_issues": ["Any coverage concerns"],
  "inline_links": ["Document references"]
}
        """,
        "liability_assessment": """
You are an expert liability claims adjuster.

From the claim documents, provide a detailed LIABILITY ASSESSMENT.

Analyze:
- Insured's percentage of liability
- Claimant's comparative negligence
- Evidence supporting liability determination
- Disputed facts or contested liability

Return STRICT JSON:

{
  "summary": "Liability assessment summary.",
  "liability_determination": {
    "insured_percentage": "Percentage (e.g., 80%)",
    "claimant_percentage": "Percentage (e.g., 20%)",
    "confidence": "High | Medium | Low",
    "basis": "Basis for determination"
  },
  "supporting_evidence": [
    {
      "evidence_type": "Police Report | Witness Statement | Photos | Video | Other",
      "description": "What it shows",
      "impact": "Supports | Undermines | Neutral"
    }
  ],
  "disputed_facts": ["Facts in dispute"],
  "liability_status": "Clear Liability | Disputed | Comparative | Under Investigation",
  "inline_links": ["Document references"]
}
        """,
        "causation_preexisting": """
You are an expert claims adjuster analyzing causation and pre-existing conditions.

From the claim documents, analyze CAUSATION and PRE-EXISTING CONDITIONS.

Evaluate:
- Causal relationship between accident and injuries
- Pre-existing medical conditions
- Aggravation vs. new injury analysis
- Medical record timeline

Return STRICT JSON:

{
  "summary": "Causation and pre-existing analysis.",
  "causation_analysis": {
    "injuries_claimed": ["List of claimed injuries"],
    "causation_determination": "Directly caused | Aggravation | Questionable | Unrelated",
    "analysis": "Detailed causation analysis"
  },
  "pre_existing_conditions": [
    {
      "condition": "Pre-existing condition",
      "documentation": "Where documented",
      "impact_on_claim": "How it affects the claim",
      "apportionment": "Percentage if applicable"
    }
  ],
  "medical_timeline": {
    "prior_treatment": "Treatment before accident",
    "gap_in_treatment": "Any gaps in treatment",
    "treatment_pattern": "Normal | Excessive | Inconsistent"
  },
  "inline_links": ["Medical record references"]
}
        """,
        "red_flags": """
You are an expert claims adjuster identifying fraud indicators and red flags.

From the claim documents, identify any RED FLAGS or fraud indicators.

Look for:
- Inconsistencies in statements
- Suspicious timing or patterns
- Documentation issues
- Known fraud indicators

Return STRICT JSON:

{
  "summary": "Red flags and fraud indicator summary.",
  "red_flags": [
    {
      "flag_type": "Type of red flag",
      "description": "What was identified",
      "severity": "High | Medium | Low",
      "recommended_action": "What to do about it"
    }
  ],
  "fraud_indicators": [
    "Specific fraud indicators noted"
  ],
  "inconsistencies": [
    {
      "area": "Where inconsistency found",
      "description": "The inconsistency",
      "significance": "Impact on claim"
    }
  ],
  "siu_referral_recommended": "Yes | No",
  "investigation_recommendations": ["Recommended investigative steps"],
  "inline_links": ["Document references"]
}
        """
    },
    "incident_timeline": {
        "medical_timeline": """
You are an expert property and casualty claims analyst.

From the claim documents, construct an INCIDENT AND MEDICAL TIMELINE.

Include:
- Date of loss event
- Medical treatment dates
- Key claim milestones
- Categorize each event's impact on liability

Return STRICT JSON:

{
  "summary": "Timeline overview.",
  "timeline_events": [
    {
      "date": "MM/DD/YYYY",
      "event_type": "Incident | Medical | Legal | Investigation | Negotiation",
      "description": "What occurred",
      "liability_impact": "Supports Liability | Disputes Liability | Neutral",
      "damages_impact": "Supports Damages | Disputes Damages | Neutral",
      "source": "Document source"
    }
  ],
  "key_dates": {
    "date_of_loss": "Date",
    "first_treatment": "Date",
    "last_treatment": "Date",
    "suit_filed": "Date if applicable"
  },
  "timeline_concerns": ["Any timeline issues or gaps"],
  "treatment_summary": "Overall treatment pattern assessment"
}
        """
    },
    "injury_treatment": {
        "injury_summary": """
You are an expert bodily injury claims adjuster.

From the claim documents, provide an INJURY AND TREATMENT SUMMARY.

Analyze:
- All injuries claimed
- Treatment received for each
- Treatment providers
- Work status and restrictions
- Prognosis

Return STRICT JSON:

{
  "summary": "Overall injury and treatment summary.",
  "injuries": [
    {
      "diagnosis": "Injury/diagnosis",
      "body_part": "Body part affected",
      "first_noted": "Date first documented",
      "treatment": "Treatment summary",
      "status": "Resolved | Ongoing | Permanent",
      "notes": "Additional notes"
    }
  ],
  "treatment_providers": [
    {
      "provider": "Provider name",
      "specialty": "Specialty",
      "treatment_dates": "Date range",
      "charges": "Amount charged"
    }
  ],
  "treatment_chronology": "Appropriate | Excessive | Delayed | Inconsistent",
  "work_status": {
    "current_status": "Working | Off Work | Modified Duty | Returned Full Duty",
    "off_work_dates": "Date range if applicable",
    "restrictions": "Any work restrictions"
  },
  "prognosis": "Expected outcome and timeline"
}
        """
    },
    "evidence_matrix": {
        "evidence_analysis": """
You are an expert claims adjuster evaluating evidence.

From the claim documents, create an EVIDENCE MATRIX categorizing all evidence.

Categorize each piece of evidence by:
- Type of evidence
- What it supports or disputes
- Reliability and weight

Return STRICT JSON:

{
  "summary": "Evidence analysis overview.",
  "evidence_items": [
    {
      "source": "Document or evidence source",
      "evidence_type": "Police Report | Medical Record | Witness | Photo | Video | Expert | Other",
      "supports_liability": true,
      "supports_injury": true,
      "supports_damages": true,
      "challenges_claim": false,
      "coverage_relevant": true,
      "weight": "High | Medium | Low",
      "notes": "Key takeaways"
    }
  ],
  "evidence_gaps": ["Missing evidence that would be helpful"],
  "strongest_evidence": "What most supports/undermines the claim",
  "recommended_additional_evidence": ["Evidence to obtain"]
}
        """
    },
    "damages_negotiation": {
        "damages_brief": """
You are an expert claims adjuster preparing a damages and negotiation brief.

From the claim documents, prepare a comprehensive DAMAGES AND NEGOTIATION BRIEF.

Include:
- Economic damages breakdown
- General damages assessment
- Settlement valuation range
- Negotiation strategy

Return STRICT JSON:

{
  "summary": "Damages and negotiation summary.",
  "economic_damages": {
    "medical_specials": "Total medical bills",
    "lost_wages": "Lost wage claim",
    "future_medicals": "Future medical estimate",
    "other_economic": "Other economic damages",
    "total_economic": "Total economic damages",
    "ai_estimated_range": "AI estimated value range"
  },
  "general_damages": {
    "pain_suffering": "Pain and suffering assessment",
    "estimated_range": "Low to high estimate",
    "multiplier_applied": "Multiplier if using multiple method"
  },
  "total_value_range": {
    "low": "Low end estimate",
    "target": "Target settlement",
    "high": "High end exposure"
  },
  "negotiation_strategy": {
    "opening_offer": "Recommended opening offer",
    "target_settlement": "Target settlement amount",
    "walk_away": "Walk away point",
    "strengths": ["Claim strengths for negotiation"],
    "weaknesses": ["Claim weaknesses"],
    "recommended_talking_points": ["Key points to emphasize"]
  }
}
        """
    },
    "tasks_next_steps": {
        "settlement_memo": """
You are an expert claims adjuster preparing a settlement recommendation.

Based on all claim information, prepare a SETTLEMENT MEMO with recommended action.

Include:
- Claim evaluation summary
- Settlement authority request
- Risk analysis
- Recommended next steps

Return STRICT JSON:

{
  "summary": "Settlement recommendation summary.",
  "claim_evaluation": {
    "liability_assessment": "Summary of liability",
    "damages_assessment": "Summary of damages",
    "coverage_status": "Coverage confirmation",
    "overall_exposure": "Total exposure estimate"
  },
  "settlement_recommendation": {
    "recommended_action": "Settle | Litigate | Investigate Further | Deny",
    "settlement_authority": "Amount requested",
    "target_settlement": "Target settlement amount",
    "rationale": "Detailed rationale"
  },
  "risk_analysis": {
    "trial_verdict_range": "Estimated verdict range",
    "litigation_costs": "Estimated defense costs",
    "probability_of_adverse_outcome": "Percentage",
    "recommendation": "Cost-benefit analysis"
  },
  "next_steps": [
    {
      "task": "Task description",
      "owner": "Who should complete",
      "due_date": "Suggested due date",
      "priority": "High | Medium | Low"
    }
  ],
  "approvals_needed": ["Any approvals required"]
}
        """
    }
}


# =============================================================================
# AUTOMOTIVE CLAIMS PERSONA CONFIGURATION (Multimodal)
# =============================================================================

AUTOMOTIVE_CLAIMS_FIELD_SCHEMA = {
    "name": "AutomotiveClaimsFields",
    "description": "Multimodal field schema for automotive claims - supports documents, images, and videos",
    "fields": {
        # ===== Claim Identification =====
        "ClaimNumber": {
            "type": "string",
            "description": "Unique claim reference number.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "PolicyNumber": {
            "type": "string",
            "description": "Insurance policy number.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "DateOfLoss": {
            "type": "date",
            "description": "Date when the incident occurred.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "TimeOfLoss": {
            "type": "string",
            "description": "Time when the incident occurred.",
            "method": "extract",
            "sources": ["document", "video"],
            "estimateSourceAndConfidence": True
        },
        
        # ===== Vehicle Information =====
        "VehicleVIN": {
            "type": "string",
            "description": "Vehicle Identification Number (17 characters).",
            "method": "extract",
            "sources": ["document", "image"],
            "estimateSourceAndConfidence": True
        },
        "VehicleMake": {
            "type": "string",
            "description": "Vehicle manufacturer (e.g., Toyota, Ford, BMW).",
            "method": "extract",
            "sources": ["document", "image"],
            "estimateSourceAndConfidence": True
        },
        "VehicleModel": {
            "type": "string",
            "description": "Vehicle model name (e.g., Camry, F-150, X5).",
            "method": "extract",
            "sources": ["document", "image"],
            "estimateSourceAndConfidence": True
        },
        "VehicleYear": {
            "type": "number",
            "description": "Vehicle model year.",
            "method": "extract",
            "sources": ["document", "image"],
            "estimateSourceAndConfidence": True
        },
        "VehicleColor": {
            "type": "string",
            "description": "Vehicle exterior color.",
            "method": "generate",
            "sources": ["image"],
            "estimateSourceAndConfidence": True
        },
        "LicensePlate": {
            "type": "string",
            "description": "Vehicle license plate number.",
            "method": "extract",
            "sources": ["document", "image", "video"],
            "estimateSourceAndConfidence": True
        },
        "Mileage": {
            "type": "string",
            "description": "Vehicle odometer reading at time of incident.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        
        # ===== Incident Information =====
        "IncidentLocation": {
            "type": "string",
            "description": "Location/address where incident occurred.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "WeatherConditions": {
            "type": "string",
            "description": "Weather conditions at time of incident.",
            "method": "extract",
            "sources": ["document", "video"],
            "estimateSourceAndConfidence": True
        },
        "RoadConditions": {
            "type": "string",
            "description": "Road surface conditions (dry, wet, icy, etc.).",
            "method": "extract",
            "sources": ["document", "video"],
            "estimateSourceAndConfidence": True
        },
        "IncidentDescription": {
            "type": "string",
            "description": "Narrative description of how the incident occurred.",
            "method": "extract",
            "sources": ["document", "video"],
            "estimateSourceAndConfidence": True
        },
        "PoliceReportNumber": {
            "type": "string",
            "description": "Police report reference number.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "PoliceReportFiled": {
            "type": "boolean",
            "description": "Whether a police report was filed.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        
        # ===== Damage Assessment (Image-Derived) =====
        "DamageAreas": {
            "type": "array",
            "description": "List of damaged areas detected from vehicle images.",
            "method": "generate",
            "sources": ["image"],
            "items": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location on vehicle: front, rear, driver_side, passenger_side, roof, hood, trunk"
                    },
                    "damageType": {
                        "type": "string",
                        "description": "Type of damage: dent, scratch, crack, shattered, crushed, missing_part"
                    },
                    "severity": {
                        "type": "string",
                        "description": "Severity level: minor, moderate, severe"
                    },
                    "components": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Affected components: bumper, fender, door, headlight, mirror, windshield, etc."
                    },
                    "description": {
                        "type": "string",
                        "description": "AI-generated description of the damage"
                    }
                }
            },
            "estimateSourceAndConfidence": True
        },
        "OverallDamageSeverity": {
            "type": "string",
            "description": "Aggregated damage severity: Minor, Moderate, Heavy, Total Loss.",
            "method": "generate",
            "sources": ["image"],
            "estimateSourceAndConfidence": True
        },
        "EstimatedDamageCategory": {
            "type": "string",
            "description": "Estimated damage cost category: Light (<$1000), Moderate ($1K-$5K), Heavy ($5K-$15K), Severe (>$15K).",
            "method": "generate",
            "sources": ["image"],
            "estimateSourceAndConfidence": True
        },
        
        # ===== Video Evidence (Video-Derived) =====
        "VideoSegments": {
            "type": "array",
            "description": "Video chapter segments with descriptions.",
            "method": "generate",
            "sources": ["video"],
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "description": "Start timestamp (HH:MM:SS)"
                    },
                    "duration": {
                        "type": "string",
                        "description": "Segment duration"
                    },
                    "description": {
                        "type": "string",
                        "description": "AI-generated scene description"
                    },
                    "keyframeUrl": {
                        "type": "string",
                        "description": "URL to keyframe image"
                    }
                }
            },
            "estimateSourceAndConfidence": True
        },
        "Transcript": {
            "type": "string",
            "description": "Audio transcript from video if available.",
            "method": "extract",
            "sources": ["video"],
            "estimateSourceAndConfidence": True
        },
        "ImpactDetected": {
            "type": "boolean",
            "description": "Whether a collision/impact was detected in video.",
            "method": "generate",
            "sources": ["video"],
            "estimateSourceAndConfidence": True
        },
        "ImpactTimestamp": {
            "type": "string",
            "description": "Timestamp of detected impact in video.",
            "method": "generate",
            "sources": ["video"],
            "estimateSourceAndConfidence": True
        },
        "PreIncidentBehavior": {
            "type": "string",
            "description": "Description of events before the incident.",
            "method": "generate",
            "sources": ["video"],
            "estimateSourceAndConfidence": True
        },
        "PostIncidentBehavior": {
            "type": "string",
            "description": "Description of events after the incident.",
            "method": "generate",
            "sources": ["video"],
            "estimateSourceAndConfidence": True
        },
        
        # ===== Repair Estimate (Document-Derived) =====
        "EstimateTotal": {
            "type": "string",
            "description": "Total repair estimate amount.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "PartsTotal": {
            "type": "string",
            "description": "Total parts cost from repair estimate.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "LaborTotal": {
            "type": "string",
            "description": "Total labor cost from repair estimate.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "LaborHours": {
            "type": "number",
            "description": "Total labor hours from repair estimate.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "LaborRate": {
            "type": "string",
            "description": "Hourly labor rate from repair estimate.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "RepairLineItems": {
            "type": "array",
            "description": "Individual repair line items from estimate.",
            "method": "extract",
            "sources": ["document"],
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unitPrice": {"type": "string"},
                    "totalPrice": {"type": "string"},
                    "type": {"type": "string", "description": "parts, labor, paint, other"}
                }
            },
            "estimateSourceAndConfidence": True
        },
        "RepairShopName": {
            "type": "string",
            "description": "Name of the repair facility providing estimate.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        
        # ===== Parties Involved =====
        "Claimant": {
            "type": "object",
            "description": "Person filing the claim.",
            "method": "extract",
            "sources": ["document"],
            "properties": {
                "name": {"type": "string"},
                "phone": {"type": "string"},
                "email": {"type": "string"},
                "role": {"type": "string", "description": "Driver, Passenger, Pedestrian, Property Owner"}
            },
            "estimateSourceAndConfidence": True
        },
        "OtherParties": {
            "type": "array",
            "description": "Other parties involved in the incident.",
            "method": "extract",
            "sources": ["document"],
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "vehicle": {"type": "string"},
                    "insurance": {"type": "string"}
                }
            },
            "estimateSourceAndConfidence": True
        },
        "Witnesses": {
            "type": "array",
            "description": "Witness information.",
            "method": "extract",
            "sources": ["document"],
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "contact": {"type": "string"},
                    "statement": {"type": "string"}
                }
            },
            "estimateSourceAndConfidence": True
        },
        
        # ===== Policy & Coverage =====
        "CoverageType": {
            "type": "string",
            "description": "Type of coverage: Collision, Comprehensive, Liability, etc.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "PolicyLimits": {
            "type": "string",
            "description": "Coverage limits from policy.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        "Deductible": {
            "type": "string",
            "description": "Applicable deductible amount.",
            "method": "extract",
            "sources": ["document"],
            "estimateSourceAndConfidence": True
        },
        
        # ===== AI-Computed Fields (Policy Engine Output) =====
        "SeverityRating": {
            "type": "string",
            "description": "AI-computed severity: Low, Medium, High, Critical.",
            "method": "generate",
            "sources": ["computed"],
            "estimateSourceAndConfidence": True
        },
        "LiabilityAssessment": {
            "type": "string",
            "description": "AI-computed liability: Clear Liability, Shared, Disputed.",
            "method": "generate",
            "sources": ["computed"],
            "estimateSourceAndConfidence": True
        },
        "LiabilityPercentage": {
            "type": "number",
            "description": "Insured's liability percentage (0-100).",
            "method": "generate",
            "sources": ["computed"],
            "estimateSourceAndConfidence": True
        },
        "PayoutRecommendation": {
            "type": "object",
            "description": "AI-computed payout recommendation.",
            "method": "generate",
            "sources": ["computed"],
            "properties": {
                "minAmount": {"type": "string"},
                "maxAmount": {"type": "string"},
                "recommendedAmount": {"type": "string"}
            },
            "estimateSourceAndConfidence": True
        },
        "PolicyRulesApplied": {
            "type": "array",
            "description": "List of policy rules that were applied.",
            "method": "generate",
            "sources": ["computed"],
            "items": {"type": "string"},
            "estimateSourceAndConfidence": True
        },
        "FraudIndicators": {
            "type": "array",
            "description": "Red flags identified by fraud detection policies.",
            "method": "generate",
            "sources": ["computed"],
            "items": {"type": "string"},
            "estimateSourceAndConfidence": True
        },
        "AdjusterNotes": {
            "type": "string",
            "description": "AI-generated summary notes for the adjuster.",
            "method": "generate",
            "sources": ["computed"],
            "estimateSourceAndConfidence": True
        }
    }
}

# Image-specific field schema for damage detection
AUTOMOTIVE_CLAIMS_IMAGE_FIELD_SCHEMA = {
    "name": "AutomotiveClaimsImageFields",
    "description": "Field schema for automotive claims image analyzer - damage detection from photos",
    "fields": {
        "DamageAreas": {
            "type": "array",
            "description": "List of detected damage areas on the vehicle",
            "method": "generate",
            "items": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location on vehicle: front, rear, driver_side, passenger_side, roof, hood, trunk"
                    },
                    "damageType": {
                        "type": "string",
                        "description": "Type of damage: dent, scratch, crack, shattered, crushed, missing_part"
                    },
                    "severity": {
                        "type": "string",
                        "description": "Severity level: minor, moderate, severe"
                    },
                    "components": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Affected components: bumper, fender, door, hood, headlight, taillight, mirror, window, tire, wheel"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the damage"
                    }
                }
            },
            "estimateSourceAndConfidence": True
        },
        "OverallDamageSeverity": {
            "type": "string",
            "description": "Overall damage severity assessment: minor, moderate, severe, total_loss",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "VehicleType": {
            "type": "string",
            "description": "Type of vehicle visible: sedan, SUV, truck, van, motorcycle, other",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "VehicleColor": {
            "type": "string",
            "description": "Primary color of the vehicle",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "LicensePlateVisible": {
            "type": "boolean",
            "description": "Whether a license plate is visible in the image",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "LicensePlateNumber": {
            "type": "string",
            "description": "License plate number if visible and readable",
            "method": "generate",
            "estimateSourceAndConfidence": True
        }
    }
}

# Video-specific field schema for incident analysis
AUTOMOTIVE_CLAIMS_VIDEO_FIELD_SCHEMA = {
    "name": "AutomotiveClaimsVideoFields",
    "description": "Field schema for automotive claims video analyzer - dashcam and incident footage analysis",
    "fields": {
        "IncidentDetected": {
            "type": "boolean",
            "description": "Whether a collision or incident is detected in the video",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "IncidentTimestamp": {
            "type": "string",
            "description": "Timestamp of the detected incident in HH:MM:SS format",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "IncidentType": {
            "type": "string",
            "description": "Type of incident: rear_end, sideswipe, head_on, single_vehicle, parking, unknown",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "PreIncidentBehavior": {
            "type": "string",
            "description": "Description of driving behavior in the 10 seconds before incident",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "PostIncidentBehavior": {
            "type": "string",
            "description": "Description of events immediately after the incident",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "WeatherConditions": {
            "type": "string",
            "description": "Weather conditions visible: clear, rain, snow, fog, night",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "RoadType": {
            "type": "string",
            "description": "Type of road: highway, city_street, parking_lot, intersection, residential",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "SpeedEstimate": {
            "type": "string",
            "description": "Estimated speed of the recording vehicle if determinable",
            "method": "generate",
            "estimateSourceAndConfidence": True
        },
        "OtherVehicles": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Other vehicles involved in the incident",
            "method": "generate",
            "estimateSourceAndConfidence": True
        }
    }
}

AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS = {
    "damage_assessment": {
        "visual_damage_analysis": """
You are an expert automotive claims adjuster analyzing vehicle damage.

From the extracted damage information and images, provide a comprehensive VISUAL DAMAGE ANALYSIS.

Focus on:
- All visible damage areas with location and severity
- Affected vehicle components
- Estimated repair complexity
- Safety-related damage (airbags, structural)

Return STRICT JSON:

{
  "summary": "2-3 sentence overview of total damage.",
  "damage_areas": [
    {
      "location": "Location on vehicle (front, rear, driver_side, etc.)",
      "damage_type": "dent | scratch | crack | shattered | crushed | missing_part",
      "severity": "minor | moderate | severe",
      "components": ["List of affected components"],
      "repair_method": "PDR | Panel Repair | Panel Replace | etc.",
      "estimated_cost_range": "$X - $Y"
    }
  ],
  "overall_severity": "Minor | Moderate | Heavy | Total Loss",
  "safety_concerns": ["Any safety-related damage"],
  "structural_damage": true | false,
  "airbag_deployment": true | false,
  "inline_links": ["References to supporting images"]
}
        """,
        "estimate_validation": """
You are an expert claims adjuster validating a repair estimate against visible damage.

Compare the repair estimate to the damage assessment and identify discrepancies.

Evaluate:
- Does the estimate match the visible damage?
- Are labor rates reasonable for the market?
- Are parts priced appropriately (OEM vs aftermarket)?
- Any items that seem inflated or missing?

Return STRICT JSON:

{
  "summary": "Estimate validation summary.",
  "estimate_total": "Total from estimate",
  "damage_assessment_estimate": "Expected range based on damage",
  "variance": "Percentage difference",
  "variance_acceptable": true | false,
  "line_item_analysis": [
    {
      "item": "Line item description",
      "quoted_price": "$X",
      "market_rate": "$Y",
      "variance": "+X% | -X% | OK",
      "flag": "none | review | concern"
    }
  ],
  "labor_rate_analysis": {
    "quoted_rate": "$X/hr",
    "market_rate": "$Y/hr",
    "acceptable": true | false
  },
  "recommendations": ["List of recommendations"],
  "inline_links": ["Document references"]
}
        """
    },
    "liability_assessment": {
        "fault_determination": """
You are an expert claims adjuster determining liability for an automotive incident.

From all available evidence (documents, images, video), assess fault and liability.

Consider:
- Type of collision and applicable traffic laws
- Evidence from dashcam/video footage
- Police report findings
- Witness statements
- Damage patterns (point of impact, direction)

Return STRICT JSON:

{
  "summary": "Liability determination summary.",
  "collision_type": "Rear-end | Side-impact | Head-on | Parking lot | Single vehicle | etc.",
  "liability_determination": {
    "insured_percentage": 0-100,
    "other_party_percentage": 0-100,
    "confidence": "High | Medium | Low",
    "basis": "Explanation of determination"
  },
  "evidence_analysis": [
    {
      "evidence_type": "Video | Police Report | Photos | Witness | etc.",
      "source": "Document/file name",
      "finding": "What it shows",
      "supports": "Insured | Other Party | Neutral"
    }
  ],
  "traffic_violations": ["Any identified violations"],
  "disputed_facts": ["Facts that are unclear or contested"],
  "liability_status": "Clear Liability | Comparative | Disputed | Under Investigation",
  "inline_links": ["Evidence references"]
}
        """,
        "video_evidence_analysis": """
You are an expert claims analyst reviewing video evidence from a vehicle incident.

Analyze the video segments and keyframes to understand what happened.

Focus on:
- Events leading up to the incident
- The moment of impact/collision
- Actions of all parties involved
- Environmental factors visible
- Any contributing factors

Return STRICT JSON:

{
  "summary": "Video evidence summary.",
  "timeline": [
    {
      "timestamp": "HH:MM:SS",
      "event": "Description of what's happening",
      "significance": "Why this matters for the claim"
    }
  ],
  "impact_analysis": {
    "impact_detected": true | false,
    "impact_timestamp": "HH:MM:SS",
    "impact_description": "How the collision occurred",
    "speed_estimate": "Approximate speed if determinable"
  },
  "party_actions": [
    {
      "party": "Insured | Other Vehicle | Pedestrian",
      "pre_incident": "Actions before incident",
      "at_incident": "Actions at time of incident",
      "post_incident": "Actions after incident"
    }
  ],
  "environmental_factors": {
    "weather_visible": "Conditions shown in video",
    "road_visible": "Road conditions shown",
    "visibility": "Good | Reduced | Poor",
    "traffic_conditions": "Light | Moderate | Heavy"
  },
  "liability_indicators": "What the video suggests about fault",
  "inline_links": ["Video segment references"]
}
        """
    },
    "fraud_detection": {
        "red_flag_analysis": """
You are an expert claims fraud investigator analyzing an automotive claim.

Review all claim information for fraud indicators and red flags.

Look for:
- Timing anomalies (new policy, recent coverage changes)
- Damage inconsistencies (damage doesn't match narrative)
- Estimate irregularities (inflated, specific shop insistence)
- Documentation gaps (no police report, missing info)
- Pattern indicators (multiple claims, prior loss history)

Return STRICT JSON:

{
  "summary": "Fraud analysis summary.",
  "risk_level": "Low | Moderate | High",
  "red_flags": [
    {
      "category": "Timing | Damage | Estimate | Documentation | Pattern",
      "indicator": "Specific red flag identified",
      "severity": "Low | Moderate | High",
      "evidence": "What triggered this flag",
      "recommended_action": "What to do about it"
    }
  ],
  "damage_narrative_consistency": {
    "consistent": true | false,
    "discrepancies": ["List any discrepancies between damage and story"]
  },
  "estimate_concerns": ["Any concerns with the repair estimate"],
  "siu_referral_recommended": true | false,
  "investigation_steps": ["Recommended investigative actions"],
  "inline_links": ["Evidence references"]
}
        """
    },
    "payout_recommendation": {
        "settlement_analysis": """
You are an expert claims adjuster preparing a payout recommendation.

Based on the damage assessment, estimate validation, and policy terms, recommend a fair settlement.

Consider:
- Validated repair costs
- Policy limits and deductibles
- Liability determination
- Betterment/depreciation if applicable
- Any coverage exclusions

Return STRICT JSON:

{
  "summary": "Settlement recommendation summary.",
  "claim_valuation": {
    "repair_estimate": "$X",
    "validated_amount": "$X (after adjustments)",
    "adjustments": [
      {"type": "Labor rate adjustment | Betterment | etc.", "amount": "$X"}
    ]
  },
  "policy_application": {
    "coverage_type": "Collision | Comprehensive | etc.",
    "policy_limit": "$X",
    "deductible": "$X",
    "applicable_limit": "$X"
  },
  "liability_impact": {
    "insured_liability": "X%",
    "reduction_amount": "$X (if comparative)"
  },
  "payout_recommendation": {
    "gross_amount": "$X",
    "less_deductible": "$X",
    "less_liability_reduction": "$X",
    "net_payout": "$X",
    "payout_range": {"min": "$X", "max": "$Y"}
  },
  "policy_rules_applied": ["List of policy rules that informed this recommendation"],
  "adjuster_notes": "Additional notes for the reviewing adjuster",
  "inline_links": ["Supporting document references"]
}
        """
    }
}


# =============================================================================
# LEGACY CLAIMS SCHEMA (for backward compatibility)
# =============================================================================

CLAIMS_FIELD_SCHEMA = LIFE_HEALTH_CLAIMS_FIELD_SCHEMA
CLAIMS_DEFAULT_PROMPTS = LIFE_HEALTH_CLAIMS_DEFAULT_PROMPTS


# =============================================================================
# MORTGAGE PERSONA CONFIGURATION (Stub)
# =============================================================================

MORTGAGE_FIELD_SCHEMA = {
    "name": "MortgageFields",
    "fields": {
        "BorrowerName": {
            "type": "string",
            "description": "Full name of the mortgage applicant/borrower.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PropertyAddress": {
            "type": "string",
            "description": "Address of the property being financed.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "LoanAmount": {
            "type": "string",
            "description": "Requested mortgage loan amount.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "PropertyValue": {
            "type": "string",
            "description": "Appraised value of the property.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "AnnualIncome": {
            "type": "string",
            "description": "Borrower's annual income.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "EmploymentStatus": {
            "type": "string",
            "description": "Current employment status of the borrower.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "CreditScore": {
            "type": "number",
            "description": "Borrower's credit score.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        },
        "DebtToIncomeRatio": {
            "type": "string",
            "description": "Calculated debt-to-income ratio.",
            "method": "extract",
            "estimateSourceAndConfidence": True
        }
    }
}

MORTGAGE_DEFAULT_PROMPTS = {
    "application_summary": {
        "borrower_profile": """
You are an expert mortgage underwriter.

Given the mortgage application documents, extract a comprehensive borrower profile.

Return STRICT JSON with borrower details, income verification, and initial assessment.
        """
    }
}


# =============================================================================
# PERSONA REGISTRY
# =============================================================================

PERSONA_CONFIGS: Dict[PersonaType, PersonaConfig] = {
    PersonaType.UNDERWRITING: PersonaConfig(
        id="underwriting",
        name="Underwriting",
        description="Life insurance underwriting workbench for processing applications and medical documents",
        icon="📋",
        color="#6366f1",  # Indigo
        field_schema=UNDERWRITING_FIELD_SCHEMA,
        default_prompts=UNDERWRITING_DEFAULT_PROMPTS,
        custom_analyzer_id="underwritingAnalyzer",
        enabled=True,
    ),
    PersonaType.LIFE_HEALTH_CLAIMS: PersonaConfig(
        id="life_health_claims",
        name="Life & Health Claims",
        description="Health insurance claims processing workbench for medical claims, eligibility verification, and benefits adjudication",
        icon="🏥",
        color="#0891b2",  # Cyan
        field_schema=LIFE_HEALTH_CLAIMS_FIELD_SCHEMA,
        default_prompts=LIFE_HEALTH_CLAIMS_DEFAULT_PROMPTS,
        custom_analyzer_id="lifeHealthClaimsAnalyzer",
        enabled=True,
    ),
    PersonaType.AUTOMOTIVE_CLAIMS: PersonaConfig(
        id="automotive_claims",
        name="Automotive Claims",
        description="Multimodal automotive claims workbench for vehicle damage assessment with image, video, and document processing",
        icon="🚗",
        color="#dc2626",  # Red
        field_schema=AUTOMOTIVE_CLAIMS_FIELD_SCHEMA,
        default_prompts=AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS,
        custom_analyzer_id="autoClaimsDocAnalyzer",
        enabled=True,
        image_analyzer_id="autoClaimsImageAnalyzer",
        video_analyzer_id="autoClaimsVideoAnalyzer",
    ),
    # Legacy P&C Claims - alias to Automotive Claims
    PersonaType.PROPERTY_CASUALTY_CLAIMS: PersonaConfig(
        id="property_casualty_claims",
        name="Property & Casualty Claims (Legacy)",
        description="Legacy P&C claims - use Automotive Claims instead",
        icon="🚗",
        color="#dc2626",  # Red
        field_schema=AUTOMOTIVE_CLAIMS_FIELD_SCHEMA,
        default_prompts=AUTOMOTIVE_CLAIMS_DEFAULT_PROMPTS,
        custom_analyzer_id="autoClaimsDocAnalyzer",
        enabled=False,  # Disabled - replaced by Automotive Claims
    ),
    PersonaType.CLAIMS: PersonaConfig(
        id="claims",
        name="Claims (Legacy)",
        description="Legacy claims persona - use Life & Health Claims or Property & Casualty Claims instead",
        icon="🏥",
        color="#0891b2",  # Cyan
        field_schema=CLAIMS_FIELD_SCHEMA,
        default_prompts=CLAIMS_DEFAULT_PROMPTS,
        custom_analyzer_id="claimsAnalyzer",
        enabled=False,  # Disabled - replaced by specific claims personas
    ),
    PersonaType.MORTGAGE: PersonaConfig(
        id="mortgage",
        name="Mortgage",
        description="Mortgage underwriting workbench for loan applications and property documents",
        icon="🏠",
        color="#059669",  # Emerald
        field_schema=MORTGAGE_FIELD_SCHEMA,
        default_prompts=MORTGAGE_DEFAULT_PROMPTS,
        custom_analyzer_id="mortgageAnalyzer",
        enabled=False,  # Coming soon
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_persona_id(persona_id: str) -> str:
    """Normalize persona ID, handling legacy aliases.
    
    Args:
        persona_id: The persona ID to normalize
        
    Returns:
        The normalized persona ID (e.g., 'claims' -> 'life_health_claims')
    """
    if persona_id and persona_id.lower() == 'claims':
        return 'life_health_claims'
    return persona_id


def get_persona_config(persona_id: str) -> PersonaConfig:
    """Get configuration for a specific persona by ID."""
    try:
        # Handle legacy 'claims' mapping to life_health_claims
        persona_id = normalize_persona_id(persona_id)
        persona_type = PersonaType(persona_id.lower())
        return PERSONA_CONFIGS[persona_type]
    except (ValueError, KeyError):
        raise ValueError(f"Unknown persona: {persona_id}. Valid options: {[p.value for p in PersonaType if p != PersonaType.CLAIMS]}")


def list_personas() -> List[Dict[str, Any]]:
    """List all available personas with their metadata."""
    return [
        {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "icon": config.icon,
            "color": config.color,
            "enabled": config.enabled,
        }
        for config in PERSONA_CONFIGS.values()
        if config.id != "claims"  # Exclude legacy claims persona from list
    ]


def get_field_schema(persona_id: str, media_type: str = "document") -> Dict[str, Any]:
    """Get the field extraction schema for a persona.
    
    Args:
        persona_id: The persona ID (e.g., 'automotive_claims')
        media_type: The media type ('document', 'image', or 'video')
    
    Returns:
        The appropriate field schema for the persona and media type
    """
    config = get_persona_config(persona_id)
    
    # For automotive claims, return media-specific schemas
    if persona_id == "automotive_claims":
        if media_type == "image":
            return AUTOMOTIVE_CLAIMS_IMAGE_FIELD_SCHEMA
        elif media_type == "video":
            return AUTOMOTIVE_CLAIMS_VIDEO_FIELD_SCHEMA
    
    # Default to the persona's main field schema
    return config.field_schema


def get_default_prompts(persona_id: str) -> Dict[str, Dict[str, str]]:
    """Get the default prompts for a persona."""
    config = get_persona_config(persona_id)
    return config.default_prompts


def get_custom_analyzer_id(persona_id: str) -> str:
    """Get the custom analyzer ID for a persona."""
    config = get_persona_config(persona_id)
    return config.custom_analyzer_id
