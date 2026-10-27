"""Deterministic enterprise actions exposed to the agents."""

import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .state import CURRENT_DEMO_DATE, get_current_state


def resolve_participant_list(names_or_groups: list[str]) -> list[str]:
    """
    Resolves implicit aliases ('all', 'all employees', 'everyone', 'engineering')
    as well as partial or full employee names into valid directory keys.
    """
    if not names_or_groups:
        return list(get_current_state().directory.keys())

    resolved_keys = []
    for raw in names_or_groups:
        token = raw.strip().lower()
        if token in {"all", "all employees", "everyone", "entire company", "company", "team", "staff", "*"}:
            return list(get_current_state().directory.keys())

        # Check department match (e.g. "engineering")
        dept_matches = [
            k for k, emp in get_current_state().directory.items()
            if token in emp.get("department", "").lower()
        ]
        if dept_matches:
            for dm in dept_matches:
                if dm not in resolved_keys:
                    resolved_keys.append(dm)
            continue

        # Check first name or full name match
        first_token = token.split()[0]
        if first_token in get_current_state().directory and first_token not in resolved_keys:
            resolved_keys.append(first_token)
        else:
            for k, emp in get_current_state().directory.items():
                if token in emp["name"].lower() and k not in resolved_keys:
                    resolved_keys.append(k)

    return resolved_keys if resolved_keys else list(get_current_state().directory.keys())

def get_participant_profiles(names: list[str]) -> dict:
    keys = resolve_participant_list(names)
    results = {}
    for k in keys:
        p = get_current_state().directory[k]
        results[k] = {
            "name": p["name"],
            "role": p["role"],
            "department": p["department"],
            "email": p["email"],
            "timezone": p["timezone"],
            "work_hours_local": f"{p['work_hours'][0]}:00 - {p['work_hours'][1]}:00",
            "busy_blocks_utc": p["busy_utc"],
        }
    return {"resolved_count": len(results), "profiles": results}

def find_optimal_meeting_slots(
    participant_names: list[str], date_str: str = CURRENT_DEMO_DATE, duration_minutes: int = 30
) -> dict:
    keys = resolve_participant_list(participant_names)
    if not date_str or date_str.lower() in {"today", "now"}:
        date_str = CURRENT_DEMO_DATE
    elif date_str.lower() == "tomorrow":
        date_str = "2026-10-27"

    duration_minutes = int(duration_minutes or 30)
    utc_tz = ZoneInfo("UTC")
    base_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=utc_tz)

    available_slots = []
    step = timedelta(minutes=30)
    duration = timedelta(minutes=duration_minutes)

    for i in range(48):
        slot_start_utc = base_date + (i * step)
        slot_end_utc = slot_start_utc + duration
        slot_valid = True
        local_times_display = {}

        for k in keys:
            emp = get_current_state().directory[k]
            emp_tz = ZoneInfo(emp["timezone"])
            local_start = slot_start_utc.astimezone(emp_tz)
            local_end = slot_end_utc.astimezone(emp_tz)

            w_start, w_end = emp["work_hours"]
            if (
                local_start.hour < w_start
                or (local_end.hour > w_end)
                or (local_end.hour == w_end and local_end.minute > 0)
            ):
                slot_valid = False
                break

            for b_start_str, b_end_str in emp["busy_utc"]:
                b_start = datetime.fromisoformat(b_start_str.replace("Z", "+00:00"))
                b_end = datetime.fromisoformat(b_end_str.replace("Z", "+00:00"))
                if slot_start_utc < b_end and b_start < slot_end_utc:
                    slot_valid = False
                    break

            if not slot_valid:
                break

            local_times_display[emp["name"]] = (
                f"{local_start.strftime('%I:%M %p')} - {local_end.strftime('%I:%M %p')} ({emp['timezone']})"
            )

        if slot_valid:
            available_slots.append(
                {
                    "start_time_utc": slot_start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end_time_utc": slot_end_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "local_times": local_times_display,
                }
            )

    return {
        "date": date_str,
        "resolved_participants": [get_current_state().directory[k]["name"] for k in keys],
        "matching_slots": available_slots[:3],
    }

