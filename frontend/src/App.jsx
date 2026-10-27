import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  Building2,
  CalendarDays,
  Check,
  ChevronDown,
  CircleHelp,
  Clock3,
  Command,
  CreditCard,
  FileText,
  KeyRound,
  LayoutDashboard,
  LoaderCircle,
  Mail,
  Menu,
  Plane,
  Plus,
  RotateCcw,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Users,
  WandSparkles,
  Workflow,
  X,
} from "lucide-react";

const navigation = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "emails", label: "Email center", icon: Mail, countKey: "sent_emails" },
  { id: "calendar", label: "Calendar", icon: CalendarDays, countKey: "calendar_events" },
  { id: "travel", label: "Travel & visa", icon: Plane, countKey: "travel_visa_requests" },
  { id: "expenses", label: "Expenses", icon: CreditCard, countKey: "expense_reports" },
  { id: "onboarding", label: "Onboarding", icon: Users, countKey: "onboarding_ledger" },
  { id: "directory", label: "People & policy", icon: Building2, countKey: "directory" },
  { id: "architecture", label: "Agent activity", icon: Workflow },
];

const initialState = {
  directory: {},
  purchase_orders: {},
  corporate_policies: {},
  calendar_events: [],
  sent_emails: [],
  onboarding_ledger: {},
  travel_visa_requests: [],
  expense_reports: [],
  routing_trace: [],
  tool_logs: [],
  last_graph_state: {},
  final_summary: null,
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "The request could not be completed.");
  return payload;
}

