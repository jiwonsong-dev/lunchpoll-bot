import os
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Timer
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

bolt_app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
flask_app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)

current_poll = {
    "votes": defaultdict(str),
    "active": False,
    "message_ts": None,
    "channel_id": None
}

def send_poll():
    resp = bolt_app.client.chat_postMessage(
        channel=CHANNEL_ID,
        text="🍴 오늘 어디서 먹을까요?",
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text": "*🍴 오늘 어디서 먹을까요?*"}},
            {"type": "actions", "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "300동"}, "value": "300동", "action_id": "vote_option"},
                {"type": "button", "text": {"type": "plain_text", "text": "301동"}, "value": "301동", "action_id": "vote_option"},
                {"type": "button", "text": {"type": "plain_text", "text": "302동"}, "value": "302동", "action_id": "vote_option"},
                {"type": "button", "text": {"type": "plain_text", "text": "안먹음"}, "value": "안먹음", "action_id": "vote_option"}
            ]}
        ]
    )
    current_poll["votes"].clear()
    current_poll["active"] = True
    current_poll["message_ts"] = resp["ts"]
    current_poll["channel_id"] = resp["channel"]
    Timer(600, close_poll).start()

def close_poll():
    current_poll["active"] = False
    counts = defaultdict(int)
    for v in current_poll["votes"].values():
        counts[v] += 1
    if not counts:
        result = "아무도 투표하지 않았습니다... 😢"
    else:
        top, cnt = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0]
        result = f"⏱️ 투표 종료!\n오늘은 *{top}*에서 {cnt}명이 식사합니다! 🍽️"
    bolt_app.client.chat_postMessage(
        channel=current_poll["channel_id"],
        thread_ts=current_poll["message_ts"],
        text=result
    )

@bolt_app.action("vote_option")
def handle_vote(ack, body, respond):
    ack()
    uid = body["user"]["id"]
    val = body["actions"][0]["value"]
    if not current_poll["active"]:
        respond("이미 종료된 설문입니다.")
        return
    if uid in current_poll["votes"]:
        respond("이미 투표하셨습니다.")
        return
    current_poll["votes"][uid] = val
    respond(f"<@{uid}>님이 *{val}*에 투표하셨습니다!")

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

scheduler = BackgroundScheduler()
scheduler.add_job(send_poll, "cron", hour=2, minute=20, day_of_week='mon-fri') # UTC+9
scheduler.add_job(send_poll, "cron", hour=10, minute=33, day_of_week='mon-fri') # UTC+9
scheduler.add_job(send_poll, "cron", hour=19, minute=33, day_of_week='mon-fri') # UTC+9
scheduler.start()

if __name__ == "__main__":
    flask_app.run(port=3000)
