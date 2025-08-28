import axios from 'axios';

export const sendMessageToBackend = async (message) => {
  try {
    const response = await axios.post(
      'http://127.0.0.1:8000/chat',
      { query: message }
    );
    return response.data;
  } catch (error) {
    if (error.response) {
      console.error(`[BACKEND ERROR]`, error.response.data);
    } else if (error.request) {
      console.error(`[NO RESPONSE]`, error.request);
    } else {
      console.error(`[AXIOS ERROR]`, error.message);
    }
    throw error;
  }
};

export async function sttUploadAudio(blob, language) {
  const form = new FormData();
  form.append("file", new File([blob], "speech.webm", { type: "audio/webm" }));
  if (language) form.append("language", language);
  const res = await fetch("/audio/stt", { method: "POST", body: form });
  if (!res.ok) throw new Error("STT request failed");
  return res.json(); // { text }
}

export async function ttsFetchAudio(text, { voice = "alloy", format = "mp3" } = {}) {
  const form = new FormData();
  form.append("text", text);
  form.append("voice", voice);
  form.append("format", format);
  const res = await fetch("/audio/tts", { method: "POST", body: form });
  if (!res.ok) throw new Error("TTS request failed");
  const buf = await res.arrayBuffer();
  return new Blob([buf], { type: format === "mp3" ? "audio/mpeg" : `audio/${format}` });
}

export async function generateImage(prompt, { size = "1024x1024" } = {}) {
  const form = new FormData();
  form.append("prompt", prompt);
  form.append("size", size);
  const res = await fetch("/images/generate", { method: "POST", body: form });
  if (!res.ok) throw new Error("Image generation failed");
  const blob = await res.blob(); // image/png
  return URL.createObjectURL(blob);
}