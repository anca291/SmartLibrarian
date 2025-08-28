import { useState } from "react";
import Message from "./Message";
import BotMessage from "./BotMessage";
import { sttUploadAudio } from "../services/api";
import { useRef } from "react";

export default function ChatWindow({ messages, onSend }) {
  const [draft, setDraft] = useState("");
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRec = async () => {
    if (recording) return;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
    chunksRef.current = [];
    mr.ondataavailable = e => e.data.size && chunksRef.current.push(e.data);
    mr.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      try {
        const { text } = await sttUploadAudio(blob, "ro");
        setDraft((prev) => (prev ? (prev + " " + text) : text));
      } catch (e) {
        console.error("STT error:", e);

      }
    };
    mr.start();
    mediaRecorderRef.current = mr;
    setRecording(true);
  };


  const stopRec = () => {
    if (!recording) return;
    mediaRecorderRef.current.stop();
    mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
    setRecording(false);
  };
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
              msg.sender === "bot" ? (
                <BotMessage key={index} message={msg.text} />
              ) : (
                <Message key={index} sender={msg.sender} text={msg.text} />
              )
            ))}
          </div>

        <form className="screen-input" onSubmit={submit}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Write here..."
        />
        <button type="button" onClick={recording ? stopRec : startRec}
                title={recording ? "Stop recording" : "Recording"}>
          {recording ? "⏺️ Stop" : "🎙️ Voice"}
        </button>
        <button type="submit">Send</button>
      </form>
        </div>
      </div>

      <div className="monitor-stand" />

    </div>
  );
}
