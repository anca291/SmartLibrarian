import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import { sendMessageToBackend } from "./services/api";
import "./styles/main.css";

export default function App() {
  const [messages, setMessages] = useState([]);

  const handleSend = async (userMessage) => {
    if (!userMessage?.trim()) return;


    setMessages((prev) => [...prev, { sender: "user", text: userMessage }]);

    const loadingMessage = { sender: "bot", text: "🤖 Bot is typing..." };
    setMessages((prev) => [...prev, loadingMessage]);

    try {
      const { recommendation, full_summary } = await sendMessageToBackend(userMessage);
      const fullText = `${recommendation}${full_summary ? `\n\nSummary:\n${full_summary}` : ""}`;

      setMessages((prev) => [...prev.slice(0, -1), { sender: "bot", text: fullText }]);
    } catch (error) {
      console.error("[FRONTEND] Error:", error);
      setMessages((prev) => [...prev.slice(0, -1), { sender: "bot", text: "❌ Server error. Please try again." }]);
    }
  };

  return (
    <div className="app">
      <ChatWindow messages={messages} onSend={handleSend} />
      <div className="desk" />
      <div className="peripherals">
        <div className="keyboard" />
        <div className="mouse">
          <span className="cable" />
        </div>
      </div>
    </div>
  );
}