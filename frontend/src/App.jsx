import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import { sendMessageToBackend } from "./services/api";
import "./styles/main.css";

export default function App() {
  const [messages, setMessages] = useState([]);

  const handleSend = async (userMessage) => {
    if (!userMessage?.trim()) return;

    console.log("[FRONTEND] User sends message:", userMessage);

    // Add user's message
    setMessages((prev) => [...prev, { sender: "user", text: userMessage }]);

    // Add temporary loading message "Bot is typing..."
    const loadingMessage = { sender: "bot", text: "🤖 Bot is typing..." };
    setMessages((prev) => [...prev, loadingMessage]);

    try {
      console.log("[FRONTEND] Sending request to backend...");
      const botResponse = await sendMessageToBackend(userMessage);
      console.log("[FRONTEND] Received response from backend:", botResponse);

    let fullText = botResponse.recommendation;
      if (botResponse.full_summary) {
        fullText += `\n\nRezumat complet:\n${botResponse.full_summary}`;
      }

      setMessages((prev) => [
        ...prev.slice(0, -1),
        { sender: "bot", text: fullText }
      ]);
    } catch (error) {
      console.error("[FRONTEND] Error sending request:", error);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { sender: "bot", text: "❌ Server error. Please try again." }
      ]);
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