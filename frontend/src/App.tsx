import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import {
  ArrowRight, ArrowUp, CalendarDays, Check, CircleHelp,
  Clock3, Inbox, ListTodo, LoaderCircle, Mail, MessageSquarePlus,
  Plus, RefreshCw, Search, ShieldCheck, Sparkles, Trash2, X,
} from "lucide-react";

type ChatFilter = { id: string; label: string; prompt: string; icon?: string; custom?: boolean };
type ChatEmailOption = {
  id: string; subject: string; sender: string; received_at?: string | null;
  summary?: string | null; priority?: "Critical" | "High" | "Medium" | "Low" | null;
  requires_action?: boolean | null; requires_attention?: boolean | null; action_items?: string[];
};
type EmailDetail = { id: string; subject: string; sender: string; receiver: string; body: string; received_at?: string | null };
type Message = { id: string; role: "user" | "assistant"; text: string; time: Date; filterLabel?: string; emailOptions?: ChatEmailOption[] };
type ChatResponse = { thread_id: string; response: string; current_email_id?: string | null; email_options?: ChatEmailOption[]; detail?: string };
type WorkspaceView = "assistant" | "inbox" | "tasks" | "meetings";
type MailboxEmail = ChatEmailOption & { is_read: boolean };
type TaskItem = { id: string; title: string; description: string; status: string; priority: string };
type MeetingItem = { id: string; title: string; start: string; end?: string | null; all_day: boolean; location?: string | null; url?: string | null };
type WorkspaceItem = MailboxEmail | TaskItem | MeetingItem;

const builtInFilters: ChatFilter[] = [
  { id: "important_unread", label: "Unread important", prompt: "Show my unread emails rated High or Critical", icon: "inbox" },
  { id: "escalated_unread", label: "Escalated emails", prompt: "Show unread escalated emails", icon: "sparkles" },
  { id: "customer_unread", label: "Customer emails", prompt: "Show unread customer emails", icon: "mail" },
  { id: "my_tasks", label: "Tasks assigned to me", prompt: "Show my tasks", icon: "tasks" },
  { id: "my_meetings", label: "My meetings", prompt: "Show my meetings", icon: "calendar" },
];

const iconFor = (name?: string) => {
  const props = { size: 16, strokeWidth: 1.8 };
  switch (name) {
    case "inbox": return <Inbox {...props} />;
    case "sparkles": return <Sparkles {...props} />;
    case "tasks": return <ListTodo {...props} />;
    case "calendar": return <CalendarDays {...props} />;
    default: return <Mail {...props} />;
  }
};

function readCustomFilters(): ChatFilter[] {
  try {
    const saved: unknown = JSON.parse(localStorage.getItem("bridgeai-email-chat-filters") ?? "[]");
    if (!Array.isArray(saved)) return [];
    return saved.filter((item: unknown): item is ChatFilter => {
      if (!item || typeof item !== "object") return false;
      const candidate = item as Record<string, unknown>;
      return typeof candidate.id === "string" && typeof candidate.label === "string" && typeof candidate.prompt === "string";
    }).slice(0, 12);
  } catch {
    return [];
  }
}

