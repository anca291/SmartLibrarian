import Message from "./Message";

  export default function ChatWindow({ messages, onSend }) {
    return (
      <div className="chat-window">
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
        <div className="input-box">
          {/* Your input and button here */}
        </div>
      </div>
    );
  }