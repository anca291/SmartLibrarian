import React, { useState } from 'react';

export default function BotMessage({ message }) {
  const [isSpeaking, setIsSpeaking] = useState(false);

  const handleSpeak = () => {
    if (isSpeaking) return;
    const utterance = new SpeechSynthesisUtterance(message);
    setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
    };
    window.speechSynthesis.speak(utterance);
  };

  const handleStop = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  return (
    <div className="bot-message" style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
      <p style={{ marginRight: '0.5rem' }}>{message}</p>
      <button onClick={handleSpeak} title="Read text" style={{ cursor: 'pointer', border: 'none', background: 'none', fontSize: '18px', color: '#007bff', marginRight: '0.5rem' }}>
        🔊
      </button>
      {isSpeaking && (
        <button onClick={handleStop} title="Stop reading" style={{ cursor: 'pointer', border: 'none', background: 'none', fontSize: '18px', color: '#dc3545' }}>
          ⏹️
        </button>
      )}
    </div>
  );
}