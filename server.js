const express = require('express');
const axios = require('axios');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

const OPENAI_KEY = process.env.OPENAI_API_KEY;
if (!OPENAI_KEY) {
  console.warn('Warning: OPENAI_API_KEY is not set. The /api/chat endpoint will fail without it.');
}

app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body;
    if (!message) return res.status(400).json({ error: 'Missing message in request body' });

    if (!OPENAI_KEY) return res.status(500).json({ error: 'Server missing OpenAI API key. Set OPENAI_API_KEY in environment.' });

    const resp = await axios.post(
      'https://api.openai.com/v1/chat/completions',
      {
        model: 'gpt-3.5-turbo',
        messages: [
          { role: 'system', content: 'You are Armin.ai — a helpful assistant.' },
          { role: 'user', content: message }
        ],
        max_tokens: 500,
        temperature: 0.7
      },
      {
        headers: {
          'Authorization': `Bearer ${OPENAI_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );

    const reply = resp.data.choices && resp.data.choices[0] && resp.data.choices[0].message && resp.data.choices[0].message.content
      ? resp.data.choices[0].message.content.trim()
      : 'Sorry, I could not generate a reply.';

    res.json({ reply });
  } catch (err) {
    console.error('Error in /api/chat:', err?.response?.data || err.message || err);
    const detail = err?.response?.data || err.message || String(err);
    res.status(500).json({ error: 'OpenAI request failed', detail });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
