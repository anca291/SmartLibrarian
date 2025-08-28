export default function Message({ sender, text }) {

  const isLoading = text.includes("Bot is thinking...");
  return (
    <div className={`message ${sender} ${isLoading ? "loading" : ""}`}>
      <div className="bubble">{text}</div>
    </div>
  );
}
