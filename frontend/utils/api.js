export async function sendMessageToBackend(text, model = 'open_llama') {
  try {
    const res = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        model: model,
        session_id: 'default' // Optional: UUID or session tracking logic
      })
    });

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();
    console.log('API Response:', data); // Debug log
    return { response: data.response || '⚠️ No response from backend' };
  } catch (error) {
    console.error('API Error:', error);
    return { response: '⚠️ Error connecting to backend' };
  }
}