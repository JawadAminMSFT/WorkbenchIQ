"""Seed data for 3 claims applications (1 health + 2 automotive).

Provides rich, realistic data matching the Customer 360 narratives.
"""

from typing import Any, Dict, List


def _sarah_chen_auto() -> Dict[str, Any]:
    """Sarah Chen — minor rear-end collision, other party at fault."""
    return {
        "id": "app-sc-auto-001",
        "created_at": "2024-11-18T14:32:00Z",
        "external_reference": "CUST-SC-001",
        "status": "completed",
        "persona": "automotive_claims",
        "files": [
            {"filename": "claim_form.pdf", "path": "applications/app-sc-auto-001/claim_form.pdf", "content_type": "application/pdf", "media_type": "document"},
            {"filename": "police_report.pdf", "path": "applications/app-sc-auto-001/police_report.pdf", "content_type": "application/pdf", "media_type": "document"},
            {"filename": "rear_bumper_photo.jpg", "path": "applications/app-sc-auto-001/rear_bumper_photo.jpg", "content_type": "image/jpeg", "media_type": "image"},
            {"filename": "trunk_lid_photo.jpg", "path": "applications/app-sc-auto-001/trunk_lid_photo.jpg", "content_type": "image/jpeg", "media_type": "image"},
            {"filename": "repair_estimate.pdf", "path": "applications/app-sc-auto-001/repair_estimate.pdf", "content_type": "application/pdf", "media_type": "document"},
        ],
        "llm_outputs": {
            "damage_assessment": {
                "visual_damage_analysis": {
                    "section": "damage_assessment",
                    "subsection": "visual_damage_analysis",
                    "raw": (
                        "Insured vehicle is a 2021 Honda CR-V photographed at Maple Auto Body. "
                        "Impact is localized to the rear of the vehicle. The rear bumper cover shows "
                        "moderate deformation with cracking along the lower edge and paint transfer "
                        "from the striking vehicle. The trunk lid has a visible buckle along the "
                        "trailing edge with minor paint flaking. No structural intrusion to the "
                        "passenger compartment. Tail lights intact. Exhaust system undamaged."
                    ),
                    "parsed": {
                        "summary": "Moderate rear-end impact damage confined to bumper cover and trunk lid. Consistent with low-speed rear-end collision.",
                        "damage_areas": [
                            {"area": "Rear bumper cover", "severity": "moderate", "description": "Deformation and cracking along lower edge with paint transfer from striking vehicle"},
                            {"area": "Trunk lid", "severity": "minor", "description": "Buckle along trailing edge with minor paint flaking; latch mechanism functional"},
                            {"area": "Rear bumper reinforcement bar", "severity": "minor", "description": "Slight bend detected; replacement recommended"},
                        ],
                        "total_damage_estimate_CAD": 3200.00,
                        "airbag_deployment": False,
                        "vehicle_drivable": True,
                        "recommended_action": "Approve repair",
                    },
                },
                "estimate_validation": {
                    "section": "damage_assessment",
                    "subsection": "estimate_validation",
                    "raw": (
                        "Repair estimate from Maple Auto Body reviewed against Mitchell benchmarks. "
                        "Parts pricing for 2021 Honda CR-V rear bumper cover, reinforcement bar, and "
                        "trunk lid are within OEM list pricing. Labour hours at 8.5 hours align with "
                        "industry standard for R&I bumper assembly, refinish, and trunk lid replacement. "
                        "Paint and materials allowance reasonable. No aftermarket parts substitutions noted."
                    ),
                    "parsed": {
                        "summary": "Estimate is reasonable and within market range for the described repairs on a 2021 Honda CR-V.",
                        "estimate_id": "EST-SC-2024-0472",
                        "parts_breakdown_CAD": 1800.00,
                        "labor_hours": 8.5,
                        "labor_rate_per_hour": 95.00,
                        "labor_cost_CAD": 807.50,
                        "sublet_items": [],
                        "paint_materials_CAD": 592.50,
                        "estimate_accuracy": "Reasonable",
                        "comparison_market": "Within market range",
                        "recommended_action": "Approve",
                    },
                },
            },
            "liability_assessment": {
                "fault_determination": {
                    "section": "liability_assessment",
                    "subsection": "fault_determination",
                    "raw": (
                        "Police report PR-2024-TPS-88214 confirms the insured vehicle was stationary "
                        "at a red light at the intersection of King St and Bay St when struck from "
                        "behind by a 2019 Toyota Camry. Witness statements from two bystanders "
                        "corroborate that the other driver failed to stop in time. Other driver cited "
                        "for careless driving under HTA s.130. No contributing factors from insured."
                    ),
                    "parsed": {
                        "summary": "Clear liability determination: insured 0% at fault; other party 100% at fault, confirmed by police report and witnesses.",
                        "point_of_impact": "Rear of insured vehicle",
                        "contributing_factors": ["Other driver following too closely", "Other driver cited for careless driving"],
                        "fault_determination": "0% — other party 100% at fault",
                        "police_report_status": "Obtained — confirms other party fault",
                        "witness_statements": "Two independent witnesses corroborate insured account",
                        "liability_risk": "Clear liability",
                    },
                },
            },
            "fraud_detection": {
                "red_flag_analysis": {
                    "section": "fraud_detection",
                    "subsection": "red_flag_analysis",
                    "raw": (
                        "No fraud indicators detected for this claim. Damage pattern is fully "
                        "consistent with the described rear-end collision. Reporting was prompt "
                        "(same day). Police report obtained and corroborates claimant's account. "
                        "No prior claims history of concern. Repair estimate is within market norms. "
                        "No relationship between parties identified."
                    ),
                    "parsed": {
                        "summary": "No fraud indicators detected. Claim circumstances, damage pattern, and documentation are consistent and credible.",
                        "red_flags": [],
                        "fraud_risk": "Low",
                        "fraud_score": 0.08,
                        "recommended_action": "Proceed with claim",
                    },
                },
            },
            "payout_recommendation": {
                "settlement_analysis": {
                    "section": "payout_recommendation",
                    "subsection": "settlement_analysis",
                    "raw": (
                        "Recommended settlement of $3,200 CAD for repair of rear bumper, reinforcement "
                        "bar, and trunk lid. Insured carries a $500 deductible; however, since the "
                        "insured is 0% at fault, subrogation will be initiated against the other "
                        "party's insurer (Aviva Canada, policy AV-2019-8827341) to recover the full "
                        "payout plus deductible. No injury claim component."
                    ),
                    "parsed": {
                        "summary": "Approve full repair payout of $3,200. Subrogation to recover from at-fault party's insurer.",
                        "recommended_payout_CAD": 3200.00,
                        "deductible_CAD": 500.00,
                        "insured_responsibility_CAD": 0.00,
                        "subrogation_target": "Aviva Canada — policy AV-2019-8827341",
                        "final_approval": True,
                        "rationale": "Insured not at fault. Damage verified, estimate reasonable. Subrogation initiated to recover full amount from other party's insurer.",
                    },
                },
            },
        },
        "extracted_fields": {
            "claim_form:ClaimNumber": {"field_name": "ClaimNumber", "value": "CLM-SC-241118-01", "confidence": 0.95, "source_file": "claim_form.pdf"},
            "claim_form:PolicyNumber": {"field_name": "PolicyNumber", "value": "AUTO-ON-7724519", "confidence": 0.97, "source_file": "claim_form.pdf"},
            "claim_form:InsuredName": {"field_name": "InsuredName", "value": "Sarah Chen", "confidence": 0.98, "source_file": "claim_form.pdf"},
            "claim_form:DateOfLoss": {"field_name": "DateOfLoss", "value": "2024-11-15", "confidence": 0.96, "source_file": "claim_form.pdf"},
            "claim_form:VehicleYear": {"field_name": "VehicleYear", "value": "2021", "confidence": 0.97, "source_file": "claim_form.pdf"},
            "claim_form:VehicleMake": {"field_name": "VehicleMake", "value": "Honda", "confidence": 0.96, "source_file": "claim_form.pdf"},
            "claim_form:VehicleModel": {"field_name": "VehicleModel", "value": "CR-V", "confidence": 0.96, "source_file": "claim_form.pdf"},
            "claim_form:VehicleVIN": {"field_name": "VehicleVIN", "value": "2HKRW2H53MH604218", "confidence": 0.93, "source_file": "claim_form.pdf"},
            "claim_form:DamageDescription": {"field_name": "DamageDescription", "value": "Rear bumper and trunk lid damage from rear-end collision", "confidence": 0.92, "source_file": "claim_form.pdf"},
            "claim_form:RepairEstimate": {"field_name": "RepairEstimate", "value": "3200.00", "confidence": 0.95, "source_file": "repair_estimate.pdf"},
            "police_report:ReportNumber": {"field_name": "ReportNumber", "value": "PR-2024-TPS-88214", "confidence": 0.94, "source_file": "police_report.pdf"},
            "police_report:OtherPartyInsurer": {"field_name": "OtherPartyInsurer", "value": "Aviva Canada", "confidence": 0.91, "source_file": "police_report.pdf"},
        },
        "confidence_summary": {
            "total_fields": 12,
            "average_confidence": 0.95,
            "high_confidence_count": 11,
            "medium_confidence_count": 1,
            "low_confidence_count": 0,
            "high_confidence_fields": [
                {"name": "claim_form:InsuredName", "confidence": 0.98},
                {"name": "claim_form:PolicyNumber", "confidence": 0.97},
                {"name": "claim_form:VehicleYear", "confidence": 0.97},
                {"name": "claim_form:VehicleMake", "confidence": 0.96},
                {"name": "claim_form:VehicleModel", "confidence": 0.96},
                {"name": "claim_form:DateOfLoss", "confidence": 0.96},
                {"name": "claim_form:ClaimNumber", "confidence": 0.95},
                {"name": "claim_form:RepairEstimate", "confidence": 0.95},
                {"name": "police_report:ReportNumber", "confidence": 0.94},
                {"name": "claim_form:VehicleVIN", "confidence": 0.93},
                {"name": "claim_form:DamageDescription", "confidence": 0.92},
            ],
            "medium_confidence_fields": [
                {"name": "police_report:OtherPartyInsurer", "confidence": 0.91},
            ],
            "low_confidence_fields": [],
        },
    }


