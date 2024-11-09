import re, os, pygsheets
from dotenv import load_dotenv
from slack_sdk.web.async_client import AsyncWebClient

import team_specifics

load_dotenv()

client = AsyncWebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

gc = pygsheets.authorize(
    service_file=os.environ.get("SPREADSHEET_API_PRIVATE_KEY_LOCATION")
)
spreadsheet = gc.open_by_key(os.environ.get("SPREADSHEET_KEY"))
raw_data_sheet = spreadsheet.worksheet_by_title("raw_data")
scores_sheet = spreadsheet.worksheet_by_title("scores")

TOP_OF_RANKINGS_ROW_NUMBER = 14
BOTTOM_OF_RANKINGS_ROW_NUMBER = 42


def add_raw_data_row(row):
    return raw_data_sheet.append_table(row)


# returns the people with top 3 rank
def get_leaders():
    rankings = scores_sheet.get_values(
        start=(TOP_OF_RANKINGS_ROW_NUMBER, 1), end=(BOTTOM_OF_RANKINGS_ROW_NUMBER, 3)
    )
    filtered_rankings = []
    for name, score, rank in rankings:
        if int(rank) <= 3:
            filtered_rankings.append([name, score])

    return filtered_rankings


def get_team_scores():
    team1 = scores_sheet.get_value("B1").split(": ")[-1]
    team2 = scores_sheet.get_value("D1").split(": ")[-1]
    team3 = scores_sheet.get_value("F1").split(": ")[-1]
    team4 = scores_sheet.get_value("H1").split(": ")[-1]
    return [team1, team2, team3, team4]


def get_your_score_rank(user_name):
    rankings = scores_sheet.get_values(
        start=(TOP_OF_RANKINGS_ROW_NUMBER, 1), end=(BOTTOM_OF_RANKINGS_ROW_NUMBER, 3)
    )
    for name, score, rank in rankings:
        if name == user_name:
            return score, rank
    return


def extract_activities(message):
    activities = []
    unfamiliar_activities = []
    hashtags = re.findall(r"#\w+", message)
    for hashtag in hashtags:
        tag = hashtag[1:]
        if tag in team_specifics.ACTIVITIES_TO_POINTS:
            activities.append(tag)
        else:
            unfamiliar_activities.append(tag)
    return (activities, unfamiliar_activities)


def extract_mentioned_user_ids(text):
    """Extracts user IDs from a Slack message text.

    Args:
        text: The text content of the Slack message.

    Returns:
        A list of user IDs mentioned in the text.
    """

    user_id_pattern = r"<@([A-Z0-9]+)>"
    user_ids = re.findall(user_id_pattern, text)
    return user_ids


async def fetch_user_real_name(user_id):
    try:
        response = await client.users_info(user=user_id)
        user_info = response["user"]
        slack_real_name = user_info[
            "real_name"
        ]  # Or 'profile.display_name' for more flexibility
        if slack_real_name in team_specifics.SLACK_NAME_MAPPING:
            return team_specifics.SLACK_NAME_MAPPING[slack_real_name]
        return slack_real_name
    except Exception as e:
        print(f"Error fetching user info for {user_id}: {e}")
        return None


async def calculate_addon_points(participant, sender, participants, bottom_list):
    points = 0
    if len(participants) > 1:
        points += 1
    for part in participants:
        if part == participant:
            continue
        is_bottom = await is_in_bottom(part, bottom_list)
        if is_bottom:
            points += 2
            break
    return points


async def is_in_bottom(participant, bottom_list):
    # cells = scores_sheet.get_values(start=(TOP_OF_RANKINGS_ROW_NUMBER,5), end=(BOTTOM_OF_RANKINGS_ROW_NUMBER,6))
    for name in bottom_list:
        if name == "":
            continue
        if name == participant:
            return True
    return False


def get_bottoms():
    cells = scores_sheet.get_values(
        start=(TOP_OF_RANKINGS_ROW_NUMBER, 5), end=(BOTTOM_OF_RANKINGS_ROW_NUMBER, 6)
    )
    filtered_cells = []
    for name, score in cells:
        if name != "":
            filtered_cells.append(name)
    return filtered_cells


def create_link(ts):
    return f"{team_specifics.SLACK_CHANNEL_BASE_URL}{''.join(ts.split('.'))}"
