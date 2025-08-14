import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

export async function sendMessage(query) {
  try {
    const response = await axios.post(`${API_URL}/chat`, null, {
      params: { query }
    });
    return response.data;
  } catch (error) {
    console.error("Eroare la API:", error);
    return { recommendation: "Eroare la server.", full_summary: "" };
  }
}
