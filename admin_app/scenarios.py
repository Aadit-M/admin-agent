"""Curated prompts for demonstrating common admin workflows."""


DEMO_SCENARIOS = {
    "1️⃣ Implicit Context Test ('All Employees' + Unstated Duration/Date)": (
        "Schedule a company-wide townhall with all employees today titled 'Q4 Global Strategy & AI Roadmap'. "
        "We haven't written formal bullet points yet, so draft the single-paragraph agenda based on everyone's "
        "roles in Engineering and HR."
    ),
    "2️⃣ Visa & Travel Approval + Expense & Invoice Triage": (
        "1. Priya needs to travel to the United Kingdom (London office) departing 2026-11-02 for the Global People Ops Summit. "
        "Estimated flight and hotel cost is $1,850. Check her visa requirements and submit the approval packet.\n"
        "2. Also audit and log two finance items: (a) Bob's team dinner receipt in London for $145, and "
        "(b) a software cloud invoice from 'CloudScale AWS' for $3,200 referencing PO-2026-101."
    ),
    "3️⃣ Onboarding + Dynamic 'All Employees' Orientation": (
        "Onboard our new Senior AI Engineer, Liam O'Connor (liam.oconnor@gmail.com), based in London (Europe/London, UK citizen) "
        "starting today. Provision GitHub Enterprise, Slack, and AWS IAM licenses, plus a 'MacBook Pro M4 + YubiKey'. "
        "Once he is onboarded, schedule a 'Welcome & Architecture Sync' meeting with all employees today so the entire company can welcome him."
    ),
    "4️⃣ Full 4-Agent Enterprise Stress Test (Onboarding + Visa + Expense + Scheduling)": (
        "Execute the following Monday admin queue:\n"
        "1. Onboard Liam O'Connor (liam.oconnor@gmail.com) as Staff ML Engineer in London (Europe/London, UK citizen) with GitHub & Slack licenses and a 'MacBook Pro M4'.\n"
        "2. Process a travel & visa request for Priya to visit the New York (USA) headquarters on 2026-11-10 for Q1 Executive Planning (estimated cost $2,950).\n"
        "3. Triage an unannounced vendor invoice from 'ShadowAI Corp' for $1,400 with no PO number attached.\n"
        "4. Schedule a sync today for all employees titled 'Weekly Global Operations Standup' summarizing these updates in the single-paragraph email agenda."
    ),
}