def _marcus_williams_health() -> Dict[str, Any]:
    """Marcus Williams — cardiac workup, all services approved."""
    return {
        "id": "app-mw-hc-001",
        "created_at": "2023-07-10T09:15:00Z",
        "external_reference": "CUST-MW-002",
        "status": "completed",
        "persona": "life_health_claims",
        "files": [
            {"filename": "claim_form_health.pdf", "path": "applications/app-mw-hc-001/claim_form_health.pdf", "content_type": "application/pdf", "media_type": "document"},
            {"filename": "eob_statement.pdf", "path": "applications/app-mw-hc-001/eob_statement.pdf", "content_type": "application/pdf", "media_type": "document"},
            {"filename": "cardiology_notes.pdf", "path": "applications/app-mw-hc-001/cardiology_notes.pdf", "content_type": "application/pdf", "media_type": "document"},
            {"filename": "lab_results.pdf", "path": "applications/app-mw-hc-001/lab_results.pdf", "content_type": "application/pdf", "media_type": "document"},
        ],
        "llm_outputs": {
            "clinical_case_notes": {
                "reason_for_visit": {
                    "section": "clinical_case_notes",
                    "subsection": "reason_for_visit",
                    "raw": (
                        "Marcus Williams, 47-year-old male, presented to Dr. Anita Reddy (Cardiology) "
                        "on 2023-06-05 for evaluation of episodic chest tightness and exertional dyspnea. "
                        "Symptoms began approximately 3 months prior and occurred primarily with moderate "
                        "physical activity such as climbing stairs or brisk walking. Patient has a known "
                        "history of essential hypertension (diagnosed 2018) managed with lisinopril 20 mg "
                        "daily, and hyperlipidemia managed with atorvastatin 40 mg daily. Family history "
                        "significant for paternal MI at age 58. No prior cardiac events."
                    ),
                    "parsed": {
                        "summary": "Patient presented for cardiac evaluation following episodes of chest discomfort.",
                        "chief_complaint": "Episodic chest tightness and shortness of breath on exertion",
                        "symptom_duration": "Intermittent over 3 months",
                        "severity": "Moderate",
                        "urgency": "Semi-Urgent",
                        "history_of_present_illness": (
                            "47-year-old male with HTN and hyperlipidemia presenting with 3-month history "
                            "of exertional chest tightness and dyspnea. Episodes occur with moderate activity, "
                            "resolve with rest within 5 minutes. No rest pain, syncope, or palpitations. "
                            "Family history of premature CAD. Current medications: lisinopril 20 mg, "
                            "atorvastatin 40 mg."
                        ),
                    },
                },
                "key_diagnoses": {
                    "section": "clinical_case_notes",
                    "subsection": "key_diagnoses",
                    "raw": (
                        "Following complete cardiac workup including stress test and echocardiogram, "
                        "primary diagnosis is hypertensive heart disease with mild left ventricular "
                        "hypertrophy (LVH). Stress test was negative for ischemia with adequate exercise "
                        "tolerance. Echocardiogram confirmed concentric LVH with preserved ejection "
                        "fraction (EF 60%). Lipid panel showed LDL 142 mg/dL, above target. ICD-10 codes "
                        "assigned: I11.9, I10, E78.5."
                    ),
                    "parsed": {
                        "summary": "Mild LVH consistent with long-standing hypertension. No ischemic heart disease. Hyperlipidemia above target.",
                        "primary_diagnosis": "I11.9 — Hypertensive heart disease without heart failure",
                        "secondary_diagnoses": ["I10 — Essential hypertension", "E78.5 — Hyperlipidemia"],
                        "diagnosis_consistency": "Yes",
                        "coding_accuracy": "Accurate",
                    },
                },
                "medical_necessity": {
                    "section": "clinical_case_notes",
                    "subsection": "medical_necessity",
                    "raw": (
                        "All services provided are medically necessary given the patient's cardiac risk "
                        "profile. A 47-year-old male with hypertension, hyperlipidemia, family history "
                        "of premature CAD, and new-onset exertional symptoms warrants a comprehensive "
                        "cardiac evaluation. The stress test was appropriate to rule out ischemia. The "
                        "echocardiogram was indicated to assess structural changes from long-standing "
                        "hypertension. Lab work was necessary for lipid monitoring and metabolic assessment. "
                        "Follow-up visit for medication adjustment was clinically appropriate."
                    ),
                    "parsed": {
                        "summary": "All services medically necessary given cardiac risk profile.",
                        "necessity_determination": "Necessary",
                        "clinical_rationale": (
                            "Patient's combination of exertional symptoms, hypertension, hyperlipidemia, "
                            "and family history of premature CAD justifies a full cardiac workup including "
                            "stress test, echocardiogram, and laboratory evaluation. Follow-up for medication "
                            "titration is standard of care."
                        ),
                        "services_reviewed": [
                            {"service": "Office Visit — Level 4", "code": "99214", "necessity_status": "Necessary", "rationale": "Complex cardiac risk assessment with multiple comorbidities"},
                            {"service": "Stress Test", "code": "93015", "necessity_status": "Necessary", "rationale": "Rule out ischemia given exertional symptoms and risk factors"},
                            {"service": "Echocardiogram", "code": "93306", "necessity_status": "Necessary", "rationale": "Evaluate cardiac structure given long-standing hypertension"},
                            {"service": "Lab Panel", "code": "80061", "necessity_status": "Necessary", "rationale": "Lipid panel monitoring and metabolic assessment"},
                            {"service": "Follow-up Visit", "code": "99213", "necessity_status": "Necessary", "rationale": "Review results and adjust antihypertensive and statin therapy"},
                        ],
                        "documentation_quality": "Adequate",
                        "recommended_action": "Approve all services",
                    },
                },
            },
            "clinical_timeline": {
                "treatment_timeline": {
                    "section": "clinical_timeline",
                    "subsection": "treatment_timeline",
                    "raw": (
                        "Treatment spanned 30 days from initial consultation to follow-up. "
                        "2023-06-05: Initial cardiology consultation with resting EKG showing LVH pattern. "
                        "2023-06-12: Exercise stress test on treadmill, Bruce protocol — 10 minutes, "
                        "negative for ischemia, adequate heart rate response. 2023-06-19: Transthoracic "
                        "echocardiogram showing concentric LVH, EF 60%, no valvular abnormalities. "
                        "2023-06-26: Fasting lab draw — lipid panel, CMP, CBC. 2023-07-05: Follow-up "
                        "visit, lisinopril increased to 40 mg, atorvastatin increased to 80 mg, lifestyle "
                        "counseling provided."
                    ),
                    "parsed": {
                        "summary": "Diagnostic cardiac workup completed over 30 days with appropriate sequencing of tests and timely follow-up.",
                        "timeline_events": [
                            {"date": "2023-06-05", "event": "Initial cardiac consultation with EKG", "duration_days": 0},
                            {"date": "2023-06-12", "event": "Exercise stress test — negative for ischemia", "duration_days": 7},
                            {"date": "2023-06-19", "event": "Echocardiogram — mild LVH detected", "duration_days": 14},
                            {"date": "2023-06-26", "event": "Lab work — lipid panel, metabolic panel", "duration_days": 21},
                            {"date": "2023-07-05", "event": "Follow-up with cardiologist — medication adjusted", "duration_days": 30},
                        ],
                        "total_duration": 30,
                        "treatment_pattern": "Episodic — diagnostic workup",
                    },
                },
            },
            "benefits_policy": {
                "eligibility_verification": {
                    "section": "benefits_policy",
                    "subsection": "eligibility_verification",
                    "raw": (
                        "Member Marcus Williams (MEM-MW-47892) verified as active under group "
                        "GRP-FIN-6621 (Meridian Financial Services). HealthPlus Preferred PPO plan "
                        "effective 2021-03-01 with no termination date through 2024-12-31. All services "
                        "rendered by in-network providers. No coordination of benefits required. "
                        "Member in good standing with premiums current."
                    ),
                    "parsed": {
                        "summary": "Member eligible for all claimed services.",
                        "eligibility_status": "Eligible",
                        "member_info": {"name": "Marcus Williams", "member_id": "MEM-MW-47892", "group": "GRP-FIN-6621"},
                        "coverage_dates": {"effective_date": "2021-03-01", "termination_date": "2024-12-31"},
                        "plan_details": {"plan_name": "HealthPlus Preferred PPO", "plan_type": "PPO", "network_status": "In-Network"},
                        "eligibility_issues": [],
                        "processing_action": "Proceed",
                    },
                },
                "exclusions_limitations": {
                    "section": "benefits_policy",
                    "subsection": "exclusions_limitations",
                    "raw": (
                        "No applicable exclusions or limitations identified for this claim. "
                        "Cardiac diagnostic services are covered under the plan's preventive and "
                        "diagnostic benefit category. Hypertension was first diagnosed in 2018 while "
                        "the member has been continuously covered since 2021-03-01, so pre-existing "
                        "condition clauses do not apply. No waiting periods for diagnostic services."
                    ),
                    "parsed": {
                        "summary": "No applicable exclusions or limitations.",
                        "applicable_exclusions": [],
                        "pre_existing_review": "Not applicable — condition onset during coverage period",
                        "waiting_periods": "None applicable",
                        "processing_action": "Approve",
                    },
                },
                "benefit_limits": {
                    "section": "benefits_policy",
                    "subsection": "benefit_limits",
                    "raw": (
                        "Member has utilized 4 specialist visits year-to-date against a plan maximum "
                        "of 30. Annual benefit maximum of $75,000 with $2,340 utilized prior to this "
                        "claim. Annual deductible of $750 has been met. Out-of-pocket maximum is $6,500 "
                        "with $1,120 applied year-to-date. All services fall within benefit limits."
                    ),
                    "parsed": {
                        "summary": "All services within benefit limits.",
                        "applicable_limits": {"max_visits": 30, "max_amount": 75000},
                        "deductible_status": "Met for year",
                        "oop_maximum": 6500,
                        "limit_concerns": [],
                        "processing_action": "Approve",
                    },
                },
            },
            "claim_line_evaluation": {
                "line_item_review": {
                    "section": "claim_line_evaluation",
                    "subsection": "line_item_review",
                    "raw": (
                        "Five claim lines reviewed. All CPT codes are appropriate for the documented "
                        "services. Office visit Level 4 (99214) supported by complexity of cardiac "
                        "risk assessment. Stress test (93015) and echocardiogram (93306) are distinct "
                        "procedures performed on separate dates — no bundling concerns. Lab panel "
                        "(80061) is the standard lipid panel code. Follow-up coded as Level 3 (99213) "
                        "which is appropriate for a results-review visit. All billed amounts reduced "
                        "to allowed amounts per PPO fee schedule. Member responsibility is 10% "
                        "coinsurance after deductible."
                    ),
                    "parsed": {
                        "summary": "All 5 claim lines reviewed and approved.",
                        "total_billed": 4800.00,
                        "total_allowed": 4200.00,
                        "total_plan_pays": 3780.00,
                        "total_member_pays": 420.00,
                        "claim_lines": [
                            {"line_num": 1, "description": "Office Visit — Level 4", "code": "99214", "billed": 285.00, "allowed": 250.00, "plan_pays": 225.00, "member_pays": 25.00, "status": "Approved"},
                            {"line_num": 2, "description": "Exercise Stress Test", "code": "93015", "billed": 1450.00, "allowed": 1200.00, "plan_pays": 1080.00, "member_pays": 120.00, "status": "Approved"},
                            {"line_num": 3, "description": "Echocardiogram", "code": "93306", "billed": 1580.00, "allowed": 1400.00, "plan_pays": 1260.00, "member_pays": 140.00, "status": "Approved"},
                            {"line_num": 4, "description": "Comprehensive Lab Panel", "code": "80061", "billed": 765.00, "allowed": 650.00, "plan_pays": 585.00, "member_pays": 65.00, "status": "Approved"},
                            {"line_num": 5, "description": "Follow-up Visit — Level 3", "code": "99213", "billed": 720.00, "allowed": 700.00, "plan_pays": 630.00, "member_pays": 70.00, "status": "Approved"},
                        ],
                        "coding_issues": [],
                        "bundling_flags": [],
                        "recommended_action": "Approve all lines",
                    },
                },
            },
            "tasks_decisions": {
                "final_decision": {
                    "section": "tasks_decisions",
                    "subsection": "final_decision",
                    "raw": (
                        "Claim HC-MW-230710-01 is approved in full. All five service lines are "
                        "medically necessary, correctly coded, and within plan benefits. Member is "
                        "eligible and in-network. No exclusions or limitations apply. Total plan "
                        "payment of $3,780.00 to be issued to Lakeview Cardiology Associates. "
                        "Member responsibility of $420.00 (10% coinsurance). EOB to be mailed to "
                        "member within 5 business days."
                    ),
                    "parsed": {
                        "summary": "Claim approved in full. All services medically necessary and within plan benefits.",
                        "decision": "Approved",
                        "decision_rationale": (
                            "All services are medically necessary for a 47-year-old male with exertional "
                            "symptoms, hypertension, hyperlipidemia, and family history of premature CAD. "
                            "Coding is accurate, no bundling issues, and all providers are in-network. "
                            "Member is eligible with deductible met."
                        ),
                        "payment_summary": {"total_plan_pays": 3780.00, "total_member_pays": 420.00, "deductible_applied": 0},
                        "denial_reasons": [],
                        "pend_reasons": [],
                        "appeal_rights": "Member may appeal within 30 days of EOB",
                        "next_steps": ["Issue payment to provider", "Send EOB to member"],
                        "reviewer_notes": "All documentation complete. Cardiac evaluation appropriate given risk factors.",
                    },
                },
            },
        },
        "extracted_fields": {
            "claim_form:ClaimNumber": {"field_name": "ClaimNumber", "value": "HC-MW-230710-01", "confidence": 0.96, "source_file": "claim_form_health.pdf"},
            "claim_form:MemberName": {"field_name": "MemberName", "value": "Marcus Williams", "confidence": 0.98, "source_file": "claim_form_health.pdf"},
            "claim_form:MemberID": {"field_name": "MemberID", "value": "MEM-MW-47892", "confidence": 0.97, "source_file": "claim_form_health.pdf"},
            "claim_form:GroupNumber": {"field_name": "GroupNumber", "value": "GRP-FIN-6621", "confidence": 0.96, "source_file": "claim_form_health.pdf"},
            "claim_form:PlanName": {"field_name": "PlanName", "value": "HealthPlus Preferred PPO", "confidence": 0.95, "source_file": "claim_form_health.pdf"},
            "claim_form:DiagnosisCode": {"field_name": "DiagnosisCode", "value": "I11.9", "confidence": 0.97, "source_file": "claim_form_health.pdf"},
            "claim_form:DiagnosisDescription": {"field_name": "DiagnosisDescription", "value": "Hypertensive heart disease without heart failure", "confidence": 0.94, "source_file": "claim_form_health.pdf"},
            "claim_form:ServiceDateFrom": {"field_name": "ServiceDateFrom", "value": "2023-06-05", "confidence": 0.96, "source_file": "claim_form_health.pdf"},
            "claim_form:ServiceDateTo": {"field_name": "ServiceDateTo", "value": "2023-07-05", "confidence": 0.95, "source_file": "claim_form_health.pdf"},
            "claim_form:TotalBilled": {"field_name": "TotalBilled", "value": "4800.00", "confidence": 0.97, "source_file": "claim_form_health.pdf"},
            "claim_form:ProviderName": {"field_name": "ProviderName", "value": "Lakeview Cardiology Associates", "confidence": 0.93, "source_file": "claim_form_health.pdf"},
            "claim_form:ProviderNPI": {"field_name": "ProviderNPI", "value": "1467823590", "confidence": 0.92, "source_file": "claim_form_health.pdf"},
            "claim_form:RenderingPhysician": {"field_name": "RenderingPhysician", "value": "Dr. Anita Reddy, MD, FACC", "confidence": 0.94, "source_file": "cardiology_notes.pdf"},
            "eob:TotalAllowed": {"field_name": "TotalAllowed", "value": "4200.00", "confidence": 0.96, "source_file": "eob_statement.pdf"},
            "eob:PlanPays": {"field_name": "PlanPays", "value": "3780.00", "confidence": 0.96, "source_file": "eob_statement.pdf"},
            "eob:MemberPays": {"field_name": "MemberPays", "value": "420.00", "confidence": 0.95, "source_file": "eob_statement.pdf"},
        },
        "confidence_summary": {
            "total_fields": 16,
            "average_confidence": 0.95,
            "high_confidence_count": 14,
            "medium_confidence_count": 2,
            "low_confidence_count": 0,
            "high_confidence_fields": [
                {"name": "claim_form:MemberName", "confidence": 0.98},
                {"name": "claim_form:MemberID", "confidence": 0.97},
                {"name": "claim_form:DiagnosisCode", "confidence": 0.97},
                {"name": "claim_form:TotalBilled", "confidence": 0.97},
                {"name": "claim_form:ClaimNumber", "confidence": 0.96},
                {"name": "claim_form:GroupNumber", "confidence": 0.96},
                {"name": "claim_form:ServiceDateFrom", "confidence": 0.96},
                {"name": "eob:TotalAllowed", "confidence": 0.96},
                {"name": "eob:PlanPays", "confidence": 0.96},
                {"name": "claim_form:PlanName", "confidence": 0.95},
                {"name": "claim_form:ServiceDateTo", "confidence": 0.95},
                {"name": "eob:MemberPays", "confidence": 0.95},
                {"name": "claim_form:DiagnosisDescription", "confidence": 0.94},
                {"name": "claim_form:RenderingPhysician", "confidence": 0.94},
            ],
            "medium_confidence_fields": [
                {"name": "claim_form:ProviderName", "confidence": 0.93},
                {"name": "claim_form:ProviderNPI", "confidence": 0.92},
            ],
            "low_confidence_fields": [],
        },
    }


