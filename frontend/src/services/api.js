import axios from 'axios';

export const sendMessageToBackend = async (message) => {
  try {
    const response = await axios.post(
      'http://127.0.0.1:8000/chat?query=' + encodeURIComponent(message)
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