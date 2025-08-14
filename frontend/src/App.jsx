import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import "./styles/main.css";

export default function App() {
  const [messages, setMessages] = useState([]);

  const handleSend = (userMessage) => {
    if (!userMessage?.trim()) return;
    setMessages((prev) => [...prev, { sender: "user", text: userMessage }]);

    // Simulare răspuns bot
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Eroare la server. Rezumat complet:" }
      ]);
    }, 500);
  };

  return (
    <div className="app">
      {/* Monitorul cu chat */}
      <ChatWindow messages={messages} onSend={handleSend} />

      {/* Biroul */}
      <div className="desk" />

      {/* Tastatura și mouse-ul */}
      <div className="peripherals">
        <div className="keyboard" />
        <div className="mouse">
          <span className="cable" />
        </div>
      </div>
    </div>
  );
}
