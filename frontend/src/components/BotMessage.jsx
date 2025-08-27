
import React, { useEffect, useRef, useState } from 'react';
import { ttsFetchAudio, generateImage } from '../services/api';

export default function BotMessage({ message }) {
  const [loadingTTS, setLoadingTTS] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const audioRef = useRef(null);
  const urlRef = useRef(null);

  const [imgUrl, setImgUrl] = useState(null);
  const [imgLoading, setImgLoading] = useState(false);

  const stopAndCleanup = () => {
    const a = audioRef.current;
    if (a) {
      a.pause();
      a.currentTime = 0;
      a.removeAttribute('src');
      a.load();
    }
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
    setAudioUrl(null);
  };

  useEffect(() => () => stopAndCleanup(), []);

  useEffect(() => {
    const a = audioRef.current;
    if (!a || !audioUrl) return;

    let cancelled = false;
    const onCanPlay = async () => {
      if (cancelled) return;
      try { await a.play(); } catch (err) { console.warn('[UI] play() failed', err); }
    };
    const onError = () => console.error('[UI] <audio> error:', a?.error);

    a.addEventListener('canplaythrough', onCanPlay, { once: true });
    a.addEventListener('error', onError, { once: true });
    a.load();

    return () => {
      cancelled = true;
      a.removeEventListener('canplaythrough', onCanPlay);
      a.removeEventListener('error', onError);
    };
  }, [audioUrl]);

  const handleServerTTS = async () => {
    if (loadingTTS) return;
    setLoadingTTS(true);
    try {
      stopAndCleanup();
      const blob = await ttsFetchAudio(message, { voice: 'alloy', format: 'mp3' });
      const url = URL.createObjectURL(blob);
      urlRef.current = url;
      setAudioUrl(url);
    } catch (e) {
      console.error('Server TTS error:', e);
    } finally {
      setLoadingTTS(false);
    }
  };

 const handleGenerateImage = async () => {
    if (imgLoading) return;
    setImgLoading(true);
    try {
      // Prompt simplu: “copertă/temă/cheie vizuală” folosind textul recomandării
      const prompt = `Copertă ilustrată, stil modern, fără text, pentru cartea recomandată: ${message}.
      Include elemente-cheie ale temei, culori coerente și compoziție clară.`;
      const url = await generateImage(prompt, { size: "1024x1024" });
      setImgUrl(url);
    } catch (e) {
      console.error('Image generation error:', e);
    } finally {
      setImgLoading(false);
    }
  };

  return (
    <div className="bot-message" style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
      <p style={{ marginRight: '0.5rem' }}>{message}</p>
      {/* DOAR server TTS */}
      <button onClick={handleServerTTS} disabled={loadingTTS}
              title={loadingTTS ? "Se generează audio..." : "Redă cu voce de server"}
              style={{ cursor:'pointer', border:'none', background:'none', fontSize:'18px' }}>
        🎧
      </button>

      <button onClick={handleGenerateImage} disabled={imgLoading}
                title={imgLoading ? "Se generează imaginea..." : "Generează imagine"}
                style={{ cursor:'pointer', border:'none', background:'none', fontSize:'18px' }}>
          🖼️
        </button>

      <audio ref={audioRef} src={audioUrl || undefined} onEnded={stopAndCleanup} />
       {/* Rând de încărcare pentru imagine */}
     {imgLoading && (
      <div className="image-loading-row" role="status" aria-live="polite">
          <div className="image-spinner" />
          <span>Se generează imaginea…</span>
        </div>
      )}

      {imgUrl && (
        <div style={{ marginTop: '0.25rem' }}>
          <img
            src={imgUrl}
            alt="Imagine generată pentru carte"
            style={{ maxWidth:'100%', borderRadius: 12 }}
            onLoad={() => setImgLoading(false)}   // ascunde spinnerul când e gata
            onError={() => setImgLoading(false)}  // ascunde și pe eroare
          />
        </div>
      )}



    </div>
  );
}
