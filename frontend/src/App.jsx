import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import { sendMessageToBackend } from "./services/api";
import "./styles/main.css";

export default function App() {
  const [messages, setMessages] = useState([]);

const handleSend = async (userMessage) => {
  if (!userMessage?.trim()) return;

  console.log("[FRONTEND] User trimite mesaj:", userMessage);

  // Adaugă mesajul userului
  setMessages((prev) => [...prev, { sender: "user", text: userMessage }]);

  // Adaugă mesaj temporar "Botul scrie..."
  const loadingMessage = { sender: "bot", text: "🤖 Botul scrie..." };
  setMessages((prev) => [...prev, loadingMessage]);

  try {
    console.log("[FRONTEND] Trimit request către backend...");
    const botResponse = await sendMessageToBackend(userMessage);
    console.log("[FRONTEND] Am primit răspunsul de la backend:", botResponse);

    const fullText = `${botResponse.recommendation}\n\nRezumat complet:\n${botResponse.full_summary}`;

    setMessages((prev) => [
      ...prev.slice(0, -1), // scoatem mesajul loading
      { sender: "bot", text: fullText }
    ]);
  } catch (error) {
    console.error("[FRONTEND] Eroare la request:", error);
    setMessages((prev) => [
      ...prev.slice(0, -1),
      { sender: "bot", text: "❌ Eroare la server. Încearcă din nou." }
    ]);
  }
};
  return (
    <div className="app">
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
