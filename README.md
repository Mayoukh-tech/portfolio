# Mayoukh Modak — Portfolio Deployment Guide

## Folder Structure

```
portfolio-deploy/
├── public/
│   └── index.html          ← your portfolio (static, served as-is)
├── api/
│   └── contact.js          ← serverless function (API key lives here, server-side only)
├── netlify.toml            ← Netlify config
├── vercel.json             ← Vercel config
├── .env.example            ← env var template (safe to commit)
├── .gitignore              ← keeps .env out of git
└── README.md
```

---

## How It Works

```
Browser form submit
      │
      ▼
POST /api/contact   (your own endpoint — no key in browser)
      │
      ▼
Serverless function reads BREVO_API_KEY from env vars
      │
      ▼
Calls Brevo API → email lands in your inbox
```

Your API key **never leaves the server**. Even if someone inspects your page source or network tab, they only see a POST to `/api/contact` with `{name, email, message}`.

---

## Step 1 — Get your Brevo credentials

1. Sign up free at **brevo.com** (300 emails/day, no card needed)
2. **API Key:** `Settings` (top right) → `API Keys` → `Generate a new API key` → copy it
3. **Verified sender:** `Senders & Domains` → `Add a sender` → add your email → verify it

---

## Deploy on Vercel (Recommended — easiest)

### Option A — GitHub (recommended)

1. Push this folder to a GitHub repo
2. Go to [vercel.com](https://vercel.com) → `New Project` → import your repo
3. Vercel auto-detects the config. In the **Environment Variables** section add:
   ```
   BREVO_API_KEY = xkeysib-xxxxxxxxxxxxxxxxxxxxxxxx
   BREVO_FROM    = you@yourdomain.com
   ```
4. Click **Deploy** — done.

### Option B — Vercel CLI

```bash
npm i -g vercel
cd portfolio-deploy
vercel
# Follow prompts, then add env vars:
vercel env add BREVO_API_KEY
vercel env add BREVO_FROM
vercel --prod
```

---

## Deploy on Netlify

### Option A — GitHub (recommended)

1. Push to GitHub
2. Go to [netlify.com](https://netlify.com) → `Add new site` → `Import from Git`
3. Settings:
   - **Publish directory:** `public`
   - **Functions directory:** `api`  (Netlify reads from `netlify.toml` automatically)
4. Go to `Site configuration` → `Environment variables` → add:
   ```
   BREVO_API_KEY = xkeysib-xxxxxxxxxxxxxxxxxxxxxxxx
   BREVO_FROM    = you@yourdomain.com
   ```
5. Trigger a redeploy — done.

### Option B — Netlify CLI

```bash
npm i -g netlify-cli
cd portfolio-deploy
netlify init
netlify env:set BREVO_API_KEY "xkeysib-xxxx"
netlify env:set BREVO_FROM "you@yourdomain.com"
netlify deploy --prod
```

---

## Test Locally (Optional)

**Vercel:**
```bash
npm i -g vercel
cd portfolio-deploy
cp .env.example .env        # fill in real values
vercel dev                  # serves on http://localhost:3000
```

**Netlify:**
```bash
npm i -g netlify-cli
cd portfolio-deploy
cp .env.example .env        # fill in real values
netlify dev                 # serves on http://localhost:8888
```

---

## Security Summary

| What            | Where it lives      | Exposed to browser? |
|-----------------|---------------------|---------------------|
| BREVO_API_KEY   | Platform env vars   | ❌ Never             |
| BREVO_FROM      | Platform env vars   | ❌ Never             |
| Your email (TO) | api/contact.js      | Only in server logs  |
| Form data       | Request body        | ✅ Yes (expected)    |

The function also includes:
- Input validation (all fields required, valid email format, max 5000 chars)
- HTML escaping on all user inputs before they go into the email body
- Rate limiting is handled at platform level (Vercel/Netlify free tier limits)
