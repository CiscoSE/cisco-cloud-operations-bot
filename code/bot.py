from dotenv import load_dotenv
import os
import requests
from webexteamsbot import TeamsBot
from webexteamsbot.models import Response
import sys
import json

load_dotenv()

# Retrieve required details from environment variables
bot_email = os.getenv("COB_BOT_EMAIL")
teams_token = os.getenv("COB_BOT_TOKEN")
bot_url = os.getenv("COB_BOT_URL")
bot_app_name = os.getenv("COB_BOT_APP_NAME")
umbrella_management_key = os.getenv("UMBRELLA_MANAGEMENT_KEY")
umbrella_management_secret = os.getenv("UMBRELLA_MANAGEMENT_SECRET")
umbrella_org_id = os.getenv("UMBRELLA_ORG_ID")

# Create a Bot Object
bot = TeamsBot(
    bot_app_name,
    teams_bot_token=teams_token,
    teams_bot_url=bot_url,
    teams_bot_email=bot_email,
    webhook_resource_event=[{"resource": "messages", "event": "created"},
                            {"resource": "attachmentActions", "event": "created"}]
)


# Create a custom bot greeting function returned when no command is given.
# The default behavior of the bot is to return the '/help' command response
def greeting(incoming_msg):
    # Loopkup details about sender
    sender = bot.teams.people.get(incoming_msg.personId)

    # Create a Response object and craft a reply in Markdown.
    response = Response()
    response.markdown = "Hello {}, I'm a chat bot. ".format(sender.firstName)
    response.markdown += "See what I can do by asking for **/help**."
    return response


# Create functions that will be linked to bot commands to add capabilities
# ------------------------------------------------------------------------

# A simple command that returns a basic string that will be sent as a reply
def do_something(incoming_msg):
    """
    Sample function to do some action.
    :param incoming_msg: The incoming message object from Teams
    :return: A text or markdown based reply
    """
    return "i did what you said - {}".format(incoming_msg.text)


def get_umbrella_destination_lists():
    r = requests.get(
        'https://management.api.umbrella.com/v1/organizations/{}/destinationlists'.format(umbrella_org_id), 
        auth=requests.auth.HTTPBasicAuth(umbrella_management_key, umbrella_management_secret)
    ).json()
    dest_lists = [(dest_list["name"], dest_list["id"]) for dest_list in r["data"]]
    return dest_lists


def add_domain_to_destination_list(domain, destination_list):
    payload = [{"destination": domain}]
    r = requests.post(
        'https://management.api.umbrella.com/v1/organizations/{}/destinationlists/{}/destinations'.format(umbrella_org_id, destination_list),
        json=payload,
        auth=requests.auth.HTTPBasicAuth(umbrella_management_key, umbrella_management_secret)
    )
    return r.status_code


# This function generates a basic adaptive card and sends it to the user
# You can use Microsofts Adaptive Card designer here:
# https://adaptivecards.io/designer/. The formatting that Webex Teams
# uses isn't the same, but this still helps with the overall layout
# make sure to take the data that comes out of the MS card designer and
# put it inside of the "content" below, otherwise Webex won't understand
# what you send it.
def show_card(incoming_msg):
    attachment = '''
    {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": 2,
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "Choose an Operation",
                                    "weight": "Bolder",
                                    "size": "Medium"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "Select an operation to perform across your Cisco cloud-based products.",
                                    "isSubtle": true,
                                    "wrap": true
                                },
                                {
                                    "type": "Input.ChoiceSet",
                                    "id": "operation",
                                    "placeholder": "Choose an operation...",
                                    "choices": [
                                        {
                                            "title": "View Meraki Traffic",
                                            "value": "meraki_traffic_analytics"
                                        },
                                        {
                                            "title": "Add Umbrella Domain Policy",
                                            "value": "umbrella_destination"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit"
                }
            ]
        }
    }
    '''
    backupmessage = "This is an example using Adaptive Cards."

    c = create_message_with_attachment(incoming_msg.roomId,
                                       msgtxt=backupmessage,
                                       attachment=json.loads(attachment))
    print(c)
    return ""


# This function generates a basic adaptive card and sends it to the user
# You can use Microsofts Adaptive Card designer here:
# https://adaptivecards.io/designer/. The formatting that Webex Teams
# uses isn't the same, but this still helps with the overall layout
# make sure to take the data that comes out of the MS card designer and
# put it inside of the "content" below, otherwise Webex won't understand
# what you send it.
def show_umbrella_destination_card(roomId):
    attachment_start = '''
    {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": 2,
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "Add a Destination to Umbrella",
                                    "weight": "Bolder",
                                    "size": "Medium"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "Enter a domain to add to an existing destination list.",
                                    "isSubtle": true,
                                    "wrap": true
                                },
                                {
                                    "type": "TextBlock",
                                    "size": "Small",
                                    "text": "Domain"
                                },
                                {
                                    "type": "Input.Text",
                                    "id": "domain",
                                    "placeholder": "example.com"
                                },
                                {
                                    "type": "TextBlock",
                                    "size": "Small",
                                    "text": "Destination List"
                                },
                                {
                                    "type": "Input.ChoiceSet",
                                    "id": "destination_list",
                                    "placeholder": "Choose a destination list...",
                                    "choices": [
    '''
    attachment_insert = ''''''
    dest_lists = get_umbrella_destination_lists()
    for dest_list in dest_lists:
        attachment_insert += '''
        {
            "title": "''' + str(dest_list[0]) + '''",
            "value": "''' + str(dest_list[1]) + '''"
        },
        '''
    attachement_end = '''
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit"
                }
            ]
        }
    }
    '''
    attachment = attachment_start + attachment_insert.rsplit(',', 1)[0] + attachement_end
    backupmessage = "This is an example using Adaptive Cards."

    c = create_message_with_attachment(roomId,
                                       msgtxt=backupmessage,
                                       attachment=json.loads(attachment))
    print(c)
    return ""


# An example of how to process card actions
def handle_cards(api, incoming_msg):
    """
    Sample function to handle card actions.
    :param api: webexteamssdk object
    :param incoming_msg: The incoming message object from Teams
    :return: A text or markdown based reply
    """
    m = get_attachment_actions(incoming_msg["data"]["id"])
    if "operation" in m["inputs"]:
        selected_operation = m["inputs"]["operation"]
        if selected_operation == "umbrella_destination":
            show_umbrella_destination_card(incoming_msg["data"]["roomId"])
    elif "domain" in m["inputs"] and "destination_list" in m["inputs"]:
        domain = m["inputs"]["domain"]
        destination_list = m["inputs"]["destination_list"]
        status_code = add_domain_to_destination_list(domain, destination_list)
        if status_code == 200:
            return "Destination added successfully!"
        else:
            return "Error occurred during destination submission."

    # return "card input was - {}".format(m["inputs"])


# Temporary function to send a message with a card attachment (not yet
# supported by webexteamssdk, but there are open PRs to add this
# functionality)
def create_message_with_attachment(rid, msgtxt, attachment):
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer ' + teams_token
    }

    url = 'https://api.ciscospark.com/v1/messages'
    data = {"roomId": rid, "attachments": [attachment], "markdown": msgtxt}
    response = requests.post(url, json=data, headers=headers)
    return response.json()


# Temporary function to get card attachment actions (not yet supported
# by webexteamssdk, but there are open PRs to add this functionality)
def get_attachment_actions(attachmentid):
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer ' + teams_token
    }

    url = 'https://api.ciscospark.com/v1/attachment/actions/' + attachmentid
    response = requests.get(url, headers=headers)
    return response.json()


# An example using a Response object.  Response objects allow more complex
# replies including sending files, html, markdown, or text. Rsponse objects
# can also set a roomId to send response to a different room from where
# incoming message was recieved.
def ret_message(incoming_msg):
    """
    Sample function that uses a Response object for more options.
    :param incoming_msg: The incoming message object from Teams
    :return: A Response object based reply
    """
    # Create a object to create a reply.
    response = Response()

    # Set the text of the reply.
    response.text = "Here's a fun little meme."

    # Craft a URL for a file to attach to message
    u = "https://sayingimages.com/wp-content/uploads/"
    u = u + "aaaaaalll-righty-then-alrighty-meme.jpg"
    response.files = u
    return response


# An example command the illustrates using details from incoming message within
# the command processing.
def current_time(incoming_msg):
    """
    Sample function that returns the current time for a provided timezone
    :param incoming_msg: The incoming message object from Teams
    :return: A Response object based reply
    """
    # Extract the message content, without the command "/time"
    timezone = bot.extract_message("/time", incoming_msg.text).strip()

    # Craft REST API URL to retrieve current time
    #   Using API from http://worldclockapi.com
    u = "http://worldclockapi.com/api/json/{timezone}/now".format(
        timezone=timezone
    )
    r = requests.get(u).json()

    # If an invalid timezone is provided, the serviceResponse will include
    # error message
    if r["serviceResponse"]:
        return "Error: " + r["serviceResponse"]

    # Format of returned data is "YYYY-MM-DDTHH:MM<OFFSET>"
    #   Example "2018-11-11T22:09-05:00"
    returned_data = r["currentDateTime"].split("T")
    cur_date = returned_data[0]
    cur_time = returned_data[1][:5]
    timezone_name = r["timeZoneName"]

    # Craft a reply string.
    reply = "In {TZ} it is currently {TIME} on {DATE}.".format(
        TZ=timezone_name, TIME=cur_time, DATE=cur_date
    )
    return reply


# Create help message for current_time command
current_time_help = "Look up the current time for a given timezone. "
current_time_help += "_Example: **/time EST**_"

# Set the bot greeting.
bot.set_greeting(greeting)

# Add new commands to the bot.
bot.add_command('attachmentActions', '*', handle_cards)
bot.add_command("/showcard", "show an adaptive card", show_card)
bot.add_command("/dosomething", "help for do something", do_something)
bot.add_command(
    "/demo", "Sample that creates a Teams message to be returned.", ret_message
)
bot.add_command("/time", current_time_help, current_time)

# Every bot includes a default "/echo" command.  You can remove it, or any
# other command with the remove_command(command) method.
bot.remove_command("/echo")

if __name__ == "__main__":
    # Run Bot
    bot.run(host="0.0.0.0", port=5000)