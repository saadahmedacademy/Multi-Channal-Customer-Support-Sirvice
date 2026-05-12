# 🤗 Hugging Face AI Integration Guide

## **Overview**

Your AI Customer Support Agent now supports **Hugging Face Inference API** as an AI provider option!

**Priority Order**:
1. OpenRouter (primary)
2. **Hugging Face** (fallback 1) ✨ NEW
3. Google Gemini (fallback 2)

---

## **1️⃣ GET HUGGING FACE API KEY**

### **Step 1: Create Account**
1. Visit: **https://huggingface.co**
2. Click **"Sign Up"** (free account)
3. Verify your email

### **Step 2: Get API Token**
1. Go to: **https://huggingface.co/settings/tokens**
2. Click **"New token"**
3. Name it: `customer-support-agent`
4. Type: **Read** (default)
5. Click **"Generate"**
6. Copy the token (starts with `hf_`)

**Free Tier Limits**:
- ✅ 30,000 tokens/month (generous for testing)
- ✅ Access to 100,000+ models
- ✅ No credit card required

---

## **2️⃣ CHOOSE A MODEL**

### **Recommended Models** (Free Tier Compatible):

| Model | Quality | Speed | Best For |
|-------|---------|-------|----------|
| **mistralai/Mixtral-8x7B-Instruct-v0.1** | ⭐⭐⭐⭐⭐ | Medium | General support (DEFAULT) |
| **meta-llama/Meta-Llama-3-8B-Instruct** | ⭐⭐⭐⭐ | Fast | Quick responses |
| **HuggingFaceH4/zephyr-7b-beta** | ⭐⭐⭐⭐ | Fast | Conversational |
| **microsoft/Phi-3-mini-4k-instruct** | ⭐⭐⭐ | Very Fast | Simple queries |

### **Model Selection Criteria**:
- ✅ **Instruct** or **Chat** models (not base models)
- ✅ Under 10B parameters (for free tier speed)
- ✅ Good at following instructions
- ✅ English language support

---

## **3️⃣ CONFIGURE YOUR PROJECT**

### **Step 1: Update .env File**

```bash
cd /home/saadahmed/hk-5
cp .env.example .env
```

Edit `.env`:
```bash
# Hugging Face (Free AI Alternative)
HUGGINGFACE_API_KEY=hf_your-actual-token-here
HUGGINGFACE_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1

# Optional: Disable other AI providers (to test Hugging Face only)
# OPENROUTER_API_KEY=
# GEMINI_API_KEY=
```

### **Step 2: Verify Configuration**

```bash
# Check if Hugging Face is configured
python -c "
from backend.config.settings import settings
print(f'Hugging Face API Key: {settings.huggingface_api_key[:10]}...' if settings.huggingface_api_key else 'NOT CONFIGURED')
print(f'Model: {settings.huggingface_model}')
"
```

---

## **4️⃣ TEST HUGGING FACE INTEGRATION**

### **Test 1: Direct API Call**

```bash
# Test Hugging Face API directly
curl -X POST "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1" \
  -H "Authorization: Bearer hf_your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "<<SYS>>\nYou are a helpful assistant.\n<</SYS>>\n\n[INST] Hello, how are you? [/INST]",
    "parameters": {
      "max_new_tokens": 100,
      "temperature": 0.7,
      "return_full_text": false
    }
  }'
```

**Expected Response**:
```json
[
  {
    "generated_text": "Hello! I'm doing well, thank you for asking. How can I help you today?"
  }
]
```

### **Test 2: Through Your Backend**

```bash
# Start your backend
cd /home/saadahmed/hk-5/backend
source ../.venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Submit a test web form request
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "subject": "Hugging Face Test",
    "category": "general",
    "priority": "medium",
    "message": "Hello, this is a test of Hugging Face integration"
  }'
```

**Check Worker Logs**:
```bash
python backend/worker/message_processor.py

# You should see:
# INFO: Hugging Face response generated (~150 tokens)
```

---

## **5️⃣ USE HUGGING FACE AS PRIMARY AI**

If you want to use **only Hugging Face** (no OpenRouter/Gemini):

### **Option A: Comment Out Other Keys**

In `.env`:
```bash
# Leave these empty or commented
OPENROUTER_API_KEY=
GEMINI_API_KEY=

# Only configure Hugging Face
HUGGINGFACE_API_KEY=hf_your-token
HUGGINGFACE_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
```

### **Option B: Change Priority in Code**

Edit `backend/worker/ai_agent.py`:

```python
async def generate_response(self, ...):
    # ...
    try:
        # Try Hugging Face FIRST
        if self.huggingface_api_key:
            response, tokens = await self._call_huggingface(messages)
            if response:
                return response, tokens, 0.85

        # Then OpenRouter
        if self.openrouter_api_key:
            response, tokens = await self._call_openrouter(messages)
            if response:
                return response, tokens, 0.9

        # Then Gemini
        if self.gemini_api_key:
            response, tokens = await self._call_gemini(message, conversation_history)
            if response:
                return response, tokens, 0.8

        # Fallback
        return self._get_fallback_response(channel), 0, None
```

---

## **6️⃣ TROUBLESHOOTING**

### **Issue 1: "Model is loading" (503 Error)**

**Symptom**: First request returns 503 with "Model is loading"

**Solution**:
- ✅ **Automatic retry** is already implemented (waits 30 seconds)
- Wait 1-2 minutes for model to load
- Try again

**Alternative**: Use a smaller, faster-loading model:
```bash
HUGGINGFACE_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
```

### **Issue 2: "Invalid token" (401 Error)**

**Check**:
```bash
# Verify your token
curl -H "Authorization: Bearer hf_your-token" \
  https://huggingface.co/api/whoami

# Should return: {"name": "your-username", ...}
```

**Solution**:
- Ensure token starts with `hf_`
- No extra spaces in `.env` file
- Token has "Read" permission

### **Issue 3: Response includes prompt text**

**Symptom**: AI response repeats the user's message

**Solution**: Already handled in code:
```python
# Clean up response (remove prompt if included)
content = content.strip()
if content.startswith(prompt[-50:]):
    content = content[len(prompt):].strip()
```

### **Issue 4: Slow responses (>30 seconds)**

**Cause**: Large model or server load

**Solutions**:
1. Use smaller model:
   ```bash
   HUGGINGFACE_MODEL=microsoft/Phi-3-mini-4k-instruct
   ```

2. Increase timeout in `.env`:
   ```bash
   AI_TIMEOUT=60  # 60 seconds instead of 30
   ```

3. Switch to paid tier for dedicated inference

---

## **7️⃣ COMPARE AI PROVIDERS**

| Feature | OpenRouter | Hugging Face | Gemini |
|---------|-----------|--------------|--------|
| **Free Tier** | ✅ Yes (some models) | ✅ 30k tokens/month | ✅ Yes (limited) |
| **Setup** | Easy | Easy | Easy |
| **Speed** | Fast | Medium | Fast |
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Models** | 100+ | 100,000+ | 1 (Gemini) |
| **Best For** | Production | Testing/Backup | Backup |

---

## **8️⃣ ADVANCED: USE DIFFERENT MODELS PER CHANNEL**

You can customize which model to use for each channel:

Edit `backend/worker/ai_agent.py`:

```python
# Channel-specific models
CHANNEL_MODELS = {
    "web_form": "mistralai/Mixtral-8x7B-Instruct-v0.1",  # High quality
    "whatsapp": "microsoft/Phi-3-mini-4k-instruct",      # Fast
    "email": "meta-llama/Meta-Llama-3-8B-Instruct"       # Balanced
}

async def _call_huggingface(self, messages, channel="web_form"):
    model = CHANNEL_MODELS.get(channel, self.huggingface_model)
    model_url = f"{self.huggingface_url}/{model}"
    # ... rest of the code
```

---

## **9️⃣ MONITORING USAGE**

### **Check Token Usage**

Visit: **https://huggingface.co/settings/billing**

Free tier shows:
- ✅ Tokens used this month
- ✅ Remaining quota
- ✅ API call history

### **Monitor in Your App**

Check worker logs:
```bash
# Look for:
INFO: Hugging Face response generated (~150 tokens)
```

Add to metrics endpoint (optional):
```python
# In backend/api/routes/metrics.py
{
    "ai_provider": "huggingface",
    "model": settings.huggingface_model,
    "tokens_used_today": 1250
}
```

---

## **🔟 COMPLETE SETUP CHECKLIST**

- [ ] Hugging Face account created
- [ ] API token generated (starts with `hf_`)
- [ ] Model selected (default: Mixtral-8x7B-Instruct)
- [ ] `.env` file updated with `HUGGINGFACE_API_KEY`
- [ ] Backend restarted
- [ ] Test API call successful
- [ ] Test web form submission works
- [ ] Worker logs show "Hugging Face response generated"
- [ ] Response received in web form/WhatsApp/email

---

## **🚀 QUICK START COMMANDS**

```bash
# 1. Set environment variable
export HUGGINGFACE_API_KEY=hf_your-token

# 2. Start backend
cd /home/saadahmed/hk-5/backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 3. Start worker (in another terminal)
cd /home/saadahmed/hk-5
python backend/worker/message_processor.py

# 4. Test with curl
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test",
    "email": "test@example.com",
    "subject": "Test",
    "category": "general",
    "priority": "medium",
    "message": "Hello from Hugging Face!"
  }'
```

---

## **💡 TIPS & BEST PRACTICES**

1. **Use Instruct Models**: Always choose models with "Instruct" or "Chat" in the name
2. **Test Multiple Models**: Try different models to find the best fit
3. **Monitor Rate Limits**: Free tier has monthly limits
4. **Have Fallback**: Keep OpenRouter/Gemini as backup
5. **Optimize Prompts**: Shorter prompts = faster responses
6. **Cache Common Responses**: Reduce API calls for FAQs

---

## **📚 RESOURCES**

- **Hugging Face Docs**: https://huggingface.co/docs/api-inference
- **Model Hub**: https://huggingface.co/models?pipeline_tag=text-generation
- **API Playground**: https://huggingface.co/spaces/huggingface-projects/llm-leaderboard
- **Free Models List**: https://huggingface.co/models?sort=trending&search=instruct

---

**Integration Complete**: 2026-04-02  
**Status**: ✅ **READY TO USE**
