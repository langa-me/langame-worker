from typing import List
import os
import requests

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
headers = {
    "Authorization": f"Bot {DISCORD_BOT_TOKEN}"
}

def get_most_talkative_players_from_channel(channel_id) -> List[dict]:
    """
    Get the most talkative players from a Discord channel.
    :param channel_id: the channel id
    """
    url = f"https://discord.com/api/v8/channels/{channel_id}/messages?limit=100"
    # TODO: https://discord.com/developers/docs/resources/channel#get-channel-messages
    # impl filtering of dates
    r =  requests.get(url, headers=headers)
    if r.status_code != 200:
        raise ValueError(f"Failed to get the list of messages for channel {channel_id}. {r.text}")
    all_messages = r.json()
    # find most talkative people on this channel
    messages_per_user = {}
    for e in all_messages:
        # filter out bots (role "Bot") or ["user"]["bot"]=True
        if e.get("author", {}).get("bot", False):
            continue
        author_id = e.get("author").get("id")
        if author_id not in messages_per_user:
            messages_per_user[author_id] = []
        messages_per_user[author_id].append(e)
    sorted_by_nb_messages = sorted(messages_per_user.items(), key=lambda x: len(x[1]), reverse=True)
    # take top three distinct users
    top_talkers = []
    for e in sorted_by_nb_messages:
        if e[1][0].get("author").get("id") not in [j.get("id") for j in top_talkers]:
            top_talkers.append(e[1][0].get("author"))
    return top_talkers
