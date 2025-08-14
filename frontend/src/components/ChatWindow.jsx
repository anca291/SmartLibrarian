import { useState } from "react";
import Message from "./Message";

export default function ChatWindow({ messages, onSend }) {
  const [draft, setDraft] = useState("");

  const submit = (e) => {
    e.preventDefault();
    const v = draft.trim();
    if (!v) return;
    onSend(v);
    setDraft("");
  };

  return (
    <div className="monitor">
      <div className="monitor-title">smart librarian</div>

      <div className="bezel">
        <div className="screen">
          <div className="messages-container">
            {messages.length === 0 && (
              <div className="chat-placeholder">
                Start your conversation...
              </div>
            )}
            {messages.map((msg, index) => (
              <Message key={index} sender={msg.sender} text={msg.text} />
            ))}
          </div>

          <form className="screen-input" onSubmit={submit}>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Scrie Întrebarea ta..."
            />
            <button type="submit">Trimite</button>
          </form>
        </div>
      </div>

      <div className="monitor-stand" />
    </div>
  );
}
