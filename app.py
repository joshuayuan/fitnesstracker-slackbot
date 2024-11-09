import os, json
from datetime import datetime
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

import utils, team_specifics

app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))


@app.event("app_mention")
async def app_mention_event(say, body):
    event = body["event"]
    message_sender = event["user"]
    message_content = event["text"]

    link = utils.create_link(event["ts"])

    reply = await process_message(message_content, message_sender, link)
    await say(reply, thread_ts=event["ts"])


@app.command("/score")
async def get_score_response(ack, body):
    user_id = body["user_id"]
    user_name = await utils.fetch_user_real_name(user_id)
    if not user_name:
        await ack(f"Sorry, couldn't find any information for user {user_id}.")
        return
    new_line_element = {
        "type": "rich_text_section",
        "elements": [{"type": "text", "text": "\n"}],
    }
    intro_element = {
        "type": "rich_text_section",
        "elements": [
            {
                "type": "text",
                "text": "Hi, ",
            },
            {
                "type": "user",
                "user_id": f"{user_id}",
            },
            {"type": "text", "text": "!\n"},
        ],
    }

    score, rank = utils.get_your_score_rank(user_name)
    user_score_element = {
        "type": "rich_text_section",
        "elements": [
            {
                "type": "text",
                "text": (
                    f"Your current rank is {rank} and you've climbed {score} rungs."
                    if score
                    else f"I couldn't find anything for {user_name} ({user_id}). Sorry!"
                ),
            }
        ],
    }

    team_score = utils.get_team_scores()
    score_table = f"Team Follow the Ladder:\t\t{team_score[0]}\n"
    score_table += f"Team See ya Ladder:\t\t\t{team_score[1]}\n"
    score_table += f"Team Higgs Boson coLadder:\t{team_score[2]}\n"
    score_table += f"Team bLadder:\t\t\t\t{team_score[3]}"
    team_scores_element = {
        "type": "rich_text_section",
        "elements": [
            {
                "type": "text",
                "text": "\nAll Teams Scores:\n",
                "style": {
                    "bold": True,
                },
            },
            {
                "type": "text",
                "text": score_table,
            },
        ],
    }

    leaders = utils.get_leaders()
    leaders_table = ""
    for name, score in leaders:
        leaders_table += f"{name}:\t\t{score}\n"

    leaders_element = {
        "type": "rich_text_section",
        "elements": [
            {
                "type": "text",
                "text": "\nLeaders:\n",
                "style": {
                    "bold": True,
                },
            },
            {
                "type": "text",
                "text": leaders_table,
            },
        ],
    }

    bottoms = utils.get_bottoms()
    bottoms_element = {
        "type": "rich_text_section",
        "elements": [
            {
                "type": "text",
                "text": f"\n{bottoms} are currently at the bottom of the ladder. Be a buddy and encourage one of them to join you in your next activity!",
            }
        ],
    }

    await ack(
        {
            "blocks": [
                {
                    "type": "rich_text",
                    "elements": [
                        intro_element,
                        user_score_element,
                        new_line_element,
                        team_scores_element,
                        new_line_element,
                        leaders_element,
                        new_line_element,
                        bottoms_element,
                    ],
                }
            ]
        }
    )
    # print(json.dumps(body, indent=4))


async def process_message(message, sender, link):
    """
    takes in string message
    uploads a row in google sheets

    returns a string reply
    """
    mentioned_user_ids = utils.extract_mentioned_user_ids(message)
    eligible_participants = []
    for mentioned_user_id in mentioned_user_ids:
        if mentioned_user_id == "U07V5E106ES":
            # skip for this bot
            continue
        display_name = await utils.fetch_user_real_name(mentioned_user_id)
        eligible_participants.append(str(display_name))

    timestamp = str(datetime.now())
    sender_name = await utils.fetch_user_real_name(sender)
    eligible_participants.append(sender_name)

    activities, unfamiliar_activities = utils.extract_activities(message)

    if len(unfamiliar_activities) == 0 and len(activities) == 0:
        return ""
    elif len(unfamiliar_activities) > 0 and len(activities) == 0:
        return f"I didn't recognize {str(unfamiliar_activities)}. Please try again and remember to also tag me."

    bottom_list = utils.get_bottoms()
    misc = {"bottoms": list(set(bottom_list) & set(eligible_participants))}
    for participant in eligible_participants:
        addon_points = await utils.calculate_addon_points(
            participant, sender_name, eligible_participants, bottom_list
        )
        for activity in activities:
            activity_points = team_specifics.ACTIVITIES_TO_POINTS[activity]
            # new_row should be carefully structured to match with the spreadsheet.
            new_row = [
                timestamp,
                participant,
                activity,
                sender_name,
                message,  # original message text
                link,  # permalink
                activity_points,  # activity points
                addon_points,  # add on points
                activity_points + addon_points,  # total points
                json.dumps(misc),  # misc data
            ]
            result = utils.add_raw_data_row(new_row)

    return f"""
        Added rows for {str(activities)} {'for ' + str(eligible_participants) if len(eligible_participants) > 0 else 'for you.'}
        \n\n
        To see your own score and the leaderboard, use the `/score` command in this channel.
        \n\n
        <{team_specifics.RAW_DATA_SHEET_URL}|Click here> to view the raw data that is being recorded.
        """


# should be at bottom of the file
async def main():
    await AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start_async()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
