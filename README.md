# lunchpoll-bot

A Slack bot that automatically runs a lunch/dinner poll for SNU VLSI Lab.

## 🍱 Features
- Automatically sends a poll to your Slack channel at:
  - 🕚 11:20 AM (Lunch)
  - 🕔 5:20 PM (Dinner)
- Voting options: `300동`, `301동`, `302동`, `안먹음` (301동은 저녁에는 제외)
- Automatically closes the poll after 10 minutes and announces the result

## 🚀 How to Deploy (Render)
1. Fork or clone this repo
2. Set the following environment variables in Render:
   - `SLACK_BOT_TOKEN`
   - `SLACK_SIGNING_SECRET`
   - `CHANNEL_ID` (Slack channel ID to post the poll)
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python lunchpoll_bot.py`
5. Set request URL for Slack Interactivity and Events:
