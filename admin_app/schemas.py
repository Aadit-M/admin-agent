"""Function-calling schemas grouped by domain agent."""


SCHEDULING_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_participant_profiles",
            "description": "Looks up employee profiles. Supports specific names OR group aliases like ['all'], ['all employees'], ['engineering'].",
            "parameters": {
                "type": "object",
                "properties": {"names": {"type": "array", "items": {"type": "string"}}},
                "required": ["names"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_optimal_meeting_slots",
            "description": "Finds conflict-free time slots across all participants' time zones. Supports ['all'] or specific names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "participant_names": {"type": "array", "items": {"type": "string"}},
                    "date_str": {"type": "string", "description": "YYYY-MM-DD (default 2026-10-26)"},
                    "duration_minutes": {"type": "integer", "description": "Default 30"},
                },
                "required": ["participant_names", "date_str", "duration_minutes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_calendar_meeting",
            "description": "Books the meeting on the calendar and returns event details and video link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_time_utc": {"type": "string"},
                    "duration_minutes": {"type": "integer"},
                    "attendee_emails": {"type": "array", "items": {"type": "string"}},
                    "agenda_summary_paragraph": {"type": "string"},
                },
                "required": ["title", "start_time_utc", "duration_minutes", "attendee_emails", "agenda_summary_paragraph"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_calendar_email_invite",
            "description": "Dispatches the email invite with local time breakdown and single-paragraph agenda.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attendee_emails": {"type": "array", "items": {"type": "string"}},
                    "subject": {"type": "string"},
                    "start_time_utc": {"type": "string"},
                    "local_time_breakdown": {"type": "string"},
                    "meeting_link": {"type": "string"},
                    "single_paragraph_agenda": {"type": "string"},
                },
                "required": ["attendee_emails", "subject", "start_time_utc", "local_time_breakdown", "meeting_link", "single_paragraph_agenda"],
            },
        },
    },
]

ONBOARDING_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "send_offer_letter",
            "description": "Dispatches an offer letter and adds the new hire to the company directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "candidate_name": {"type": "string"},
                    "candidate_email": {"type": "string"},
                    "role_title": {"type": "string"},
                    "department": {"type": "string"},
                    "start_date": {"type": "string"},
                    "timezone": {"type": "string"},
                    "citizenship": {"type": "string"},
                    "manager_name": {"type": "string"},
                },
                "required": ["candidate_name", "candidate_email", "role_title", "department", "start_date", "timezone", "citizenship", "manager_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "provision_software_licenses",
            "description": "Provisions SaaS licenses for the new employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string"},
                    "corporate_email": {"type": "string"},
                    "role_title": {"type": "string"},
                    "requested_tools": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["employee_name", "corporate_email", "role_title", "requested_tools"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_it_support_keys",
            "description": "Generates temporary SSO keys, VPN tokens, and hardware tickets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string"},
                    "corporate_email": {"type": "string"},
                    "hardware_profile": {"type": "string"},
                },
                "required": ["employee_name", "corporate_email", "hardware_profile"],
            },
        },
    },
]

TRAVEL_VISA_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "evaluate_visa_and_travel_policy",
            "description": "Evaluates visa requirements based on employee citizenship and checks travel budget policy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string"},
                    "destination_country": {"type": "string"},
                    "trip_purpose": {"type": "string"},
                    "departure_date": {"type": "string"},
                    "estimated_cost_usd": {"type": "number"},
                },
                "required": ["employee_name", "destination_country", "trip_purpose", "departure_date", "estimated_cost_usd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_travel_and_visa_approval",
            "description": "Generates the visa documentation packet and routes travel request to the approver.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string"},
                    "destination_country": {"type": "string"},
                    "visa_type_required": {"type": "string"},
                    "required_documents": {"type": "array", "items": {"type": "string"}},
                    "estimated_cost_usd": {"type": "number"},
                    "policy_verdict": {"type": "string"},
                    "approver_name": {"type": "string"},
                    "justification_summary": {"type": "string"},
                },
                "required": [
                    "employee_name",
                    "destination_country",
                    "visa_type_required",
                    "required_documents",
                    "estimated_cost_usd",
                    "policy_verdict",
                    "approver_name",
                    "justification_summary",
                ],
            },
        },
    },
]

EXPENSE_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "audit_expense_or_invoice",
            "description": "Audits an expense receipt or vendor invoice against policy caps and active Purchase Orders (POs).",
            "parameters": {
                "type": "object",
                "properties": {
                    "submitter_or_vendor": {"type": "string"},
                    "category": {"type": "string"},
                    "amount_usd": {"type": "number"},
                    "description": {"type": "string"},
                    "po_number": {"type": "string", "description": "Optional PO number like PO-2026-101, or empty string if none"},
                },
                "required": ["submitter_or_vendor", "category", "amount_usd", "description", "po_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_reconciliation_decision",
            "description": "Logs the official expense/invoice triage decision into the finance ledger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "submitter_or_vendor": {"type": "string"},
                    "category": {"type": "string"},
                    "amount_usd": {"type": "number"},
                    "audit_verdict": {"type": "string"},
                    "anomaly_flags": {"type": "array", "items": {"type": "string"}},
                    "po_number": {"type": "string"},
                    "reconciliation_notes": {"type": "string"},
                },
                "required": ["submitter_or_vendor", "category", "amount_usd", "audit_verdict", "anomaly_flags", "po_number", "reconciliation_notes"],
            },
        },
    },
]
