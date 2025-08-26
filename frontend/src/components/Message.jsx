export default function Message({ sender, text }) {
  // dacă textul este "Botul scrie..." => adaugă clasa "loading"
  const isLoading = text.includes("Botul scrie...");
  return (
    <div className={`message ${sender} ${isLoading ? "loading" : ""}`}>
      <div className="bubble">{text}</div>
    </div>
  );
}
