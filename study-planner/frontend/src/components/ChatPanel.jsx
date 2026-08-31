import { useState, useRef, useEffect } from "react";
import { api } from "../api";

const STARTER_PROMPTS = [
  "I fell behind, what should I do?",
  "Explain spaced repetition",
  "Give me a Pomodoro tip",
];

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "I'm your study coach. Ask me about your schedule, study techniques, or say the word if you've fallen behind.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const send = async (text) => {
    const msg = text ?? input;
    if (!msg.trim() || sending) return;
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setInput("");
    setSending(true);
    try {
      const res = await api.chat(msg);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't reach the coach service just now." },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span className="chat-dot" />
        <h3>Study coach</h3>
      </div>
      <div className="chat-messages" ref={listRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            {m.content}
          </div>
        ))}
        {sending && <div className="chat-msg assistant typing">thinking…</div>}
      </div>
      <div className="chat-prompts">
        {STARTER_PROMPTS.map((p) => (
          <button key={p} className="chip" onClick={() => send(p)} disabled={sending}>
            {p}
          </button>
        ))}
      </div>
      <form
        className="chat-input-row"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <input
          type="text"
          placeholder="Ask your coach anything…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" disabled={sending || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