function App() {
  const [view, setView] = useState<WorkspaceView>("assistant");
  const [workspaceItems, setWorkspaceItems] = useState<WorkspaceItem[]>([]);
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [workspaceError, setWorkspaceError] = useState("");
  const [inboxQuery, setInboxQuery] = useState("");
  const [threadId, setThreadId] = useState(() => sessionStorage.getItem("bridgeai-email-thread") || crypto.randomUUID());
  const [customFilters, setCustomFilters] = useState<ChatFilter[]>(readCustomFilters);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [filterName, setFilterName] = useState("");
  const [filterPrompt, setFilterPrompt] = useState("");
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [scrolled, setScrolled] = useState(true);
  const [openedEmail, setOpenedEmail] = useState<{ email: EmailDetail | null; loading: boolean; error?: string } | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => { sessionStorage.setItem("bridgeai-email-thread", threadId); }, [threadId]);
  useEffect(() => { localStorage.setItem("bridgeai-email-chat-filters", JSON.stringify(customFilters)); }, [customFilters]);
  useEffect(() => {
    if (scrolled && listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, busy, scrolled]);

  useEffect(() => {
    if (view !== "assistant") void loadWorkspace(view);
  }, [view]);

  async function loadWorkspace(target: WorkspaceView = view) {
    const endpoint = target === "inbox" ? "/emails?limit=50" : target === "tasks" ? "/tasks" : "/meetings?limit=50";
    setWorkspaceLoading(true);
    setWorkspaceError("");
    try {
      const response = await fetch(endpoint);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Could not load ${target}.`);
      setWorkspaceItems(Array.isArray(data) ? data as WorkspaceItem[] : []);
    } catch (caught) {
      setWorkspaceError(caught instanceof Error ? caught.message : `Could not load ${target}.`);
      setWorkspaceItems([]);
    } finally {
      setWorkspaceLoading(false);
    }
  }

  async function submitMessage(text: string, filter?: ChatFilter, selectedEmailId?: string) {
    const clean = text.trim();
    if (!clean || busy) return;
    setError("");
    setActiveFilter(filter?.id ?? null);
    setMessages((current) => [...current, {
      id: crypto.randomUUID(), role: "user", text: clean, time: new Date(), filterLabel: filter?.label,
    }]);
    setDraft("");
    setBusy(true);
    try {
      const response = await fetch("/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: clean,
          thread_id: threadId,
          filter_id: filter && !filter.custom ? filter.id : undefined,
          selected_email_id: selectedEmailId,
        }),
      });
      const data = await response.json().catch(() => ({})) as Partial<ChatResponse>;
      if (!response.ok) throw new Error(data.detail || `The request failed (${response.status}).`);
      setMessages((current) => [...current, {
        id: crypto.randomUUID(), role: "assistant", text: data.response || "I couldn’t complete that request.",
        time: new Date(), emailOptions: data.email_options,
      }]);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "BridgeAI could not reach the local service.";
      setError(message);
      setMessages((current) => [...current, {
        id: crypto.randomUUID(), role: "assistant", text: "I couldn’t reach the Email Agent service. Check that the app is running, then try again.", time: new Date(),
      }]);
    } finally {
      setBusy(false);
      setActiveFilter(null);
      inputRef.current?.focus();
    }
  }

  async function openEmail(emailId: string) {
    setOpenedEmail({ email: null, loading: true });
    try {
      const response = await fetch(`/emails/${encodeURIComponent(emailId)}`);
      if (!response.ok) throw new Error(response.status === 404 ? "This email is no longer available." : "Could not open this email.");
      const email = await response.json() as EmailDetail;
      setOpenedEmail({ email, loading: false });
    } catch (caught) {
      setOpenedEmail({ email: null, loading: false, error: caught instanceof Error ? caught.message : "Could not open this email." });
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitMessage(draft);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      inputRef.current?.form?.requestSubmit();
    }
  }

  function addFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const label = filterName.trim();
    const prompt = filterPrompt.trim();
    if (!label || !prompt || customFilters.length >= 12) return;
    const next = [...customFilters, { id: `custom-${crypto.randomUUID()}`, label, prompt, custom: true }];
    setCustomFilters(next);
    setFilterName("");
    setFilterPrompt("");
    setModalOpen(false);
  }

  function removeFilter(id: string) {
    setCustomFilters((filters) => filters.filter((filter) => filter.id !== id));
  }

  function newConversation() {
    const nextThreadId = crypto.randomUUID();
    setThreadId(nextThreadId);
    sessionStorage.setItem("bridgeai-email-thread", nextThreadId);
    setMessages([]);
    setError("");
    setScrolled(true);
  }

  function askAgentAbout(email: MailboxEmail) {
    setView("assistant");
    void submitMessage(`Summarize this email from ${email.sender}`, undefined, email.id);
  }

  const allFilters = [...builtInFilters, ...customFilters];
  const pageTitle = view === "assistant" ? "Email Agent" : view === "inbox" ? "Inbox" : view === "tasks" ? "Tasks" : "Meetings";

  return (
    <div className="app-shell app-layout">
      <aside className="sidebar" aria-label="Main navigation">
        <a className="brand sidebar-brand" href="/" aria-label="BridgeAI Email Agent home">
          <span className="brand-mark"><Mail size={19} strokeWidth={2.1} /></span>
          <span className="brand-text"><strong>BridgeAI</strong><span>Email Agent</span></span>
        </a>
        <div className="sidebar-section-label">WORKSPACE</div>
        <nav className="primary-nav">
          {([
            ["assistant", "Assistant", Sparkles], ["inbox", "Inbox", Inbox],
            ["tasks", "My tasks", ListTodo], ["meetings", "Meetings", CalendarDays],
          ] as const).map(([id, label, Icon]) => (
            <button key={id} type="button" className={`nav-link ${view === id ? "active" : ""}`} onClick={() => setView(id)} aria-current={view === id ? "page" : undefined}>
              <Icon size={17} strokeWidth={1.8} /><span>{label}</span><ArrowRight className="nav-arrow" size={14} />
            </button>
          ))}
        </nav>
        <div className="sidebar-spacer" />
        <div className="sidebar-local"><span className="local-dot" /><div><strong>Private workspace</strong><span>Single-user app</span></div></div>
      </aside>
      <div className="app-main">
      <header className="topbar">
        <div className="page-heading"><span className="page-kicker">YOUR EMAIL WORKSPACE</span><strong>{pageTitle}</strong></div>
        <div className="topbar-right">
          <span className="topbar-private"><ShieldCheck size={15} /> Local and private</span>
          {view === "assistant" && <button className="icon-button new-chat" type="button" onClick={newConversation} title="New conversation" aria-label="New conversation"><MessageSquarePlus size={18} /></button>}
        </div>
      </header>

      <main className="workspace">
        {view === "assistant" ? <>
        <section className="welcome-row">
          <div>
            <div className="eyebrow"><span className="eyebrow-dot" /> YOUR EMAIL WORKSPACE</div>
            <h1>What would you like to work on?</h1>
            <p>Ask about your mailbox, or use a chat filter to get started.</p>
          </div>
          <div className="today-card"><Clock3 size={17} /><span>{new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "numeric" }).format(new Date())}</span></div>
        </section>

        <section className="filters-section" aria-labelledby="filters-heading">
          <div className="filters-heading-row">
            <div className="filters-title"><h2 id="filters-heading">Chat filters</h2><span className="info-wrap" title="A filter is a saved instruction sent to the Email Agent."><CircleHelp size={14} /></span></div>
            <span className="filter-hint">Choose one to send its instruction</span>
          </div>
          <div className="filter-list">
            {allFilters.map((filter) => (
              <div className="filter-wrap" key={filter.id}>
                <button
                  className={`filter-chip ${activeFilter === filter.id ? "selected" : ""}`}
                  type="button"
                  disabled={busy}
                  onClick={() => void submitMessage(filter.prompt, filter)}
                >
                  {iconFor(filter.icon)}<span>{filter.label}</span>
                </button>
                {filter.custom && <button className="filter-remove" type="button" onClick={() => removeFilter(filter.id)} aria-label={`Remove ${filter.label}`} title="Remove filter"><X size={12} /></button>}
              </div>
            ))}
            <button className="filter-chip add-filter" type="button" onClick={() => setModalOpen(true)} disabled={customFilters.length >= 12}>
              <Plus size={16} /><span>Add filter</span>
            </button>
          </div>
        </section>

        <section className="chat-card" aria-label="Email Agent conversation">
          <div className="chat-card-head">
            <div className="agent-avatar"><Sparkles size={18} /></div>
            <div className="chat-title"><h2>Email Agent</h2><span>Ready when you are</span></div>
            <button className="clear-button" type="button" onClick={newConversation} disabled={!messages.length || busy}>
              <Trash2 size={15} /> Clear chat
            </button>
          </div>

          <div className="chat-body" ref={listRef} onScroll={(event) => {
            const element = event.currentTarget;
            setScrolled(element.scrollHeight - element.scrollTop - element.clientHeight < 80);
          }}>
            {messages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon"><Sparkles size={24} /></div>
                <h3>Your email assistant is ready</h3>
                <p>Ask a question about an email, request a summary, or choose a chat filter above.</p>
                <div className="suggestions">
                  <button type="button" onClick={() => void submitMessage("Show the last five emails")}>Show my latest emails <ArrowUp size={14} /></button>
                  <button type="button" onClick={() => void submitMessage("What needs my attention in my emails?")}>Find action items <ArrowUp size={14} /></button>
                </div>
              </div>
            ) : (
              <div className="message-list">
                {messages.map((message) => (
                  <article className={`message-row ${message.role}`} key={message.id}>
                    {message.role === "assistant" && <div className="message-avatar"><Sparkles size={15} /></div>}
                    <div className="message-content">
                      {message.filterLabel && <div className="filter-context">{iconFor(allFilters.find((filter) => filter.label === message.filterLabel)?.icon)}<span>{message.filterLabel}</span></div>}
                      <div className={`message-bubble ${message.role}`}>{message.text}</div>
                      {message.role === "assistant" && message.emailOptions?.length ? (
                        <div className="email-options" aria-label="Emails in this result">
                          {message.emailOptions.map((email) => (
                            <article className="email-option" key={email.id}>
                              <button className="email-option-open" type="button" onClick={() => void openEmail(email.id)} title="Open full email">
                                <div className="email-option-copy">
                                  <strong title={email.subject || "(No subject)"}>{email.subject || "(No subject)"}</strong>
                                  <span>{email.sender}{email.received_at ? ` · ${new Date(email.received_at).toLocaleString()}` : ""}</span>
                                  {email.priority && <span className={`priority-badge priority-${email.priority.toLowerCase()}`}>{email.priority} priority</span>}
                                  {email.summary && <span className="email-option-summary">{email.summary}</span>}
                                  {email.action_items?.length ? <span className="email-option-actions-summary">Action items: {email.action_items.join("; ")}</span> : null}
                                </div>
                              </button>
                              <div className="email-option-actions">
                                {!email.summary && <button type="button" disabled={busy} onClick={() => void submitMessage("Analyze this email", undefined, email.id)}>Review email</button>}
                                <button type="button" disabled={busy} onClick={() => void submitMessage("Analyze this email and create eligible tasks", undefined, email.id)}>Create eligible task</button>
                              </div>
                            </article>
                          ))}
                        </div>
                      ) : null}
                      <time className="message-time" dateTime={message.time.toISOString()}>{message.time.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</time>
                    </div>
                  </article>
                ))}
                {busy && <div className="message-row assistant"><div className="message-avatar"><Sparkles size={15} /></div><div className="message-content"><div className="message-bubble loading-bubble"><LoaderCircle size={16} className="spin" /> Checking your request…</div></div></div>}
              </div>
            )}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            {error && <div className="inline-error" role="status">{error}</div>}
            <div className="composer-box">
              <textarea
                ref={inputRef}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={handleKeyDown}
                maxLength={4000}
                placeholder="Message your Email Agent…"
                aria-label="Message your Email Agent"
                rows={1}
              />
              <button className="send-button" type="submit" disabled={busy || !draft.trim()} aria-label="Send message" title="Send message">
                {busy ? <LoaderCircle size={17} className="spin" /> : <ArrowUp size={18} />}
              </button>
            </div>
            <div className="composer-foot"><span>Enter to send · Shift + Enter for a new line</span><span>{draft.length}/4000</span></div>
          </form>
        </section>
        <p className="privacy-note"><ShieldCheck size={14} /> Chat requests and short email excerpts for AI reviews are sent to Gemini. Your mailbox stays with your Google account.</p>
        </> : <section className="data-page">
          <div className="data-page-heading">
            <div><div className="eyebrow"><span className="eyebrow-dot" /> PERSONAL WORKSPACE</div><h1>{view === "inbox" ? "Your inbox" : view === "tasks" ? "Your tasks" : "Your meetings"}</h1><p>{view === "inbox" ? "Browse messages and ask the agent to review any email." : view === "tasks" ? "Follow up on the work you have captured from email." : "See upcoming events from your connected calendar."}</p></div>
            <button className="refresh-button" type="button" onClick={() => void loadWorkspace()} disabled={workspaceLoading}><RefreshCw size={15} className={workspaceLoading ? "spin" : ""} /> Refresh</button>
          </div>
          {view === "inbox" && <label className="inbox-search"><Search size={17} /><input value={inboxQuery} onChange={(event) => setInboxQuery(event.target.value)} placeholder="Filter loaded emails by sender or subject" aria-label="Filter loaded emails" />{inboxQuery && <button type="button" onClick={() => setInboxQuery("")} aria-label="Clear search"><X size={15} /></button>}</label>}
          {workspaceError && <div className="page-error" role="status">{workspaceError}<button type="button" onClick={() => void loadWorkspace()}>Try again</button></div>}
          {workspaceLoading ? <div className="page-empty"><LoaderCircle className="spin" size={20} /> Loading {pageTitle.toLowerCase()}…</div> : !workspaceError && view === "inbox" && (() => {
            const emails = (workspaceItems as MailboxEmail[]).filter((email) => `${email.sender} ${email.subject}`.toLocaleLowerCase().includes(inboxQuery.trim().toLocaleLowerCase()));
            return emails.length ? <div className="workspace-list">{emails.map((email) => <article className="workspace-row" key={email.id}>
              <button className="workspace-row-main" type="button" onClick={() => void openEmail(email.id)}><span className={`mail-status ${email.is_read ? "read" : "unread"}`} /><span className="workspace-row-copy"><strong>{email.subject || "(No subject)"}</strong><span>{email.sender} · {email.received_at ? new Date(email.received_at).toLocaleString() : "Date unavailable"}</span></span><ArrowRight size={16} /></button>
              <button className="row-agent-action" type="button" onClick={() => askAgentAbout(email)} title="Ask the Email Agent to review this email"><Sparkles size={15} /><span>Ask agent</span></button>
            </article>)}</div> : <div className="page-empty"><Inbox size={22} /><strong>{inboxQuery ? "No loaded emails match that filter" : "No emails to show"}</strong><span>{inboxQuery ? "Try a different sender or subject." : "Refresh or check your email connection."}</span></div>;
          })()}
          {!workspaceLoading && !workspaceError && view === "tasks" && (() => {
            const tasks = workspaceItems as TaskItem[];
            return tasks.length ? <div className="workspace-list">{tasks.map((task) => <article className="task-row" key={task.id}><span className={`task-state ${task.status === "completed" ? "done" : ""}`}>{task.status === "completed" ? <Check size={14} /> : <ListTodo size={15} />}</span><div className="workspace-row-copy"><strong>{task.title}</strong><span>{task.description}</span></div><span className={`task-priority ${task.priority.toLowerCase()}`}>{task.priority}</span></article>)}</div> : <div className="page-empty"><ListTodo size={22} /><strong>No tasks yet</strong><span>Review an email in chat and create a task when it has an actionable follow-up.</span><button className="primary-button" type="button" onClick={() => setView("assistant")}><Sparkles size={15} /> Open Email Agent</button></div>;
          })()}
          {!workspaceLoading && !workspaceError && view === "meetings" && (() => {
            const meetings = workspaceItems as MeetingItem[];
            return meetings.length ? <div className="workspace-list">{meetings.map((meeting) => <article className="meeting-row" key={meeting.id}><div className="meeting-date"><CalendarDays size={17} /><span>{meeting.all_day ? "All day" : new Date(meeting.start).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</span></div><div className="workspace-row-copy"><strong>{meeting.title}</strong><span>{new Date(meeting.start).toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" })}{meeting.location ? ` · ${meeting.location}` : ""}</span></div>{meeting.url && <a className="row-agent-action" href={meeting.url} target="_blank" rel="noreferrer">Open event <ArrowRight size={14} /></a>}</article>)}</div> : <div className="page-empty"><CalendarDays size={22} /><strong>No upcoming meetings</strong><span>There are no events in the calendar window currently loaded.</span></div>;
          })()}
        </section>}
      </main>

      {modalOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setModalOpen(false); }}>
        <section className="filter-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div className="modal-head"><div><span className="modal-kicker">PERSONALIZE YOUR WORKSPACE</span><h2 id="modal-title">Create a chat filter</h2></div><button className="icon-button" type="button" onClick={() => setModalOpen(false)} aria-label="Close"><X size={18} /></button></div>
          <p className="modal-copy">Save a shortcut for an instruction you often send to your Email Agent. It is stored in this browser on this computer and can use the Email Agent’s supported actions.</p>
          <form onSubmit={addFilter}>
            <label htmlFor="filter-name">Filter name</label>
            <input id="filter-name" value={filterName} onChange={(event) => setFilterName(event.target.value)} maxLength={48} placeholder="For example, Follow up today" required autoFocus />
            <label htmlFor="filter-prompt">Instruction for the Email Agent</label>
            <textarea id="filter-prompt" value={filterPrompt} onChange={(event) => setFilterPrompt(event.target.value)} maxLength={500} placeholder="For example, Find emails from my manager that need a reply" rows={4} required />
            <div className="modal-actions"><span>{customFilters.length}/12 saved filters</span><button className="primary-button" type="submit" disabled={!filterName.trim() || !filterPrompt.trim() || customFilters.length >= 12}><Check size={16} /> Save filter</button></div>
          </form>
        </section>
      </div>}

      {openedEmail && <div className="modal-backdrop email-detail-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setOpenedEmail(null); }}>
        <section className="email-detail-modal" role="dialog" aria-modal="true" aria-labelledby="email-detail-title">
          <div className="email-detail-head">
            <div><span className="modal-kicker">FULL EMAIL</span><h2 id="email-detail-title">{openedEmail.email?.subject || "Email"}</h2></div>
            <button className="icon-button" type="button" onClick={() => setOpenedEmail(null)} aria-label="Close email"><X size={18} /></button>
          </div>
          {openedEmail.loading ? <p className="email-detail-status">Loading email…</p> : openedEmail.error ? <p className="email-detail-status email-detail-error">{openedEmail.error}</p> : openedEmail.email && <>
            <div className="email-detail-meta"><span><strong>From:</strong> {openedEmail.email.sender}</span><span><strong>To:</strong> {openedEmail.email.receiver}</span>{openedEmail.email.received_at && <time>{new Date(openedEmail.email.received_at).toLocaleString()}</time>}</div>
            <div className="email-detail-body">{openedEmail.email.body || "(This email has no readable text body.)"}</div>
          </>}
        </section>
      </div>}
      </div>
    </div>
  );
}

export default App;
