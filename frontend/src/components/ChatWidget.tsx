import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { ChatMessage, ChatSession } from "../types";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadSessions = useCallback(async () => {
    try {
      const { data } = await api.get<ChatSession[]>("/chat/sessions");
      setSessions(data);
      if (!activeId && data.length > 0) setActiveId(data[0].id);
    } catch {
      /* ignore */
    }
  }, [activeId]);

  const loadMessages = useCallback(async (sessionId: number) => {
    const { data } = await api.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
    setMessages(data);
  }, []);

  useEffect(() => {
    if (open) loadSessions();
  }, [open, loadSessions]);

  useEffect(() => {
    if (activeId) loadMessages(activeId);
  }, [activeId, loadMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function ensureSession(): Promise<number> {
    if (activeId) return activeId;
    const { data } = await api.post<ChatSession>("/chat/sessions");
    setSessions((s) => [data, ...s]);
    setActiveId(data.id);
    return data.id;
  }

  async function send() {
    if (!input.trim() || loading) return;
    setLoading(true);
    const text = input.trim();
    setInput("");
    try {
      const sid = await ensureSession();
      const { data } = await api.post<{ user_message: ChatMessage; assistant_message: ChatMessage }>(
        `/chat/sessions/${sid}/messages`,
        { content: text }
      );
      setMessages((m) => [...m, data.user_message, data.assistant_message]);
      loadSessions();
    } finally {
      setLoading(false);
    }
  }

  async function newChat() {
    const { data } = await api.post<ChatSession>("/chat/sessions");
    setSessions((s) => [data, ...s]);
    setActiveId(data.id);
    setMessages([]);
    setShowHistory(false);
  }

  return (
    <>
      <button type="button" className="chat-fab" onClick={() => setOpen(true)} title="Chat with coach">
        ✦
      </button>

      {open && (
        <div className="chat-overlay" onClick={() => setOpen(false)}>
          <div className="chat-drawer" onClick={(e) => e.stopPropagation()}>
            <header className="chat-header">
              <div>
                <p className="eyebrow">Finance coach</p>
                <h3>AiFin Agent</h3>
              </div>
              <div className="chat-header-actions">
                <button type="button" className="icon-btn" onClick={() => setShowHistory(!showHistory)}>
                  ☰
                </button>
                <button type="button" className="icon-btn" onClick={newChat}>
                  +
                </button>
                <button type="button" className="icon-btn" onClick={() => setOpen(false)}>
                  ×
                </button>
              </div>
            </header>

            <div className="chat-body">
              {showHistory && (
                <aside className="chat-history">
                  <p className="eyebrow">Previous chats</p>
                  {sessions.length === 0 && <p className="muted">No conversations yet.</p>}
                  {sessions.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      className={`history-item ${activeId === s.id ? "active" : ""}`}
                      onClick={() => {
                        setActiveId(s.id);
                        setShowHistory(false);
                      }}
                    >
                      <span>{s.title}</span>
                      <small>{new Date(s.updated_at).toLocaleDateString()}</small>
                    </button>
                  ))}
                </aside>
              )}

              <div className="chat-messages">
                {messages.length === 0 && (
                  <p className="chat-empty">
                    Free local finance coach — ask about debt, SIP, emergency fund, strategy, or goals.
                  </p>
                )}
                {messages.map((m) => (
                  <div key={m.id} className={`chat-bubble ${m.role}`}>
                    {m.content}
                  </div>
                ))}
                {loading && <div className="chat-bubble assistant typing">Thinking…</div>}
                <div ref={bottomRef} />
              </div>
            </div>

            <footer className="chat-input-row">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your finances…"
                onKeyDown={(e) => e.key === "Enter" && send()}
              />
              <button type="button" className="btn-primary sm" onClick={send} disabled={loading}>
                Send
              </button>
            </footer>
          </div>
        </div>
      )}
    </>
  );
}