def _priya_patel_auto() -> Dict[str, Any]:
    """Priya Patel — major collision, high fraud risk, SIU investigation active."""
    return {
        "id": "app-pp-auto-001",
        "created_at": "2024-12-03T11:48:00Z",
        "external_reference": "CUST-PP-003",
        "status": "under_investigation",
        "persona": "automotive_claims",
        "files": [
            {"filename": "claim_form.pdf", "path": "applications/app-pp-auto-001/claim_form.pdf", "content_type": "application/pdf", "media_type": "document"},
            {"filename": "damage_photo_front.jpg", "path": "applications/app-pp-auto-001/damage_photo_front.jpg", "content_type": "image/jpeg", "media_type": "image"},
            {"filename": "damage_photo_side.jpg", "path": "applications/app-pp-auto-001/damage_photo_side.jpg", "content_type": "image/jpeg", "media_type": "image"},
            {"filename": "repair_estimate.pdf", "path": "applications/app-pp-auto-001/repair_estimate.pdf", "content_type": "application/pdf", "media_type": "document"},
            {"filename": "tow_receipt.pdf", "path": "applications/app-pp-auto-001/tow_receipt.pdf", "content_type": "application/pdf", "media_type": "document"},
        ],
        "llm_outputs": {
            "damage_assessment": {
                "visual_damage_analysis": {
                    "section": "damage_assessment",
                    "subsection": "visual_damage_analysis",
                    "raw": (
                        "Insured vehicle is a 2023 BMW X5 xDrive40i photographed at Premium Collision "
                        "Centre. Significant front-end damage observed: bumper cover destroyed, grille "
                        "shattered, hood buckled with deep V-shaped deformation. Radiator support pushed "
                        "back approximately 6 inches. Both headlamp assemblies cracked. Front fenders "
                        "show stress wrinkling. Of note: pre-existing scuffs and oxidation visible on "
                        "the left front fender and driver door — inconsistent with a 2023 model year "
                        "vehicle in claimed condition. Right-side A-pillar appears undamaged, which is "
                        "unusual given the stated swerve-to-avoid scenario."
                    ),
                    "parsed": {
                        "summary": "Major front-end impact damage to 2023 BMW X5. Damage pattern raises concerns — direct frontal impact inconsistent with claimed evasive swerve maneuver. Pre-existing wear noted on adjacent panels.",
                        "damage_areas": [
                            {"area": "Front bumper cover", "severity": "severe", "description": "Completely destroyed; fragmented plastic and detached from mounting points"},
                            {"area": "Hood", "severity": "severe", "description": "Deep V-shaped buckle indicating direct frontal impact; paint separation at crease lines"},
                            {"area": "Grille and radiator support", "severity": "severe", "description": "Grille shattered; radiator support displaced approximately 6 inches rearward"},
                            {"area": "Headlamp assemblies", "severity": "moderate", "description": "Both units cracked; left assembly partially dislodged from housing"},
                            {"area": "Front fenders", "severity": "moderate", "description": "Stress wrinkling on both sides; pre-existing scuffs and oxidation on left fender inconsistent with vehicle age"},
                            {"area": "Driver door", "severity": "minor", "description": "Pre-existing scuffs and paint oxidation noted — not consistent with 2023 model year"},
                        ],
                        "total_damage_estimate_CAD": 18500.00,
                        "airbag_deployment": False,
                        "vehicle_drivable": False,
                        "recommended_action": "Hold for SIU review — damage pattern inconsistencies require investigation",
                    },
                },
                "estimate_validation": {
                    "section": "damage_assessment",
                    "subsection": "estimate_validation",
                    "raw": (
                        "Repair estimate from Premium Collision Centre totals $18,500 CAD. OEM parts "
                        "pricing for 2023 BMW X5 components is at the high end of market range but "
                        "within BMW dealer pricing. Labour at 42 hours is on the upper bound for the "
                        "documented damage scope. Several line items require clarification: estimate "
                        "includes blending on rear quarter panels which are not adjacent to the impact "
                        "zone. Paint and materials at $2,800 exceeds typical range for front-only refinish."
                    ),
                    "parsed": {
                        "summary": "Estimate is at the high end of market range with several questionable line items requiring clarification.",
                        "estimate_id": "EST-PP-2024-1187",
                        "parts_breakdown_CAD": 10200.00,
                        "labor_hours": 42.0,
                        "labor_rate_per_hour": 110.00,
                        "labor_cost_CAD": 4620.00,
                        "sublet_items": [
                            {"description": "Wheel alignment", "cost_CAD": 180.00},
                            {"description": "AC recharge", "cost_CAD": 150.00},
                        ],
                        "paint_materials_CAD": 2800.00,
                        "estimate_accuracy": "Questionable — several line items need clarification",
                        "comparison_market": "High end of market range",
                        "recommended_action": "Hold pending SIU review and independent appraisal",
                    },
                },
            },
            "liability_assessment": {
                "fault_determination": {
                    "section": "liability_assessment",
                    "subsection": "fault_determination",
                    "raw": (
                        "Claimant reports swerving to avoid a deer on Highway 401 near Milton at "
                        "approximately 10:45 PM on November 30, 2024, resulting in the vehicle "
                        "striking a concrete median barrier. No police report was filed. Claimant "
                        "states she did not call police because the vehicle was towed by a passing "
                        "motorist to a nearby lot. No witnesses identified. No dashcam footage "
                        "available. The damage pattern shows direct frontal impact which is more "
                        "consistent with a head-on collision than a swerving maneuver into a median."
                    ),
                    "parsed": {
                        "summary": "Single-vehicle incident on Highway 401; claimant alleges swerve to avoid deer. No police report, no witnesses. Damage pattern inconsistent with stated events.",
                        "point_of_impact": "Direct frontal — center of vehicle",
                        "contributing_factors": ["Alleged deer avoidance maneuver", "Nighttime driving", "No corroborating evidence"],
                        "fault_determination": "100% — single vehicle, insured at fault (if claim is valid)",
                        "police_report_status": "Not filed — claimant cites informal tow arrangement",
                        "witness_statements": "None available",
                        "liability_risk": "Undetermined pending investigation",
                    },
                },
            },
            "fraud_detection": {
                "red_flag_analysis": {
                    "section": "fraud_detection",
                    "subsection": "red_flag_analysis",
                    "raw": (
                        "Two significant fraud red flags identified. First, the damage pattern is "
                        "inconsistent with the claimed loss scenario: the claimant describes swerving "
                        "to avoid a deer and striking a median barrier, but the damage shows a direct, "
                        "centered frontal impact with a V-shaped hood deformation pattern — this is "
                        "more consistent with striking a stationary object head-on at moderate speed, "
                        "not a glancing or angled impact from a swerve. Airbags did not deploy despite "
                        "significant frontal damage, which is unusual. Second, there was a 72-hour "
                        "delay in reporting the loss. The incident allegedly occurred on November 30, "
                        "2024, but the claim was not reported until December 3, 2024. No police report "
                        "was filed despite significant damage and a non-drivable vehicle on a major "
                        "highway. Additionally, the vehicle photos show pre-existing wear and oxidation "
                        "on adjacent panels inconsistent with a 2023 model year vehicle."
                    ),
                    "parsed": {
                        "summary": "Two fraud red flags identified: (1) damage pattern inconsistent with claimed swerve maneuver, (2) 72-hour reporting delay with no police report.",
                        "red_flags": [
                            {
                                "flag": "Inconsistent damage pattern",
                                "severity": "High",
                                "description": (
                                    "Direct centered frontal impact with V-shaped hood deformation is inconsistent "
                                    "with claimed swerve-into-median scenario. Airbags did not deploy despite "
                                    "significant frontal crush. Pre-existing wear on adjacent panels raises "
                                    "concerns about vehicle condition prior to loss."
                                ),
                            },
                            {
                                "flag": "Delayed reporting and missing documentation",
                                "severity": "High",
                                "description": (
                                    "72-hour delay between alleged loss date (Nov 30) and claim report (Dec 3). "
                                    "No police report filed despite non-drivable vehicle on Highway 401. "
                                    "No witnesses identified. Informal tow arrangement not verifiable."
                                ),
                            },
                        ],
                        "fraud_risk": "High",
                        "fraud_score": 0.78,
                        "recommended_action": "Refer to SIU for full investigation before any payment",
                    },
                },
            },
            "payout_recommendation": {
                "settlement_analysis": {
                    "section": "payout_recommendation",
                    "subsection": "settlement_analysis",
                    "raw": (
                        "Payment is on hold pending completion of the Special Investigations Unit "
                        "(SIU) review. The combination of inconsistent damage pattern, delayed "
                        "reporting, absent police report, and pre-existing panel wear warrants a "
                        "thorough investigation before any settlement is authorized. An independent "
                        "appraisal has been ordered. SIU investigator assigned: K. Thornton, case "
                        "reference SIU-2024-PP-0891. Estimated investigation timeline: 30-45 days."
                    ),
                    "parsed": {
                        "summary": "Under investigation — hold payment pending SIU review and independent appraisal.",
                        "recommended_payout_CAD": 0.00,
                        "deductible_CAD": 1000.00,
                        "insured_responsibility_CAD": 1000.00,
                        "subrogation_target": None,
                        "final_approval": False,
                        "rationale": (
                            "Payment withheld pending SIU investigation. Two high-severity fraud red flags "
                            "require resolution: inconsistent damage pattern and 72-hour reporting delay "
                            "with no police report. Independent appraisal ordered. SIU case SIU-2024-PP-0891 "
                            "assigned to investigator K. Thornton."
                        ),
                    },
                },
            },
        },
        "extracted_fields": {
            "claim_form:ClaimNumber": {"field_name": "ClaimNumber", "value": "CLM-PP-241203-01", "confidence": 0.94, "source_file": "claim_form.pdf"},
            "claim_form:PolicyNumber": {"field_name": "PolicyNumber", "value": "AUTO-ON-9918273", "confidence": 0.96, "source_file": "claim_form.pdf"},
            "claim_form:InsuredName": {"field_name": "InsuredName", "value": "Priya Patel", "confidence": 0.97, "source_file": "claim_form.pdf"},
            "claim_form:DateOfLoss": {"field_name": "DateOfLoss", "value": "2024-11-30", "confidence": 0.93, "source_file": "claim_form.pdf"},
            "claim_form:DateReported": {"field_name": "DateReported", "value": "2024-12-03", "confidence": 0.95, "source_file": "claim_form.pdf"},
            "claim_form:VehicleYear": {"field_name": "VehicleYear", "value": "2023", "confidence": 0.96, "source_file": "claim_form.pdf"},
            "claim_form:VehicleMake": {"field_name": "VehicleMake", "value": "BMW", "confidence": 0.97, "source_file": "claim_form.pdf"},
            "claim_form:VehicleModel": {"field_name": "VehicleModel", "value": "X5 xDrive40i", "confidence": 0.95, "source_file": "claim_form.pdf"},
            "claim_form:VehicleVIN": {"field_name": "VehicleVIN", "value": "5UXCR6C05P9K78432", "confidence": 0.88, "source_file": "claim_form.pdf"},
            "claim_form:DamageDescription": {"field_name": "DamageDescription", "value": "Major front-end collision damage — hood, bumper, grille, radiator support", "confidence": 0.91, "source_file": "claim_form.pdf"},
            "claim_form:RepairEstimate": {"field_name": "RepairEstimate", "value": "18500.00", "confidence": 0.94, "source_file": "repair_estimate.pdf"},
            "claim_form:LossLocation": {"field_name": "LossLocation", "value": "Highway 401 near Milton, ON", "confidence": 0.89, "source_file": "claim_form.pdf"},
            "claim_form:PoliceReportFiled": {"field_name": "PoliceReportFiled", "value": "No", "confidence": 0.92, "source_file": "claim_form.pdf"},
            "tow_receipt:TowCompany": {"field_name": "TowCompany", "value": "Not documented — informal arrangement", "confidence": 0.65, "source_file": "tow_receipt.pdf"},
        },
        "confidence_summary": {
            "total_fields": 14,
            "average_confidence": 0.92,
            "high_confidence_count": 9,
            "medium_confidence_count": 4,
            "low_confidence_count": 1,
            "high_confidence_fields": [
                {"name": "claim_form:InsuredName", "confidence": 0.97},
                {"name": "claim_form:VehicleMake", "confidence": 0.97},
                {"name": "claim_form:PolicyNumber", "confidence": 0.96},
                {"name": "claim_form:VehicleYear", "confidence": 0.96},
                {"name": "claim_form:DateReported", "confidence": 0.95},
                {"name": "claim_form:VehicleModel", "confidence": 0.95},
                {"name": "claim_form:ClaimNumber", "confidence": 0.94},
                {"name": "claim_form:RepairEstimate", "confidence": 0.94},
                {"name": "claim_form:DateOfLoss", "confidence": 0.93},
            ],
            "medium_confidence_fields": [
                {"name": "claim_form:PoliceReportFiled", "confidence": 0.92},
                {"name": "claim_form:DamageDescription", "confidence": 0.91},
                {"name": "claim_form:LossLocation", "confidence": 0.89},
                {"name": "claim_form:VehicleVIN", "confidence": 0.88},
            ],
            "low_confidence_fields": [
                {"name": "tow_receipt:TowCompany", "confidence": 0.65},
            ],
        },
    }


def get_claims_apps() -> List[Dict[str, Any]]:
    """Return seed data for 3 claims applications (1 health + 2 automotive)."""
    return [
        _sarah_chen_auto(),
        _marcus_williams_health(),
        _priya_patel_auto(),
    ]
