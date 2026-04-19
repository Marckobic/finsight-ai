# Railway Backend Deployment

All config files are already in the repo (Procfile, railway.json, nixpacks.toml).
This is a one-time manual setup — takes ~10 minutes.

---

## Step 1 — Push your repo to GitHub

If not already done:
```bash
git add .
git commit -m "add railway + deployment config"
git push origin main
```

---

## Step 2 — Create Railway project

1. Go to https://railway.app
2. Click **New Project**
3. Choose **Deploy from GitHub repo**
4. Select your `finsight-ai` repository
5. Railway will auto-detect the `Procfile` and start building

---

## Step 3 — Set environment variables

In Railway dashboard → your service → **Variables** tab, add:

| Variable | Value |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI key (sk-...) |
| `PYTHON_VERSION` | `3.11` |

Optional (if you add auth later):
| `SECRET_KEY` | Any random string (use: `openssl rand -hex 32`) |

---

## Step 4 — Get your Railway URL

After first deploy (2–3 min):
1. Railway dashboard → your service → **Settings** tab
2. Under **Domains** → click **Generate Domain**
3. Copy the URL — looks like: `https://finsight-ai-production.up.railway.app`

---

## Step 5 — Update app.json with the Railway URL

In `apps/mobile/app.json`, replace:
```json
"apiUrl": "https://your-app.railway.app"
```
with your actual Railway URL:
```json
"apiUrl": "https://finsight-ai-production.up.railway.app"
```

Also update `apps/mobile/.env` (create from `.env.example`):
```
EXPO_PUBLIC_API_URL=https://finsight-ai-production.up.railway.app
```

---

## Step 6 — Rebuild and redeploy web

After updating the API URL:
```powershell
cd apps/mobile
npx expo export --platform web --clear
vercel --prod
```

---

## Step 7 — Verify backend is running

```bash
curl https://YOUR-RAILWAY-URL.up.railway.app/health
# Should return: {"status": "ok"}
```

---

## Notes

- Railway free tier gives $5/month credit — enough for light usage
- The service auto-sleeps after inactivity; first request after sleep takes ~10s (cold start)
- To avoid cold starts on the free tier, upgrade to Hobby ($5/mo) or use Railway's "Always On" setting
- Logs: Railway dashboard → your service → **Logs** tab
