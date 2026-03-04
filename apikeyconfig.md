# API Key Configuration

This guide explains how to obtain and configure API keys so that Claude, ChatGPT, and Gemini models appear in the OpenBeavs model selector.

All keys go in `front/.env`. Restart the backend after any changes.

---

## Anthropic (Claude)

### 1. Get Your API Key
1. Go to [console.anthropic.com](https://console.anthropic.com) and sign in.
2. In the left sidebar, click **API Keys**.
3. Click **Create Key**, give it a name (e.g. `openbeavs-local`), and click **Create API Key**.
4. Copy the key — it starts with `sk-ant-`. **You will not be able to see it again after closing the dialog.**

### 2. Add to `front/.env`
```
ANTHROPIC_API_KEY='sk-ant-YOUR_KEY_HERE'
ENABLE_ANTHROPIC_API='True'
```

### 3. Models Available
- Claude Opus 4.6
- Claude Sonnet 4.6
- Claude Haiku 4.5
- Claude 3.5 Sonnet
- Claude 3.5 Haiku

---

## OpenAI (ChatGPT)

### 1. Get Your API Key
1. Go to [platform.openai.com](https://platform.openai.com) and sign in.
2. In the left sidebar, click **API keys**.
3. Click **Create new secret key**, give it a name, and click **Create secret key**.
4. Copy the key — it starts with `sk-`. **You will not be able to see it again after closing the dialog.**

### 2. Add to `front/.env`
```
CHATGPT_API_KEY='sk-YOUR_KEY_HERE'
ENABLE_CHATGPT_API='True'
```

### 3. Models Available
- GPT-5.2 Thinking
- GPT-5.2 Instant
- GPT-5.2 Pro
- GPT-4o
- GPT-4o mini

---

## Google (Gemini)

### 1. Get Your API Key
1. Go to [aistudio.google.com](https://aistudio.google.com) and sign in with your Google account.
2. Click **Get API key** in the left sidebar.
3. Click **Create API key**, select a Google Cloud project, and click **Create API key in existing project**.
4. Copy the key — it starts with `AIza`.

### 2. Add to `front/.env`
```
GEMINI_CHAT_API_KEY='AIza-YOUR_KEY_HERE'
ENABLE_GEMINI_CHAT_API='True'
```

### 3. Models Available
- Gemini 2.5 Pro
- Gemini 2.5 Flash
- Gemini 2.0 Flash
- Gemini 2.0 Flash-Lite
- Gemini 1.5 Pro
- Gemini 1.5 Flash

---

## Notes

- If a key is left empty, that provider's models will not appear in the selector — no error is shown, they are simply hidden.
- Keys are stored in `front/.env` which is gitignored and never committed to the repository.
- A full backend restart is required after changing any key.

```bash
conda run -n open-webui bash dev.sh
```

Note: I (Long Tran) has the api keys for Claude and GPT for testing purpose, but since the key got revoked multiple times
since I leave it here in plain text, I didn't include it here anymore.
If you need the API keys, email or message me on Discord.