def book_calendar_meeting(
    title: str,
    start_time_utc: str,
    duration_minutes: int,
    attendee_emails: list[str],
    agenda_summary_paragraph: str,
) -> dict:
    # Expand if LLM passed "all" in attendee_emails
    if any(e.lower() in {"all", "all employees", "everyone"} for e in attendee_emails):
        attendee_emails = [emp["email"] for emp in get_current_state().directory.values()]

    slug = "".join(c if c.isalnum() else "-" for c in title.lower()).strip("-")[:25]
    event = {
        "event_id": f"EVT-{len(get_current_state().calendar_events) + 1001}",
        "title": title,
        "start_time_utc": start_time_utc,
        "duration_minutes": int(duration_minutes),
        "attendees": attendee_emails,
        "meeting_link": f"https://meet.company.com/{slug}",
        "agenda": agenda_summary_paragraph,
        "status": "CONFIRMED",
    }
    get_current_state().calendar_events.append(event)

    start_dt = datetime.fromisoformat(start_time_utc.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(minutes=int(duration_minutes))
    end_time_utc = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    for emp in get_current_state().directory.values():
        if emp["email"] in attendee_emails:
            emp["busy_utc"].append((start_time_utc, end_time_utc))

    return event

def send_calendar_email_invite(
    attendee_emails: list[str],
    subject: str,
    start_time_utc: str,
    local_time_breakdown: str,
    meeting_link: str,
    single_paragraph_agenda: str,
) -> dict:
    if any(e.lower() in {"all", "all employees", "everyone"} for e in attendee_emails):
        attendee_emails = [emp["email"] for emp in get_current_state().directory.values()]

    email_payload = {
        "email_id": f"MSG-{uuid.uuid4().hex[:6].upper()}",
        "to": attendee_emails,
        "subject": f"Calendar Invite: {subject}",
        "start_time_utc": start_time_utc,
        "local_time_breakdown": local_time_breakdown,
        "meeting_link": meeting_link,
        "single_paragraph_agenda": single_paragraph_agenda,
    }
    get_current_state().sent_emails.append(email_payload)
    return {"status": "SENT", "email_id": email_payload["email_id"], "recipients": attendee_emails}

def send_offer_letter(
    candidate_name: str,
    candidate_email: str,
    role_title: str,
    department: str = "Engineering",
    start_date: str = CURRENT_DEMO_DATE,
    timezone: str = "Europe/London",
    citizenship: str = "UK",
    manager_name: str = "Alice Carter",
) -> dict:
    first_key = candidate_name.strip().lower().split()[0]
    corporate_email = f"{first_key}@company.com"

    get_current_state().directory[first_key] = {
        "name": candidate_name,
        "role": role_title,
        "department": department,
        "email": corporate_email,
        "timezone": timezone,
        "citizenship": citizenship,
        "manager": manager_name,
        "work_hours": (9, 18),
        "busy_utc": [],
    }

    offer_record = {
        "offer_id": f"OFR-{uuid.uuid4().hex[:6].upper()}",
        "candidate_name": candidate_name,
        "personal_email": candidate_email,
        "corporate_email": corporate_email,
        "role_title": role_title,
        "department": department,
        "start_date": start_date,
        "timezone": timezone,
        "citizenship": citizenship,
        "manager": manager_name,
        "status": "OFFER_SENT & DIRECTORY_PROVISIONED",
    }
    get_current_state().onboarding_ledger[first_key] = {
        "offer": offer_record,
        "licenses": {},
        "it_keys": {},
    }
    return offer_record

def provision_software_licenses(
    employee_name: str, corporate_email: str, role_title: str, requested_tools: list[str]
) -> dict:
    licenses = {}
    for tool in requested_tools:
        licenses[tool] = {
            "seat_id": f"LIC-{tool.upper().replace(' ', '')[:5]}-{uuid.uuid4().hex[:5].upper()}",
            "assigned_to": corporate_email,
            "status": "ACTIVE",
        }

    first_key = employee_name.strip().lower().split()[0]
    if first_key not in get_current_state().onboarding_ledger:
        get_current_state().onboarding_ledger[first_key] = {"offer": {}, "licenses": {}, "it_keys": {}}
    get_current_state().onboarding_ledger[first_key]["licenses"] = licenses
    return {"employee": employee_name, "corporate_email": corporate_email, "licenses": licenses}

def generate_it_support_keys(
    employee_name: str, corporate_email: str, hardware_profile: str
) -> dict:
    it_bundle = {
        "it_ticket_id": f"IT-REQ-{uuid.uuid4().hex[:5].upper()}",
        "hardware_assigned": hardware_profile,
        "temp_sso_key": f"SSO-TMP-{uuid.uuid4().hex[:8].upper()}",
        "vpn_bootstrap_token": f"VPN-KEY-{uuid.uuid4().hex[:10].upper()}",
        "yubikey_serial": f"YK-{uuid.uuid4().int % 100000000:08d}",
    }
    first_key = employee_name.strip().lower().split()[0]
    if first_key not in get_current_state().onboarding_ledger:
        get_current_state().onboarding_ledger[first_key] = {"offer": {}, "licenses": {}, "it_keys": {}}
    get_current_state().onboarding_ledger[first_key]["it_keys"] = it_bundle
    return it_bundle

def evaluate_visa_and_travel_policy(
    employee_name: str,
    destination_country: str,
    trip_purpose: str,
    departure_date: str,
    estimated_cost_usd: float,
) -> dict:
    keys = resolve_participant_list([employee_name])
    emp_key = keys[0] if keys else "priya"
    emp = get_current_state().directory.get(emp_key, get_current_state().directory["priya"])

    citizenship = emp.get("citizenship", "India")
    dest = destination_country.strip().upper()
    cost = float(estimated_cost_usd)
    cap = get_current_state().corporate_policies["flight_hotel_cap_usd"]

    # Deterministic Visa Matrix
    if citizenship.upper() == dest or (citizenship == "UK" and dest in {"UNITED KINGDOM", "LONDON", "UK"}):
        visa_type = "Domestic / No Visa Required"
        docs_needed = ["Corporate ID Badge"]
    elif citizenship == "India" and dest in {"UK", "UNITED KINGDOM", "LONDON"}:
        visa_type = "UK Standard Visitor (Business) Visa"
        docs_needed = ["Valid Passport (6m+)", "UK Sponsor Invitation Letter", "Corporate Bank Guarantee"]
    elif citizenship == "India" and dest in {"USA", "US", "UNITED STATES", "NEW YORK"}:
        visa_type = "US B-1 Business Visitor Visa"
        docs_needed = ["DS-160 Confirmation", "US Office Invitation Letter", "Travel Itinerary"]
    elif citizenship == "UK" and dest in {"USA", "US", "UNITED STATES", "NEW YORK"}:
        visa_type = "US ESTA (Visa Waiver Program)"
        docs_needed = ["Electronic Passport", "ESTA Registration Receipt"]
    else:
        visa_type = f"Standard Business Entry Visa ({citizenship} -> {destination_country})"
        docs_needed = ["Valid Passport", "Host Office Invitation Letter"]

    within_budget = cost <= cap
    policy_verdict = "COMPLIANT" if within_budget else "OVER_CAP_REQUIRES_VP_OVERRIDE"

    return {
        "employee": emp["name"],
        "citizenship_inferred": citizenship,
        "manager_inferred": emp["manager"],
        "destination_country": destination_country,
        "departure_date": departure_date,
        "visa_type_required": visa_type,
        "required_documents": docs_needed,
        "estimated_cost_usd": cost,
        "policy_budget_cap_usd": cap,
        "policy_verdict": policy_verdict,
    }

def submit_travel_and_visa_approval(
    employee_name: str,
    destination_country: str,
    visa_type_required: str,
    required_documents: list[str],
    estimated_cost_usd: float,
    policy_verdict: str,
    approver_name: str,
    justification_summary: str,
) -> dict:
    status = "APPROVED_AND_VISA_PACKET_ISSUED" if policy_verdict == "COMPLIANT" else "PENDING_VP_BUDGET_SIGNOFF"
    packet = {
        "request_id": f"TRV-{len(get_current_state().travel_visa_requests) + 501}",
        "employee_name": employee_name,
        "destination": destination_country,
        "visa_type": visa_type_required,
        "required_documents": required_documents,
        "estimated_cost_usd": float(estimated_cost_usd),
        "policy_verdict": policy_verdict,
        "routed_to_approver": approver_name,
        "status": status,
        "justification_summary": justification_summary,
    }
    get_current_state().travel_visa_requests.append(packet)
    return packet

def audit_expense_or_invoice(
    submitter_or_vendor: str,
    category: str,
    amount_usd: float,
    description: str,
    po_number: str = "",
) -> dict:
    amount = float(amount_usd)
    pol = get_current_state().corporate_policies
    cat_lower = category.lower()
    anomalies = []
    po_matched = False

    if "meal" in cat_lower or "dinner" in cat_lower or "food" in cat_lower:
        if amount > pol["meal_expense_cap_usd"]:
            anomalies.append(f"Exceeds ${pol['meal_expense_cap_usd']} meal policy cap.")
    elif "flight" in cat_lower or "travel" in cat_lower or "hotel" in cat_lower:
        if amount > pol["flight_hotel_cap_usd"]:
            anomalies.append(f"Exceeds ${pol['flight_hotel_cap_usd']} travel policy cap.")

    if po_number and po_number in get_current_state().purchase_orders:
        po_data = get_current_state().purchase_orders[po_number]
        po_matched = True
        if amount > po_data["budget_usd"]:
            anomalies.append(f"Invoice amount (${amount}) exceeds {po_number} ceiling (${po_data['budget_usd']}).")
    elif amount > pol["po_required_threshold_usd"] and ("vendor" in cat_lower or "software" in cat_lower or "invoice" in cat_lower or "hardware" in cat_lower):
        anomalies.append(f"Missing valid Purchase Order for vendor/software spend over ${pol['po_required_threshold_usd']}.")

    verdict = "AUTO_APPROVED" if not anomalies else "FLAGGED_FOR_FINANCE_REVIEW"
    return {
        "submitter_or_vendor": submitter_or_vendor,
        "category": category,
        "amount_usd": amount,
        "po_number": po_number or "NONE",
        "po_matched": po_matched,
        "anomalies_detected": anomalies,
        "recommended_verdict": verdict,
    }

def log_reconciliation_decision(
    submitter_or_vendor: str,
    category: str,
    amount_usd: float,
    audit_verdict: str,
    anomaly_flags: list[str],
    po_number: str,
    reconciliation_notes: str,
) -> dict:
    record = {
        "expense_id": f"EXP-{len(get_current_state().expense_reports) + 801}",
        "submitter_or_vendor": submitter_or_vendor,
        "category": category,
        "amount_usd": float(amount_usd),
        "po_number": po_number or "N/A",
        "status": audit_verdict,
        "anomaly_flags": anomaly_flags,
        "reconciliation_notes": reconciliation_notes,
    }
    get_current_state().expense_reports.append(record)
    return record

TOOL_FUNCTIONS = {
    "get_participant_profiles": get_participant_profiles,
    "find_optimal_meeting_slots": find_optimal_meeting_slots,
    "book_calendar_meeting": book_calendar_meeting,
    "send_calendar_email_invite": send_calendar_email_invite,
    "send_offer_letter": send_offer_letter,
    "provision_software_licenses": provision_software_licenses,
    "generate_it_support_keys": generate_it_support_keys,
    "evaluate_visa_and_travel_policy": evaluate_visa_and_travel_policy,
    "submit_travel_and_visa_approval": submit_travel_and_visa_approval,
    "audit_expense_or_invoice": audit_expense_or_invoice,
    "log_reconciliation_decision": log_reconciliation_decision,
}