function App() {
  const [sessionId, setSessionId] = useState("");
  const [workspace, setWorkspace] = useState(initialState);
  const [scenarios, setScenarios] = useState([]);
  const [activePage, setActivePage] = useState("overview");
  const [selectedScenario, setSelectedScenario] = useState("");
  const [prompt, setPrompt] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("openai/gpt-oss-120b");
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const refreshWorkspace = useCallback(async (id) => {
    const data = await api(`/api/session/${id}/state`);
    setWorkspace(data);
  }, []);

  useEffect(() => {
    let active = true;
    async function initialize() {
      try {
        const [scenarioData, health] = await Promise.all([api("/api/scenarios"), api("/api/health")]);
        if (!health.status) throw new Error("The API is unavailable.");
        const storedId = localStorage.getItem("adminhelp-session-id");
        let id = storedId;
        if (id) {
          try {
            await api(`/api/session/${id}/state`);
          } catch {
            id = "";
          }
        }
        if (!id) {
          const created = await api("/api/session", { method: "POST" });
          id = created.session_id;
          localStorage.setItem("adminhelp-session-id", id);
        }
        const state = await api(`/api/session/${id}/state`);
        if (active) {
          setScenarios(scenarioData);
          setSessionId(id);
          setWorkspace(state);
          setSelectedScenario(scenarioData[0]?.name || "");
          setPrompt(scenarioData[0]?.prompt || "");
        }
      } catch (requestError) {
        if (active) setError(requestError.message);
      } finally {
        if (active) setLoading(false);
      }
    }
    initialize();
    return () => {
      active = false;
    };
  }, []);

  const employeeCount = Object.keys(workspace.directory || {}).length;
  const agentCount = workspace.routing_trace?.filter((hop) => hop.to !== "FINISH").length || 0;
  const latency = (workspace.routing_trace || []).reduce((total, hop) => total + (hop.latency_ms || 0), 0)
    + (workspace.tool_logs || []).reduce((total, call) => total + (call.latency_ms || 0), 0);

  const pageTitle = navigation.find((item) => item.id === activePage)?.label || "Overview";

  function chooseScenario(name) {
    setSelectedScenario(name);
    setPrompt(scenarios.find((scenario) => scenario.name === name)?.prompt || "");
  }

  async function runWorkflow(event) {
    event?.preventDefault();
    setError("");
    setNotice("");
    if (!prompt.trim()) {
      setError("Write an instruction or choose a demo scenario to get started.");
      return;
    }
    setRunning(true);
    try {
      await api(`/api/session/${sessionId}/run`, {
        method: "POST",
        body: JSON.stringify({ prompt, model_id: model, api_key: apiKey || null }),
      });
      await refreshWorkspace(sessionId);
      setNotice("Workflow complete. Your workspace has been updated.");
      setActivePage("overview");
    } catch (requestError) {
      setError(requestError.message);
      await refreshWorkspace(sessionId).catch(() => {});
    } finally {
      setRunning(false);
    }
  }

  async function resetWorkspace() {
    if (!window.confirm("Reset this workspace and clear all demo activity?")) return;
    setError("");
    try {
      await api(`/api/session/${sessionId}/reset`, { method: "POST" });
      await refreshWorkspace(sessionId);
      setNotice("Workspace restored to the original demo data.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  const openSettings = () => {
    setSettingsOpen(true);
    setError("");
  };

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNavOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Sparkles size={20} strokeWidth={2.2} /></div>
          <div><strong>AdminHelp</strong><span>ADMIN INTELLIGENCE</span></div>
          <button className="icon-button mobile-close" onClick={() => setMobileNavOpen(false)} aria-label="Close menu"><X size={19} /></button>
        </div>
        <button className="workspace-switcher">
          <span className="workspace-avatar"><Building2 size={17} /></span>
          <span className="workspace-copy"><strong>company pvt ltd</strong><small>Enterprise workspace</small></span>
          <ChevronDown size={16} className="muted-icon" />
        </button>
        <div className="nav-caption">WORKSPACE</div>
        <nav className="nav-list" aria-label="Main navigation">
          {navigation.map((item) => {
            const Icon = item.icon;
            const rawCount = item.countKey ? workspace[item.countKey] : null;
            const count = rawCount ? Object.keys(rawCount).length : 0;
            return (
              <button
                key={item.id}
                className={`nav-item ${activePage === item.id ? "nav-active" : ""}`}
                onClick={() => { setActivePage(item.id); setMobileNavOpen(false); }}
              >
                <Icon size={18} strokeWidth={1.8} /><span>{item.label}</span>
                {count > 0 && <span className="nav-count">{count}</span>}
              </button>
            );
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="trust-card">
            <div className="trust-icon"><ShieldCheck size={17} /></div>
            <div><strong>Governance active</strong><small>Actions follow company policy</small></div>
          </div>
          <button className="profile-button" onClick={openSettings}>
            <span className="profile-avatar">AC</span>
            <span className="profile-copy"><strong>Admin console</strong><small>Workspace settings</small></span>
            <Settings2 size={17} className="muted-icon" />
          </button>
        </div>
      </aside>

      {mobileNavOpen && <button className="mobile-backdrop" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation" />}

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button className="icon-button mobile-menu" onClick={() => setMobileNavOpen(true)} aria-label="Open menu"><Menu size={20} /></button>
            <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>{pageTitle}</strong></div>
          </div>
          <div className="topbar-actions">
            <div className="system-status"><span className="status-dot" /> All systems operational</div>
            <button className="icon-button notification-button" aria-label="Notifications"><Bell size={18} /><i /></button>
            <span className="topbar-divider" />
            <button className="top-profile" onClick={openSettings}><span className="profile-avatar small-avatar">AC</span><ChevronDown size={15} /></button>
          </div>
        </header>

        <div className="page-content">
          {error && <div className="alert alert-error"><CircleHelp size={18} /><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss error"><X size={16} /></button></div>}
          {notice && <div className="alert alert-success"><Check size={18} /><span>{notice}</span><button onClick={() => setNotice("")} aria-label="Dismiss message"><X size={16} /></button></div>}
          {loading ? <LoadingState /> : (
            <>
              {activePage === "overview" && (
                <OverviewPage
                  workspace={workspace}
                  scenarios={scenarios}
                  selectedScenario={selectedScenario}
                  prompt={prompt}
                  running={running}
                  onScenarioChange={chooseScenario}
                  onPromptChange={setPrompt}
                  onRun={runWorkflow}
                  onNavigate={setActivePage}
                  employeeCount={employeeCount}
                  agentCount={agentCount}
                  latency={latency}
                />
              )}
              {activePage === "emails" && <CollectionPage title="Email center" subtitle="Calendar invitations and communication sent by your admin agents." icon={Mail} rows={workspace.sent_emails} empty="No invitations sent yet." render={(mail) => <EmailCard key={mail.email_id} mail={mail} />} />}
              {activePage === "calendar" && <CollectionPage title="Calendar" subtitle="Meetings booked across your team's calendars." icon={CalendarDays} rows={workspace.calendar_events} empty="No meetings booked yet." render={(event) => <EventCard key={event.event_id} event={event} />} />}
              {activePage === "travel" && <CollectionPage title="Travel & visa desk" subtitle="Travel approvals, visa determinations, and supporting documentation." icon={Plane} rows={workspace.travel_visa_requests} empty="No travel or visa requests yet." render={(request) => <TravelCard key={request.request_id} request={request} />} />}
              {activePage === "expenses" && <CollectionPage title="Expense review" subtitle="Receipts and vendor invoices reconciled against company policy." icon={CreditCard} rows={workspace.expense_reports} empty="No expenses have been triaged." render={(expense) => <ExpenseCard key={expense.expense_id} expense={expense} />} />}
              {activePage === "onboarding" && <OnboardingPage ledger={workspace.onboarding_ledger} />}
              {activePage === "directory" && <DirectoryPage workspace={workspace} />}
              {activePage === "architecture" && <ArchitecturePage workspace={workspace} />}
            </>
          )}
        </div>
      </main>

      {settingsOpen && (
        <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && setSettingsOpen(false)}>
          <section className="settings-modal" role="dialog" aria-modal="true" aria-labelledby="settings-title">
            <div className="modal-heading"><div><div className="eyebrow">WORKSPACE CONFIGURATION</div><h2 id="settings-title">Settings</h2></div><button className="icon-button" onClick={() => setSettingsOpen(false)} aria-label="Close settings"><X size={19} /></button></div>
            <label className="field-label" htmlFor="model-select">Groq model</label>
            <select id="model-select" className="text-input" value={model} onChange={(event) => setModel(event.target.value)}><option value="openai/gpt-oss-120b">GPT OSS 120B</option></select>
            <label className="field-label key-label" htmlFor="api-key">Groq API key <span>Optional if configured on the server</span></label>
            <input id="api-key" className="text-input" type="password" autoComplete="off" placeholder="gsk_••••••••••••••••••••" value={apiKey} onChange={(event) => setApiKey(event.target.value)} />
            <div className="settings-hint"><KeyRound size={16} /><span>Your key is sent only to this server for workflow execution and is never saved in the browser workspace.</span></div>
            <div className="modal-footer"><button className="button button-quiet" onClick={resetWorkspace}><RotateCcw size={16} /> Reset workspace</button><button className="button button-primary" onClick={() => setSettingsOpen(false)}>Done</button></div>
          </section>
        </div>
      )}
    </div>
  );
}

function LoadingState() {
  return <div className="loading-state"><div className="loading-orb"><Sparkles size={23} /></div><h2>Preparing your workspace</h2><p>Connecting to your enterprise admin environment…</p></div>;
}

function OverviewPage({ workspace, scenarios, selectedScenario, prompt, running, onScenarioChange, onPromptChange, onRun, onNavigate, employeeCount, agentCount, latency }) {
  const stats = [
    { label: "Team members", value: employeeCount, icon: Users, tone: "violet", detail: "Active directory" },
    { label: "Meetings booked", value: workspace.calendar_events.length, icon: CalendarDays, tone: "blue", detail: "On company calendars" },
    { label: "Travel requests", value: workspace.travel_visa_requests.length, icon: Plane, tone: "amber", detail: "Reviewed by policy" },
    { label: "New hires", value: Object.keys(workspace.onboarding_ledger).length, icon: UserPlusIcon, tone: "green", detail: "Onboarding records" },
  ];
  return (
    <>
      <section className="welcome-row">
        <div><div className="eyebrow">MONDAY, OCTOBER 26, 2026 <span className="eyebrow-dot" /> YOUR OPERATIONS, IN ORBIT</div><h1>Good morning, Admin <span className="wave">✦</span></h1><p>Your people operations are in good shape. Here's the latest from your workspace.</p></div>
        <div className="welcome-actions"><span className="date-pill"><CalendarDays size={15} /> Monday, Oct 26</span><button className="button button-quiet" onClick={onRun} disabled={running}><WandSparkles size={16} /> Run command</button></div>
      </section>
      {workspace.final_summary && <section className="executive-summary"><div className="summary-check"><Check size={18} /></div><div><div className="eyebrow">EXECUTIVE SUMMARY</div><h2>Workflow complete</h2><p>{workspace.final_summary}</p></div></section>}
      <section className="stat-grid" aria-label="Workspace metrics">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return <div className="stat-card" key={stat.label}><div className="stat-top"><div className={`stat-icon ${stat.tone}`}><Icon size={18} /></div><span className="stat-trend"><ArrowUpRight size={14} /> Live</span></div><div className="stat-value">{stat.value}</div><div className="stat-label">{stat.label}</div><div className="stat-detail">{stat.detail}</div></div>;
        })}
      </section>

      <section className="overview-grid">
        <div className="command-card">
          <div className="command-header"><div className="command-icon"><Command size={19} /></div><div><h2>What can I take off your plate?</h2><p>Tell your AI team what needs to get done.</p></div><span className="ai-chip"><Sparkles size={13} /> AI COMMAND</span></div>
          <form onSubmit={onRun}>
            <label className="field-label" htmlFor="scenario">Start with a workflow</label>
            <div className="select-wrap"><select id="scenario" value={selectedScenario} onChange={(event) => onScenarioChange(event.target.value)}><option value="">Choose a demo scenario or write your own</option>{scenarios.map((scenario) => <option key={scenario.name} value={scenario.name}>{scenario.name}</option>)}</select><ChevronDown size={16} /></div>
            <label className="sr-only" htmlFor="command-prompt">Natural language instruction</label>
            <textarea id="command-prompt" value={prompt} onChange={(event) => onPromptChange(event.target.value)} placeholder="e.g. Schedule a team town hall for next week…" rows={4} />
            <div className="command-footer"><span><ShieldCheck size={15} /> Actions are checked against company policy</span><button className="button button-primary" type="submit" disabled={running}>{running ? <><LoaderCircle className="spin" size={16} /> Working…</> : <><Send size={15} /> Run workflow <ArrowDownRight size={15} /></>}</button></div>
          </form>
          {running && <div className="run-progress"><div className="progress-track"><span /></div><span>Coordinating your specialist agents…</span></div>}
        </div>
        <div className="activity-card">
          <div className="section-heading"><div><h2>Agent activity</h2><p>Live workflow observability</p></div><button className="text-button" onClick={() => onNavigate("architecture")}>View details <ArrowUpRight size={14} /></button></div>
          {workspace.routing_trace.length ? (
            <div className="activity-list">{workspace.routing_trace.slice(-4).reverse().map((hop, index) => <div className="activity-item" key={`${hop.hop}-${index}`}><div className={`activity-node ${hop.to === "END" ? "activity-done" : ""}`}><Workflow size={15} /></div><div className="activity-copy"><strong>{formatAgent(hop.from)} <span>→</span> {formatAgent(hop.to)}</strong><small>{hop.reasoning}</small></div><span className="activity-time">{hop.latency_ms} ms</span></div>)}</div>
          ) : <div className="empty-activity"><div className="empty-orbit"><Workflow size={19} /></div><strong>Your agents are standing by</strong><span>Run a workflow to see the supervisor and specialist agents in action.</span></div>}
          <div className="activity-summary"><div><span className="summary-dot green-dot" /> <strong>{agentCount}</strong><small> agents activated</small></div><span className="summary-divider" /><div><Clock3 size={14} /><strong>{latency ? `${Math.round(latency)} ms` : "—"}</strong><small> total latency</small></div></div>
        </div>
      </section>

      <section className="lower-grid">
        <div className="recent-card">
          <div className="section-heading"><div><h2>Recent operations</h2><p>Latest activity across your enterprise</p></div><button className="text-button" onClick={() => onNavigate("calendar")}>Open calendar <ArrowUpRight size={14} /></button></div>
          {workspace.calendar_events.length ? workspace.calendar_events.slice(-3).reverse().map((event) => <div className="recent-row" key={event.event_id}><div className="recent-icon calendar-recent"><CalendarDays size={17} /></div><div className="recent-main"><strong>{event.title}</strong><span>{event.start_time_utc} · {event.attendees.length} attendees</span></div><StatusPill value={event.status} /></div>) : <div className="recent-empty"><span className="recent-icon calendar-recent"><CalendarDays size={17} /></span><span><strong>Nothing on the calendar yet</strong><small>Ask your scheduling agent to book a meeting.</small></span><button className="icon-button add-button" onClick={() => onNavigate("calendar")} aria-label="Open calendar"><Plus size={17} /></button></div>}
        </div>
        <div className="quick-card">
          <div className="section-heading"><div><h2>Quick links</h2><p>Jump into your workspace</p></div></div>
          <button className="quick-link" onClick={() => onNavigate("directory")}><span className="quick-icon quick-people"><Users size={16} /></span><span><strong>People directory</strong><small>{employeeCount} active team members</small></span><ArrowUpRight size={15} /></button>
          <button className="quick-link" onClick={() => onNavigate("expenses")}><span className="quick-icon quick-spend"><CreditCard size={16} /></span><span><strong>Expense review</strong><small>{workspace.expense_reports.length} reports in the ledger</small></span><ArrowUpRight size={15} /></button>
          <button className="quick-link" onClick={() => onNavigate("architecture")}><span className="quick-icon quick-agents"><Activity size={16} /></span><span><strong>Agent observability</strong><small>Routing & tool call telemetry</small></span><ArrowUpRight size={15} /></button>
        </div>
      </section>
    </>
  );
}

function UserPlusIcon(props) {
  return <Users {...props} />;
}

function CollectionPage({ title, subtitle, icon: Icon, rows, empty, render }) {
  return <section className="detail-page"><PageHeading title={title} subtitle={subtitle} icon={Icon} /><div className="collection-toolbar"><span>{rows.length} {rows.length === 1 ? "record" : "records"}</span><span className="live-tag"><span className="status-dot" /> LIVE WORKSPACE DATA</span></div>{rows.length ? <div className="collection-list">{[...rows].reverse().map(render)}</div> : <EmptyState title={empty} detail="Once an agent completes an action, it will appear here." />}</section>;
}

function PageHeading({ title, subtitle, icon: Icon }) {
  return <div className="page-heading"><div className="page-heading-icon"><Icon size={21} /></div><div><div className="eyebrow">ENTERPRISE OPERATIONS</div><h1>{title}</h1><p>{subtitle}</p></div></div>;
}

function EmailCard({ mail }) {
  return <article className="record-card"><div className="record-heading"><div className="record-title"><div className="record-icon blue"><Mail size={17} /></div><div><h3>{mail.subject}</h3><span>{mail.email_id}</span></div></div><StatusPill value="SENT" /></div><div className="record-meta"><span><Users size={15} /> {mail.to.length} recipients</span><span><Clock3 size={15} /> {mail.start_time_utc}</span><a href={mail.meeting_link} target="_blank" rel="noreferrer">Open meeting link <ArrowUpRight size={13} /></a></div><div className="agenda-box"><span>AGENDA</span><p>{mail.single_paragraph_agenda}</p></div><div className="record-subtext"><strong>Local time breakdown</strong><p>{mail.local_time_breakdown}</p></div></article>;
}

function EventCard({ event }) {
  return <article className="record-card"><div className="record-heading"><div className="record-title"><div className="record-icon blue"><CalendarDays size={17} /></div><div><h3>{event.title}</h3><span>{event.event_id}</span></div></div><StatusPill value={event.status} /></div><div className="record-meta"><span><Clock3 size={15} /> {event.start_time_utc} · {event.duration_minutes} min</span><span><Users size={15} /> {event.attendees.length} attendees</span><a href={event.meeting_link} target="_blank" rel="noreferrer">Join meeting <ArrowUpRight size={13} /></a></div><div className="agenda-box"><span>MEETING AGENDA</span><p>{event.agenda}</p></div><div className="attendee-list">{event.attendees.map((attendee) => <span className="email-chip" key={attendee}>{attendee}</span>)}</div></article>;
}

function TravelCard({ request }) {
  return <article className="record-card"><div className="record-heading"><div className="record-title"><div className="record-icon amber"><Plane size={17} /></div><div><h3>{request.employee_name} <span className="title-arrow">→</span> {request.destination}</h3><span>{request.request_id} · {request.visa_type}</span></div></div><StatusPill value={request.status} /></div><div className="data-grid"><DataPoint label="Estimated cost" value={money(request.estimated_cost_usd)} /><DataPoint label="Policy verdict" value={request.policy_verdict} /><DataPoint label="Approver" value={request.routed_to_approver} /><DataPoint label="Required documents" value={request.required_documents.join(", ")} /></div><div className="record-subtext"><strong>Justification</strong><p>{request.justification_summary}</p></div></article>;
}

function ExpenseCard({ expense }) {
  return <article className="record-card"><div className="record-heading"><div className="record-title"><div className="record-icon green"><CreditCard size={17} /></div><div><h3>{expense.submitter_or_vendor}</h3><span>{expense.expense_id} · {expense.category}</span></div></div><StatusPill value={expense.status} /></div><div className="data-grid"><DataPoint label="Amount" value={money(expense.amount_usd)} /><DataPoint label="Purchase order" value={expense.po_number} /><DataPoint label="Reconciliation" value={expense.reconciliation_notes} /></div>{expense.anomaly_flags?.length > 0 && <div className="anomaly-box"><ShieldCheck size={16} /><span>{expense.anomaly_flags.join(" · ")}</span></div>}</article>;
}

function DataPoint({ label, value }) {
  return <div className="data-point"><span>{label}</span><strong>{value || "—"}</strong></div>;
}

function OnboardingPage({ ledger }) {
  const hires = Object.entries(ledger || {});
  return <section className="detail-page"><PageHeading title="Onboarding" subtitle="New hire offers, software access, and IT provisioning." icon={Users} /><div className="collection-toolbar"><span>{hires.length} {hires.length === 1 ? "new hire" : "new hires"}</span><span className="live-tag"><span className="status-dot" /> PROVISIONING LEDGER</span></div>{hires.length ? <div className="collection-list">{hires.reverse().map(([key, record]) => { const offer = record.offer || {}; const keys = record.it_keys || {}; return <article className="record-card" key={key}><div className="record-heading"><div className="record-title"><div className="record-icon green"><Users size={17} /></div><div><h3>{offer.candidate_name || key}</h3><span>{offer.role_title || "New hire"} · {offer.offer_id || "Offer issued"}</span></div></div><StatusPill value={offer.status || "IN PROGRESS"} /></div><div className="data-grid"><DataPoint label="Corporate email" value={offer.corporate_email} /><DataPoint label="Timezone" value={offer.timezone} /><DataPoint label="Citizenship" value={offer.citizenship} /><DataPoint label="Hardware" value={keys.hardware_assigned} /><DataPoint label="IT ticket" value={keys.it_ticket_id} /><DataPoint label="Temporary SSO" value={keys.temp_sso_key} /></div><div className="license-list"><strong>Software access</strong>{Object.entries(record.licenses || {}).length ? Object.entries(record.licenses).map(([name, license]) => <span className="license-chip" key={name}><Check size={13} /> {name} <small>{license.seat_id}</small></span>) : <span className="muted-text">No licenses assigned.</span>}</div></article>; })}</div> : <EmptyState title="No hires onboarded yet." detail="Run an onboarding workflow and the provisioning ledger will appear here." />}</section>;
}

function DirectoryPage({ workspace }) {
  const employees = Object.entries(workspace.directory || {});
  return <section className="detail-page"><PageHeading title="People & policy" subtitle="Your employee directory, purchase orders, and active governance controls." icon={Building2} /><div className="section-heading directory-heading"><div><h2>People directory</h2><p>{employees.length} active employees across your organization</p></div><span className="live-tag"><span className="status-dot" /> AMBIENT CONTEXT</span></div><div className="people-grid">{employees.map(([key, person]) => <article className="person-card" key={key}><div className="person-top"><span className="person-avatar">{initials(person.name)}</span><span className="person-presence" /></div><h3>{person.name}</h3><p>{person.role}</p><div className="person-department">{person.department}</div><div className="person-info"><span><Mail size={14} /> {person.email}</span><span><Building2 size={14} /> {person.timezone}</span><span><ShieldCheck size={14} /> Manager: {person.manager}</span><span><FileText size={14} /> Citizenship: {person.citizenship}</span></div></article>)}</div><div className="section-heading policy-heading"><div><h2>Purchase orders & policy</h2><p>Live controls applied to agent decisions.</p></div></div><div className="governance-grid"><div className="po-card"><div className="compact-heading"><div className="record-icon violet"><FileText size={17} /></div><div><strong>Active purchase orders</strong><small>Available for invoice matching</small></div></div>{Object.entries(workspace.purchase_orders || {}).map(([id, po]) => <div className="po-row" key={id}><span><strong>{id}</strong><small>{po.vendor} · {po.department}</small></span><b>{money(po.budget_usd)}</b></div>)}</div><div className="po-card policy-card"><div className="compact-heading"><div className="record-icon amber"><ShieldCheck size={17} /></div><div><strong>Corporate policy limits</strong><small>Enforced during workflow execution</small></div></div>{Object.entries(workspace.corporate_policies || {}).map(([key, value]) => <div className="policy-row" key={key}><span>{humanize(key)}</span><strong>{key.includes("cap") || key.includes("threshold") ? money(value) : `${value} min`}</strong></div>)}</div></div></section>;
}

function ArchitecturePage({ workspace }) {
  const hops = workspace.routing_trace || [];
  const calls = workspace.tool_logs || [];
  return <section className="detail-page"><PageHeading title="Agent activity" subtitle="A transparent view of supervisor routing, specialist agents, and deterministic tool calls." icon={Workflow} /><div className="architecture-stats"><div><span>ROUTING HOPS</span><strong>{hops.length}</strong></div><div><span>TOOL CALLS</span><strong>{calls.length}</strong></div><div><span>WORKERS ACTIVATED</span><strong>{new Set(hops.map((hop) => hop.to).filter((to) => to.endsWith("_agent"))).size}</strong></div></div><div className="section-heading architecture-section"><div><h2>Supervisor routing trace</h2><p>LangGraph conditional transitions for the latest run.</p></div></div>{hops.length ? <div className="trace-list">{hops.map((hop) => <article className="trace-card" key={hop.hop}><div className="trace-step">{String(hop.hop).padStart(2, "0")}</div><div className="trace-main"><div><strong>{formatAgent(hop.from)}</strong><span className="trace-arrow">→</span><strong>{formatAgent(hop.to)}</strong></div><p>{hop.reasoning}</p></div><span className="trace-latency"><Clock3 size={14} /> {hop.latency_ms} ms</span></article>)}</div> : <EmptyState title="No routing activity yet." detail="Run a workflow to inspect how the supervisor delegates work." />}<div className="section-heading architecture-section"><div><h2>Tool call telemetry</h2><p>Inputs and deterministic results from domain agents.</p></div></div>{calls.length ? <div className="tool-list">{[...calls].reverse().map((call) => <details className="tool-card" key={`${call.step}-${call.tool}`}><summary><span className="tool-number">{String(call.step).padStart(2, "0")}</span><span className="tool-summary"><strong>{call.tool}()</strong><small>{formatAgent(call.agent)} · {call.latency_ms} ms</small></span><ChevronDown size={16} /></summary><div className="tool-payloads"><JsonPanel title="Arguments passed by agent" value={call.args} /><JsonPanel title="Deterministic result" value={call.output} /></div></details>)}</div> : <EmptyState title="No tool calls recorded." detail="Agent tool calls and outputs will be listed here." />}<div className="section-heading architecture-section"><div><h2>Ambient context & graph state</h2><p>Enterprise data snapshot supplied to every specialist.</p></div></div><div className="context-grid"><JsonPanel title="Ambient enterprise context" value={workspace.ambient_context || "No ambient context available."} /><JsonPanel title="Latest graph state" value={workspace.last_graph_state} /></div></section>;
}

function JsonPanel({ title, value }) {
  return <div className="json-panel"><div className="json-title"><FileText size={15} /> {title}</div><pre>{typeof value === "string" ? value : JSON.stringify(value || {}, null, 2)}</pre></div>;
}

function EmptyState({ title, detail }) {
  return <div className="empty-state"><div className="empty-orbit"><Sparkles size={19} /></div><h3>{title}</h3><p>{detail}</p></div>;
}

function StatusPill({ value }) {
  const normalized = String(value || "PENDING").toUpperCase();
  const tone = normalized.includes("APPROVED") || normalized.includes("CONFIRMED") || normalized.includes("SENT") || normalized.includes("ACTIVE") ? "status-good" : normalized.includes("PENDING") || normalized.includes("FLAGGED") || normalized.includes("REVIEW") || normalized.includes("OVERRIDE") ? "status-warn" : "status-neutral";
  return <span className={`status-pill ${tone}`}><span />{normalized.replaceAll("_", " ")}</span>;
}

function formatAgent(value) {
  return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function initials(name) {
  return String(name || "").split(" ").slice(0, 2).map((part) => part[0] || "").join("").toUpperCase();
}

function money(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(Number(value || 0));
}

function humanize(value) {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default App;
