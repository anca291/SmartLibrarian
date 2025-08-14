import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import InputBox from "./components/InputBox";
import { sendMessage } from "./services/api";
import "./styles/main.css";

export default function App() {
  const [messages, setMessages] = useState([]);

  const handleSend = async (userMessage) => {
    setMessages((prev) => [...prev, { sender: "user", text: userMessage }]);

    const botResponse = await sendMessage(userMessage);

    const fullText = `${botResponse.recommendation}\n\nRezumat complet:\n${botResponse.full_summary}`;
    setMessages((prev) => [...prev, { sender: "bot", text: fullText }]);
  };

  return (
    <div className="app">
      <h1>Smart Librarian</h1>
      <ChatWindow messages={messages} />
      <InputBox onSend={handleSend} />
    </div>
  );
}
