"""Seed data for underwriting applications aligned with Customer 360 narratives."""


def get_underwriting_apps() -> list[dict]:
    """Return a list of dicts, each suitable for creating an ApplicationMetadata object."""
    return [
        _sarah_chen(),
        _marcus_williams(),
        _priya_patel(),
    ]


# ---------------------------------------------------------------------------
# 1. Sarah Chen — Healthy, straightforward approval
# ---------------------------------------------------------------------------


def _sarah_chen() -> dict:
    return {
        "id": "app-sc-uw-001",
        "created_at": "2019-06-15T12:00:00Z",
        "external_reference": "CUST-SC-001",
        "status": "completed",
        "persona": "underwriting",
        "files": [],
        "llm_outputs": {
            "application_summary": {
                "customer_profile": {
                    "section": "application_summary",
                    "subsection": "customer_profile",
                    "summary": "Sarah Chen — Term Life $500K",
                    "raw": (
                        "for a 20-year Term Life policy with a face amount of $500,000. "
                        "She is a non-smoker with a BMI of 22.1 and resides in San "
                        "Francisco, CA. Her occupation is classified as low-risk. "
                        "No adverse lifestyle factors were identified during the "
                        "application process."
                    ),
                    "parsed": {
                        "summary": "Sarah Chen — Term Life $500K",
                        "key_fields": [
                            {"label": "Full Name", "value": "Sarah Chen"},
                            {"label": "Age", "value": "31"},
                            {"label": "Sex", "value": "Female"},
                            {"label": "Smoker Status", "value": "Non-smoker"},
                            {"label": "BMI", "value": "22.1"},
                            {"label": "Occupation", "value": "Software Engineer"},
                            {"label": "Coverage Amount", "value": "$500,000"},
                            {"label": "Product", "value": "Term Life — 20 Year"},
                        ],
                        "risk_assessment": "Low Risk — Standard Plus",
                        "underwriting_action": "Issue at Standard Plus Rates",
                    },
                },
                "existing_policies": {
                    "section": "application_summary",
                    "subsection": "existing_policies",
                    "raw": "No existing policies on file for this applicant.",
                    "parsed": {
                        "summary": "No existing policies found.",
                        "policies": [],
                    },
                },
            },
            "medical_summary": {
                "other_medical_findings": {
                    "section": "medical_summary",
                    "subsection": "other_medical_findings",
                    "raw": (
                        "No significant medical findings were identified during the "
                        "review of submitted medical records and lab results. The "
                        "applicant reports no history of hospitalization, surgery, or "
                        "chronic illness. All routine blood work returned within normal "
                        "reference ranges."
                    ),
                    "parsed": {
                        "summary": "No significant medical findings. All lab results within normal limits.",
                        "key_items": [
                            {
                                "finding": "Complete blood count",
                                "result": "Within normal limits",
                                "significance": "None",
                            },
                            {
                                "finding": "Liver function panel",
                                "result": "Within normal limits",
                                "significance": "None",
                            },
                            {
                                "finding": "Fasting glucose",
                                "result": "4.8 mmol/L (normal < 5.6)",
                                "significance": "None",
                            },
                        ],
                        "risk_assessment": "Low",
                        "underwriting_action": "No action required",
                    },
                },
                "hypertension": {
                    "section": "medical_summary",
                    "subsection": "hypertension",
                    "raw": (
                        "Blood pressure recorded at 118/72 mmHg on paramedical exam, "
                        "which is within the optimal range. No history of hypertension "
                        "or use of antihypertensive medications. No end-organ damage "
                        "indicators present."
                    ),
                    "parsed": {
                        "summary": "No hypertension. Blood pressure 118/72 mmHg — optimal range.",
                        "bp_readings": [
                            {"systolic": 118, "diastolic": 72, "date": "2019-05-20"},
                        ],
                        "key_items": [
                            {
                                "finding": "Blood pressure",
                                "result": "118/72 mmHg",
                                "significance": "Optimal — no further action",
                            },
                        ],
                        "risk_assessment": "Low",
                        "underwriting_action": "No action required",
                    },
                },
                "high_cholesterol": {
                    "section": "medical_summary",
                    "subsection": "high_cholesterol",
                    "raw": (
                        "Total cholesterol measured at 4.2 mmol/L, which falls within "
                        "the desirable range (< 5.2 mmol/L). LDL cholesterol 2.3 mmol/L, "
                        "HDL cholesterol 1.6 mmol/L, triglycerides 0.9 mmol/L. No lipid-"
                        "lowering medications reported."
                    ),
                    "parsed": {
                        "summary": "Cholesterol within desirable range. Total 4.2 mmol/L.",
                        "lipid_panels": [
                            {
                                "total_cholesterol": "4.2 mmol/L",
                                "ldl": "2.3 mmol/L",
                                "hdl": "1.6 mmol/L",
                                "triglycerides": "0.9 mmol/L",
                                "date": "2019-05-20",
                            },
                        ],
                        "key_items": [
                            {
                                "finding": "Total cholesterol",
                                "result": "4.2 mmol/L",
                                "significance": "Desirable (< 5.2)",
                            },
                            {
                                "finding": "LDL cholesterol",
                                "result": "2.3 mmol/L",
                                "significance": "Optimal (< 2.6)",
                            },
                            {
                                "finding": "HDL cholesterol",
                                "result": "1.6 mmol/L",
                                "significance": "Favorable (> 1.0)",
                            },
                            {
                                "finding": "Triglycerides",
                                "result": "0.9 mmol/L",
                                "significance": "Normal (< 1.7)",
                            },
                        ],
                        "risk_assessment": "Low",
                        "underwriting_action": "No action required",
                    },
                },
                "family_history": {
                    "section": "medical_summary",
                    "subsection": "family_history",
                    "raw": (
                        "No significant family medical history reported. Both parents "
                        "are alive and in good health in their early 60s. No family "
                        "history of cancer, heart disease, stroke, or diabetes before "
                        "age 60. One sibling (brother, age 28) reported in good health."
                    ),
                    "parsed": {
                        "summary": "No significant family history. Parents alive and healthy in their 60s.",
                        "key_items": [
                            {
                                "relation": "Father",
                                "age": "63",
                                "status": "Alive, healthy",
                                "conditions": "None reported",
                            },
                            {
                                "relation": "Mother",
                                "age": "61",
                                "status": "Alive, healthy",
                                "conditions": "None reported",
                            },
                            {
                                "relation": "Brother",
                                "age": "28",
                                "status": "Alive, healthy",
                                "conditions": "None reported",
                            },
                        ],
                        "risk_assessment": "Low",
                        "underwriting_action": "No action required",
                    },
                },
                "other_risks": {
                    "section": "medical_summary",
                    "subsection": "other_risks",
                    "raw": (
                        "The applicant reports no tobacco, recreational drug, or "
                        "excessive alcohol use. Alcohol consumption is reported as "
                        "occasional (2-3 drinks per week). No hazardous hobbies or "
                        "activities beyond normal recreational exercise (running, yoga). "
                        "No history of DUI or reckless driving. No foreign travel to "
                        "high-risk regions planned."
                    ),
                    "parsed": {
                        "summary": "No substance use concerns. No hazardous activities.",
                        "key_items": [
                            {
                                "factor": "Alcohol",
                                "detail": "Occasional — 2-3 drinks/week",
                                "risk_level": "None",
                            },
                            {
                                "factor": "Tobacco",
                                "detail": "Never used",
                                "risk_level": "None",
                            },
                            {
                                "factor": "Recreational drugs",
                                "detail": "None reported",
                                "risk_level": "None",
                            },
                            {
                                "factor": "Hazardous activities",
                                "detail": "None — recreational running and yoga",
                                "risk_level": "None",
                            },
                        ],
                        "risk_assessment": "Low",
                        "underwriting_action": "No action required",
                    },
                },
            },
            "requirements": {
                "requirements_summary": {
                    "section": "requirements",
                    "subsection": "requirements_summary",
                    "raw": (
                        "All underwriting requirements have been fulfilled. Blood "
                        "profile, urinalysis, and paramedical exam were completed and "
                        "returned satisfactory results. No outstanding items remain."
                    ),
                    "parsed": {
                        "requirements_list": [
                            {
                                "requirement": "Blood profile",
                                "priority": "Routine",
                                "status": "Completed",
                            },
                            {
                                "requirement": "Urinalysis",
                                "priority": "Routine",
                                "status": "Completed",
                            },
                            {
                                "requirement": "Paramedical exam",
                                "priority": "Routine",
                                "status": "Completed",
                            },
                        ],
                    },
                },
            },
        },
        "extracted_fields": None,
        "confidence_summary": None,
        "risk_analysis": {
            "parsed": {
                "overall_risk_level": "Low",
                "overall_rationale": (
                    "Applicant meets all Standard Plus criteria. No medical, lifestyle, "
                    "or family history concerns identified. Recommend issue at quoted rate."
                ),
                "findings": [
                    {
                        "policy_id": "POL-HEALTH-001",
                        "policy_name": "Standard Health Assessment",
                        "finding": "All health metrics within normal ranges — no medical concerns identified.",
                        "risk_level": "Low",
                    },
                    {
                        "policy_id": "POL-LIFESTYLE-001",
                        "policy_name": "Lifestyle Risk Evaluation",
                        "finding": "Non-smoker, no hazardous activities, minimal alcohol consumption.",
                        "risk_level": "Low",
                    },
                ],
                "premium_recommendation": {
                    "base_decision": "Standard",
                    "loading_percentage": "0%",
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# 2. Marcus Williams — Medium risk, referred for senior review
# ---------------------------------------------------------------------------


def _marcus_williams() -> dict:
    return {
        "id": "app-mw-uw-001",
        "created_at": "2024-02-20T09:30:00Z",
        "external_reference": "CUST-MW-002",
        "status": "completed",
        "persona": "underwriting",
        "files": [],
        "llm_outputs": {
            "application_summary": {
                "customer_profile": {
                    "section": "application_summary",
                    "subsection": "customer_profile",
                    "summary": "Marcus Williams — Whole Life $750K",
                    "raw": (
                        "applying for a Whole Life policy with a face amount of "
                        "$750,000. He is a non-smoker with a BMI of 29.1 (overweight "
                        "category). He currently takes lisinopril 10 mg daily for "
                        "controlled hypertension. Family history is notable for "
                        "cardiac disease on the paternal side."
                    ),
                    "parsed": {
                        "summary": "Marcus Williams — Whole Life $750K",
                        "key_fields": [
                            {"label": "Full Name", "value": "Marcus Williams"},
                            {"label": "Age", "value": "45"},
                            {"label": "Sex", "value": "Male"},
                            {"label": "Smoker Status", "value": "Non-smoker"},
                            {"label": "BMI", "value": "29.1"},
                            {"label": "Occupation", "value": "Financial Analyst"},
                            {"label": "Coverage Amount", "value": "$750,000"},
                            {"label": "Product", "value": "Whole Life"},
                        ],
                        "risk_assessment": "Medium Risk — Refer to Senior Underwriter",
                        "underwriting_action": "Refer for Senior Underwriter Review",
                    },
                },
                "existing_policies": {
                    "section": "application_summary",
                    "subsection": "existing_policies",
                    "raw": (
                        "Applicant holds an existing Group Term Life policy through "
                        "employer with a face amount of $200,000. No individual "
                        "policies on file."
                    ),
                    "parsed": {
                        "summary": "One existing group policy found.",
                        "policies": [
                            {
                                "type": "Group Term Life",
                                "face_amount": "$200,000",
                                "source": "Employer-sponsored",
                                "status": "Active",
                            },
                        ],
                    },
                },
            },
            "medical_summary": {
                "hypertension": {
                    "section": "medical_summary",
                    "subsection": "hypertension",
                    "raw": (
                        "Applicant was diagnosed with Stage 1 hypertension three years "
                        "ago and has been managed on lisinopril 10 mg daily since "
                        "diagnosis. Most recent blood pressure reading was 138/88 mmHg "
                        "on paramedical exam, which remains in the high-normal to mildly "
                        "elevated range. No end-organ damage reported. Echocardiogram "
                        "from 12 months ago showed normal left ventricular function. "
                        "Physician notes indicate stable control with current regimen."
                    ),
                    "parsed": {
                        "summary": (
                            "Controlled hypertension on lisinopril 10 mg. "
                            "BP 138/88 mmHg — mildly elevated, requires monitoring."
                        ),
                        "bp_readings": [
                            {"systolic": 138, "diastolic": 88, "date": "2024-01-15"},
                        ],
                        "key_items": [
                            {
                                "finding": "Blood pressure",
                                "result": "138/88 mmHg",
                                "significance": "Mildly elevated despite medication",
                            },
                            {
                                "finding": "Medication",
                                "result": "Lisinopril 10 mg daily",
                                "significance": "Stable regimen for 3 years",
                            },
                            {
                                "finding": "Echocardiogram",
                                "result": "Normal LV function",
                                "significance": "No end-organ damage",
                            },
                        ],
                        "risk_assessment": "Moderate",
                        "underwriting_action": "Rate as Substandard Table B — monitor BP trend at renewal",
                    },
                },
                "high_cholesterol": {
                    "section": "medical_summary",
                    "subsection": "high_cholesterol",
                    "raw": (
                        "Lipid panel shows borderline elevated values. Total cholesterol "
                        "5.8 mmol/L (borderline high, reference < 5.2). LDL cholesterol "
                        "3.9 mmol/L (above optimal, reference < 3.4). HDL cholesterol "
                        "1.2 mmol/L (borderline low for males, reference > 1.0). "
                        "Triglycerides 1.8 mmol/L (borderline, reference < 1.7). "
                        "No lipid-lowering medication currently prescribed. Physician "
                        "has recommended dietary modifications and increased physical "
                        "activity."
                    ),
                    "parsed": {
                        "summary": (
                            "Borderline elevated lipid panel. Total cholesterol 5.8, "
                            "LDL 3.9, HDL 1.2, triglycerides 1.8 mmol/L."
                        ),
                        "lipid_panels": [
                            {
                                "total_cholesterol": "5.8 mmol/L",
                                "ldl": "3.9 mmol/L",
                                "hdl": "1.2 mmol/L",
                                "triglycerides": "1.8 mmol/L",
                                "date": "2024-01-10",
                            },
                        ],
                        "key_items": [
                            {
                                "finding": "Total cholesterol",
                                "result": "5.8 mmol/L",
                                "significance": "Borderline high (> 5.2)",
                            },
                            {
                                "finding": "LDL cholesterol",
                                "result": "3.9 mmol/L",
                                "significance": "Above optimal (> 3.4)",
                            },
                            {
                                "finding": "HDL cholesterol",
                                "result": "1.2 mmol/L",
                                "significance": "Borderline low for male (> 1.0)",
                            },
                            {
                                "finding": "Triglycerides",
                                "result": "1.8 mmol/L",
                                "significance": "Borderline elevated (> 1.7)",
                            },
                        ],
                        "risk_assessment": "Moderate",
                        "underwriting_action": "Consider statin therapy recommendation; recheck lipids at 6 months",
                    },
                },
                "family_history": {
                    "section": "medical_summary",
                    "subsection": "family_history",
                    "raw": (
                        "Significant paternal cardiac history. Father suffered a "
                        "myocardial infarction at age 58 and underwent coronary artery "
                        "bypass grafting. Father is currently alive at age 72 with "
                        "ongoing cardiac management. Paternal grandfather died of a "
                        "stroke at age 65. Mother is alive and healthy at age 70 with "
                        "no significant medical conditions. One sister (age 42) is "
                        "in good health."
                    ),
                    "parsed": {
                        "summary": (
                            "Significant paternal cardiac history — father MI at 58, "
                            "paternal grandfather stroke at 65."
                        ),
                        "key_items": [
                            {
                                "relation": "Father",
                                "age": "72",
                                "status": "Alive, cardiac management",
                                "conditions": "MI at age 58, CABG",
                            },
                            {
                                "relation": "Paternal grandfather",
                                "age": "Deceased at 65",
                                "status": "Deceased",
                                "conditions": "Stroke at age 65",
                            },
                            {
                                "relation": "Mother",
                                "age": "70",
                                "status": "Alive, healthy",
                                "conditions": "None reported",
                            },
                            {
                                "relation": "Sister",
                                "age": "42",
                                "status": "Alive, healthy",
                                "conditions": "None reported",
                            },
                        ],
                        "risk_assessment": "Elevated",
                        "underwriting_action": (
                            "Family history of premature cardiac disease increases "
                            "cardiovascular risk profile; factor into overall rating"
                        ),
                    },
                },
                "other_medical_findings": {
                    "section": "medical_summary",
                    "subsection": "other_medical_findings",
                    "raw": (
                        "BMI of 29.1 places the applicant in the overweight category "
                        "(reference: 18.5–24.9 normal). Abdominal ultrasound performed "
                        "six months ago identified mild hepatic steatosis (fatty liver) "
                        "consistent with metabolic syndrome features. Liver enzymes "
                        "(ALT 42 U/L, AST 38 U/L) are mildly elevated but within "
                        "acceptable range. No diagnosis of diabetes — HbA1c 5.6%."
                    ),
                    "parsed": {
                        "summary": "Elevated BMI 29.1 with mild hepatic steatosis on imaging.",
                        "key_items": [
                            {
                                "finding": "BMI",
                                "result": "29.1 (overweight)",
                                "significance": "Above normal range; metabolic risk factor",
                            },
                            {
                                "finding": "Hepatic steatosis",
                                "result": "Mild, on abdominal ultrasound",
                                "significance": "Consistent with metabolic syndrome",
                            },
                            {
                                "finding": "Liver enzymes",
                                "result": "ALT 42 U/L, AST 38 U/L",
                                "significance": "Mildly elevated, within acceptable range",
                            },
                            {
                                "finding": "HbA1c",
                                "result": "5.6%",
                                "significance": "Upper normal — pre-diabetic threshold is 5.7%",
                            },
                        ],
                        "risk_assessment": "Moderate",
                        "underwriting_action": "Factor BMI and hepatic steatosis into overall rating; request follow-up labs in 12 months",
                    },
                },
                "other_risks": {
                    "section": "medical_summary",
                    "subsection": "other_risks",
                    "raw": (
                        "Applicant reports moderate alcohol consumption of approximately "
                        "10 standard drinks per week, primarily wine and beer. No "
                        "tobacco use — never smoked. No recreational drug use. "
                        "Occupation is sedentary (desk-based financial analyst). "
                        "No hazardous hobbies reported. Regular exercise limited to "
                        "weekend golf and occasional walking."
                    ),
                    "parsed": {
                        "summary": "Moderate alcohol intake (10 drinks/week). Sedentary occupation.",
                        "key_items": [
                            {
                                "factor": "Alcohol",
                                "detail": "Moderate — approximately 10 drinks/week",
                                "risk_level": "Moderate — at upper boundary of acceptable range",
                            },
                            {
                                "factor": "Tobacco",
                                "detail": "Never used",
                                "risk_level": "None",
                            },
                            {
                                "factor": "Recreational drugs",
                                "detail": "None reported",
                                "risk_level": "None",
                            },
                            {
                                "factor": "Occupation",
                                "detail": "Sedentary desk role — Financial Analyst",
                                "risk_level": "Low (occupational), but contributes to metabolic risk",
                            },
                            {
                                "factor": "Exercise",
                                "detail": "Minimal — weekend golf, occasional walking",
                                "risk_level": "Low activity level; contributes to elevated BMI",
                            },
                        ],
                        "risk_assessment": "Moderate",
                        "underwriting_action": "Note alcohol consumption in file; no exclusion warranted at this level",
                    },
                },
            },
            "requirements": {
                "requirements_summary": {
                    "section": "requirements",
                    "subsection": "requirements_summary",
                    "raw": (
                        "Core requirements are complete. Blood profile and paramedical "
                        "exam have been received. Attending Physician Statement (APS) "
                        "has been obtained and reviewed. Case requires senior underwriter "
                        "review due to the combination of elevated BMI, controlled "
                        "hypertension, borderline lipids, and significant cardiac family "
                        "history."
                    ),
                    "parsed": {
                        "requirements_list": [
                            {
                                "requirement": "Blood profile",
                                "priority": "Routine",
                                "status": "Completed",
                            },
                            {
                                "requirement": "Paramedical exam",
                                "priority": "Routine",
                                "status": "Completed",
                            },
                            {
                                "requirement": "Attending Physician Statement (APS)",
                                "priority": "Required",
                                "status": "Completed",
                            },
                            {
                                "requirement": "Echocardiogram report",
                                "priority": "Required",
                                "status": "Completed",
                            },
                            {
                                "requirement": "Senior underwriter review",
                                "priority": "Required",
                                "status": "Pending",
                            },
                        ],
                    },
                },
            },
        },
        "extracted_fields": None,
        "confidence_summary": None,
        "risk_analysis": {
            "parsed": {
                "overall_risk_level": "Moderate",
                "overall_rationale": (
                    "Multiple moderate risk factors present: controlled hypertension, "
                    "borderline dyslipidemia, elevated BMI with hepatic steatosis, and "
                    "significant paternal cardiac history. Individually manageable, but "
                    "the combination warrants senior underwriter review for appropriate "
                    "rating class determination."
                ),
                "findings": [
                    {
                        "policy_id": "POL-CARDIAC-001",
                        "policy_name": "Cardiac Risk Assessment",
                        "finding": (
                            "Controlled hypertension with family history of premature "
                            "cardiac disease. Father MI at 58, paternal grandfather "
                            "stroke at 65. Elevated cardiovascular risk profile."
                        ),
                        "risk_level": "Moderate",
                    },
                    {
                        "policy_id": "POL-METABOLIC-001",
                        "policy_name": "Metabolic Syndrome Evaluation",
                        "finding": (
                            "BMI 29.1 (overweight), borderline dyslipidemia, mild "
                            "hepatic steatosis. Metabolic syndrome features present."
                        ),
                        "risk_level": "Moderate",
                    },
                    {
                        "policy_id": "POL-LIFESTYLE-001",
                        "policy_name": "Lifestyle Risk Evaluation",
                        "finding": (
                            "Moderate alcohol consumption (10 drinks/week) at upper "
                            "boundary of acceptable range. Sedentary occupation."
                        ),
                        "risk_level": "Low",
                    },
                ],
                "premium_recommendation": {
                    "base_decision": "Rated",
                    "loading_percentage": "+50%",
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# 3. Priya Patel — Medium risk, pending aviation documentation
# ---------------------------------------------------------------------------


def _priya_patel() -> dict:
    return {
        "id": "app-pp-uw-001",
        "created_at": "2024-11-05T14:15:00Z",
        "external_reference": "CUST-PP-003",
        "status": "pending",
        "persona": "underwriting",
        "files": [],
        "llm_outputs": {
            "application_summary": {
                "customer_profile": {
                    "section": "application_summary",
                    "subsection": "customer_profile",
                    "summary": "Priya Patel — Term Life $1M",
                    "raw": (
                        "applying for a 30-year Term Life policy with a face amount of "
                        "$1,000,000. She is a non-smoker with a BMI of 23.4. The "
                        "applicant holds a Private Pilot License (PPL) and flies "
                        "recreationally, which introduces an aviation risk factor "
                        "requiring additional documentation and evaluation."
                    ),
                    "parsed": {
                        "summary": "Priya Patel — Term Life $1M",
                        "key_fields": [
                            {"label": "Full Name", "value": "Priya Patel"},
                            {"label": "Age", "value": "32"},
                            {"label": "Sex", "value": "Female"},
                            {"label": "Smoker Status", "value": "Non-smoker"},
                            {"label": "BMI", "value": "23.4"},
                            {"label": "Occupation", "value": "UX Consultant (Self-Employed)"},
                            {"label": "Coverage Amount", "value": "$1,000,000"},
                            {"label": "Product", "value": "Term Life — 30 Year"},
                        ],
                        "risk_assessment": "Medium Risk — Aviation Hazard",
                        "underwriting_action": "Pending — Awaiting Aviation Documentation",
                    },
                },
                "existing_policies": {
                    "section": "application_summary",
                    "subsection": "existing_policies",
                    "raw": (
                        "No existing individual or group life insurance policies on "
                        "file for this applicant."
                    ),
                    "parsed": {
                        "summary": "No existing policies found.",
                        "policies": [],
                    },
                },
            },
            "medical_summary": {
                "other_medical_findings": {
                    "section": "medical_summary",
                    "subsection": "other_medical_findings",
                    "raw": (
                        "No significant medical findings identified. The applicant "
                        "reports no history of chronic illness, hospitalization, or "
                        "surgery. All routine lab work — complete blood count, metabolic "
                        "panel, liver function, and thyroid panel — returned within "
                        "normal reference ranges. Fasting glucose 4.6 mmol/L. HbA1c "
                        "5.1%. No allergies or adverse drug reactions reported."
                    ),
                    "parsed": {
                        "summary": "No significant medical findings. All lab results normal.",
                        "key_items": [
                            {
                                "finding": "Complete blood count",
                                "result": "Within normal limits",
                                "significance": "None",
                            },
                            {
                                "finding": "Comprehensive metabolic panel",
                                "result": "Within normal limits",
                                "significance": "None",
                            },
                            {
                                "finding": "Fasting glucose",
                                "result": "4.6 mmol/L",
                                "significance": "Normal (< 5.6)",
                            },
                            {
                                "finding": "HbA1c",
                                "result": "5.1%",
                                "significance": "Normal (< 5.7)",
                            },
                            {
                                "finding": "Thyroid panel",
                                "result": "Within normal limits",
                                "significance": "None",
                            },
                        ],
                        "risk_assessment": "Low",
                        "underwriting_action": "No action required",
                    },
                },
                "hypertension": {
                    "section": "medical_summary",
                    "subsection": "hypertension",
                    "raw": (
                        "Blood pressure recorded at 112/68 mmHg on paramedical exam. "
                        "This is well within the optimal range. No history of "
                        "hypertension or use of blood pressure medications."
                    ),
                    "parsed": {
                        "summary": "No hypertension. Blood pressure 112/68 mmHg — optimal.",
                        "bp_readings": [
                            {"systolic": 112, "diastolic": 68, "date": "2024-10-20"},
                        ],
                        "key_items": [
                            {
                                "finding": "Blood pressure",
                                "result": "112/68 mmHg",
                                "significance": "Optimal — no concerns",
                            },
                        ],
                        "risk_assessment": "Low",
                        "underwriting_action": "No action required",
                    },
                },
                "high_cholesterol": {
                    "section": "medical_summary",
                    "subsection": "high_cholesterol",
                    "raw": (
                        "Total cholesterol 4.0 mmol/L, well within the desirable range. "
                        "LDL 2.1 mmol/L (optimal). HDL 1.5 mmol/L (favorable). "
                        "Triglycerides 0.8 mmol/L (normal). No lipid-lowering medication "
                        "in use. Lipid profile is excellent across all markers."
                    ),
                    "parsed": {
                        "summary": "Excellent lipid profile. Total cholesterol 4.0 mmol/L.",
                        "lipid_panels": [
                            {
                                "total_cholesterol": "4.0 mmol/L",
                                "ldl": "2.1 mmol/L",
                                "hdl": "1.5 mmol/L",
                                "triglycerides": "0.8 mmol/L",
                                "date": "2024-10-20",
                            },
                        ],
                        "key_items": [
                            {
                                "finding": "Total cholesterol",
                                "result": "4.0 mmol/L",
                                "significance": "Desirable (< 5.2)",
                            },
                            {
                                "finding": "LDL cholesterol",
                                "result": "2.1 mmol/L",
                                "significance": "Optimal (< 2.6)",
                            },
                            {
                                "finding": "HDL cholesterol",
                                "result": "1.5 mmol/L",
                                "significance": "Favorable (> 1.0)",
                            },
                            {
                                "finding": "Triglycerides",
                                "result": "0.8 mmol/L",
                                "significance": "Normal (< 1.7)",
                            },
                        ],
                        "risk_assessment": "Low",
                        "underwriting_action": "No action required",
                    },
                },
                "family_history": {
                    "section": "medical_summary",
                    "subsection": "family_history",
                    "raw": (
                        "No significant family medical history. Father is alive and "
                        "healthy at age 60. Mother is alive and healthy at age 57. "
                        "One brother (age 29) in good health. No family history of "
                        "cancer, heart disease, stroke, diabetes, or mental illness "
                        "before age 60."
                    ),
                    "parsed": {
                        "summary": "No significant family history.",
                        "key_items": [
                            {
                                "relation": "Father",
                                "age": "60",
                                "status": "Alive, healthy",
                                "conditions": "None reported",
                            },
                            {
                                "relation": "Mother",
                                "age": "57",
                                "status": "Alive, healthy",
                                "conditions": "None reported",
                            },
                            {
                                "relation": "Brother",
                                "age": "29",
                                "status": "Alive, healthy",
                                "conditions": "None reported",
                            },
                        ],
                        "risk_assessment": "Low",
                        "underwriting_action": "No action required",
                    },
                },
                "other_risks": {
                    "section": "medical_summary",
                    "subsection": "other_risks",
                    "raw": (
                        "The primary risk factor for this applicant is recreational "
                        "aviation. She holds a Private Pilot License (PPL) with "
                        "approximately 120 total flight hours logged. She flies a "
                        "single-engine Cessna 172 approximately twice per month from "
                        "a local general aviation airport. She does not fly "
                        "commercially or for hire. No instrument rating — VFR only. "
                        "An aviation medical certificate (FAA Class 3) is required to "
                        "complete the underwriting evaluation. Depending on flight "
                        "hours, aircraft type, and medical clearance, a flat extra "
                        "premium of $2.50–$5.00 per thousand or an aviation exclusion "
                        "rider may be applied. No other hazardous activities, substance "
                        "use, or lifestyle risk factors were identified."
                    ),
                    "parsed": {
                        "summary": (
                            "Recreational pilot — PPL holder, ~120 flight hours, "
                            "single-engine Cessna 172. Aviation risk requires additional "
                            "documentation and potential flat extra premium."
                        ),
                        "key_items": [
                            {
                                "factor": "Aviation — Private Pilot",
                                "detail": (
                                    "PPL holder, ~120 flight hours, flies Cessna 172 "
                                    "approximately twice/month, VFR only"
                                ),
                                "risk_level": "Moderate — requires aviation medical and flat extra or exclusion rider",
                            },
                            {
                                "factor": "Alcohol",
                                "detail": "Occasional — 1-2 drinks/week",
                                "risk_level": "None",
                            },
                            {
                                "factor": "Tobacco",
                                "detail": "Never used",
                                "risk_level": "None",
                            },
                            {
                                "factor": "Recreational drugs",
                                "detail": "None reported",
                                "risk_level": "None",
                            },
                        ],
                        "risk_assessment": "Moderate",
                        "underwriting_action": (
                            "Obtain aviation medical certificate (FAA Class 3) and "
                            "detailed flight log. Evaluate for flat extra premium "
                            "$2.50–$5.00 per thousand or aviation exclusion rider."
                        ),
                    },
                },
            },
            "requirements": {
                "requirements_summary": {
                    "section": "requirements",
                    "subsection": "requirements_summary",
                    "raw": (
                        "Blood profile, urinalysis, and paramedical exam have been "
                        "completed with satisfactory results. However, due to the "
                        "applicant's recreational pilot status, additional documentation "
                        "is required before the case can proceed to final decision. An "
                        "aviation medical certificate (FAA Class 3) and a detailed "
                        "flight log covering the past 12 months must be submitted."
                    ),
                    "parsed": {
                        "requirements_list": [
                            {
                                "requirement": "Blood profile",
                                "priority": "Routine",
                                "status": "Completed",
                            },
                            {
                                "requirement": "Urinalysis",
                                "priority": "Routine",
                                "status": "Completed",
                            },
                            {
                                "requirement": "Paramedical exam",
                                "priority": "Routine",
                                "status": "Completed",
                            },
                            {
                                "requirement": "Aviation medical certificate (FAA Class 3)",
                                "priority": "Required",
                                "status": "Pending",
                            },
                            {
                                "requirement": "Detailed flight log — past 12 months",
                                "priority": "Required",
                                "status": "Pending",
                            },
                        ],
                    },
                },
            },
        },
        "extracted_fields": None,
        "confidence_summary": None,
        "risk_analysis": {
            "parsed": {
                "overall_risk_level": "Moderate",
                "overall_rationale": (
                    "Medical profile is excellent and would qualify for Preferred rates. "
                    "However, recreational aviation introduces a hazardous activity risk "
                    "factor. Final decision and rating class cannot be determined until "
                    "the aviation medical certificate and flight log are received and "
                    "reviewed. Anticipated outcome: Standard rates plus flat extra "
                    "premium for aviation, or aviation exclusion rider."
                ),
                "findings": [
                    {
                        "policy_id": "POL-HEALTH-001",
                        "policy_name": "Standard Health Assessment",
                        "finding": "All health metrics within normal ranges — excellent medical profile.",
                        "risk_level": "Low",
                    },
                    {
                        "policy_id": "POL-AVIATION-001",
                        "policy_name": "Aviation Hazard Assessment",
                        "finding": (
                            "Private Pilot License holder with ~120 flight hours, "
                            "flying single-engine Cessna 172 approximately twice per "
                            "month. VFR only. Requires aviation medical certificate "
                            "and flight log for final determination."
                        ),
                        "risk_level": "Moderate",
                    },
                ],
                "premium_recommendation": {
                    "base_decision": "Standard",
                    "loading_percentage": "+$2.50–$5.00 per thousand (flat extra)",
                },
            },
        },
    }
