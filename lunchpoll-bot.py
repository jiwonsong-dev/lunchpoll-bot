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


def send_poll(poll_type="lunch"):
    if poll_type == "lunch":
        options = [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "300동"},
                "value": "300동",
                "action_id": "vote_300"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "301동"},
                "value": "301동",
                "action_id": "vote_301"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "302동"},
                "value": "302동",
                "action_id": "vote_302"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "안먹음"},
                "value": "안먹음",
                "action_id": "vote_none"
            }
        ]
    else:  # dinner
        options = [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "300동"},
                "value": "300동",
                "action_id": "vote_300"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "302동"},
                "value": "302동",
                "action_id": "vote_302"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "안먹음"},
                "value": "안먹음",
                "action_id": "vote_none"
            }
        ]

    resp = bolt_app.client.chat_postMessage(
        channel=CHANNEL_ID,
        text="🍴 오늘 어디서 먹을까요?",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*🍴 오늘 어디서 먹을까요?*"}
            },
            {
                "type": "actions",
                "elements": options
            }
        ]
    )

    current_poll["votes"].clear()
    current_poll["active"] = True
    current_poll["message_ts"] = resp["ts"]
    current_poll["channel_id"] = resp["channel"]

    Timer(600, close_poll).start()
    Timer(420, send_warning_message).start()


def send_warning_message():
    if not current_poll["active"]:
        return
    bolt_app.client.chat_postMessage(
        channel=current_poll["channel_id"],
        #thread_ts=current_poll["message_ts"],
        text="⏳ 3분 남았습니다! 아직 투표 안 하셨다면 지금 눌러주세요 🙌"
    )

def close_poll():
    current_poll["active"] = False
    vote_counts = defaultdict(int)
    for vote in current_poll["votes"].values():
        vote_counts[vote] += 1

    if not vote_counts:
        result_text = "아무도 투표하지 않았습니다... 😢"
    else:
        # 최고 득표 수 찾기
        max_votes = max(vote_counts.values())
        top_places = [place for place, count in vote_counts.items() if count == max_votes]

        if len(top_places) == 1:
            result_text = f"⏱️ 투표 종료!\n오늘은 *{top_places[0]}*에서 식사합니다! 🍽️"
        else:
            joined = ", ".join(top_places)
            result_text = f"⏱️ 투표 종료!\n동률입니다! 다음 중 한 곳에서 식사하면 좋을 것 같아요: *{joined}* (각 {max_votes}표)"

    bolt_app.client.chat_postMessage(
        channel=current_poll["channel_id"],
        text=result_text
    )

import re

@bolt_app.action(re.compile("vote_.*"))
def handle_vote(ack, body, respond):
    ack()
    user_id = body["user"]["id"]
    value = body["actions"][0]["value"]

    if not current_poll["active"]:
        respond("이미 종료된 설문입니다.")
        return

    if user_id in current_poll["votes"]:
        respond("이미 투표하셨습니다.")
        return

    current_poll["votes"][user_id] = value
    respond(f"<@{user_id}>님이 *{value}*에 투표하셨습니다!")

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/", methods=["GET"])
def health_check():
    return "lunchpoll-bot is running", 200

scheduler = BackgroundScheduler()
scheduler.add_job(lambda: send_poll("lunch"), "cron", hour=2, minute=20, day_of_week='mon-fri')
scheduler.add_job(lambda: send_poll("dinner"), "cron", hour=8, minute=20, day_of_week='mon-fri')
scheduler.add_job(lambda: send_poll("dinner"), "cron", hour=11, minute=24, day_of_week='mon-fri')
scheduler.start()

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port)
