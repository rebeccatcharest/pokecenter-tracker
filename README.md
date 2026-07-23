# Pokemon Center Stock Robot 🤖

This little robot checks the Pokemon Center website every 5 minutes for:
- Elite Trainer Boxes
- Booster Packs
- Tins

If it finds something that isn't sold out, it yells at you on Discord.

## Setup (like a treasure map, step by step)

### Step 1: Make a home for the robot (a GitHub repo)
1. Go to https://github.com and make a free account if you don't have one.
2. Click the "+" in the top right → "New repository."
3. Name it anything, like `pokecenter-tracker`.
4. Make sure it's set to **Public** (this keeps it free and unlimited).
5. Click "Create repository."

### Step 2: Put the robot's brain inside
1. In your new repo, click "Add file" → "Upload files."
2. Upload these files (keeping the folder structure!):
   - `checker.py`
   - `requirements.txt`
   - `state.json`
   - `.github/workflows/check.yml`
3. Click "Commit changes."

### Step 3: Give the robot your walkie-talkie (Discord webhook)
1. In Discord, go to the channel you want alerts in.
2. Server Settings → Integrations → Webhooks → New Webhook.
3. Copy the Webhook URL.
4. In your GitHub repo, go to Settings → Secrets and variables → Actions.
5. Click "New repository secret."
6. Name it exactly: `DISCORD_WEBHOOK_URL`
7. Paste the webhook URL as the value. Save.

### Step 4: Wind up the alarm clock
That's it — the workflow file already tells GitHub to run the robot every
5 minutes automatically. You don't need to do anything else.

### Step 5 (optional): Test it right now
1. In your repo, click the "Actions" tab.
2. Click "Pokemon Center Stock Check" on the left.
3. Click "Run workflow" → "Run workflow" (the green button).
4. Wait about 30-60 seconds, then check your Discord channel.

## How it decides what to alert you about
The robot looks at each product on the page. If it does NOT see the words
"Sold Out," "Unavailable," or "Coming Soon" near a product, it assumes
that product is buyable and sends you an alert. It remembers what it
already told you (in `state.json`) so it won't repeat itself -- but if
something sells out and comes back in stock later, it WILL alert you again.

## Things to know
- Pokemon Center restocks can sell out in minutes, so even 5-minute
  checks might miss the fastest drops.
- If the website changes its layout, the robot might get confused and
  need small tweaks to keep working.
- GitHub Actions may occasionally run a minute or two late during busy
  periods -- this is normal and out of our control.
