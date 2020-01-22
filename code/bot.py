import base64
from dotenv import load_dotenv
import io 
import json
import matplotlib.pyplot as plt
import meraki
import os
import requests
import sys
from webexteamsbot import TeamsBot
from webexteamsbot.models import Response

load_dotenv()

# Retrieve required details from environment variables
bot_email = os.getenv("COB_BOT_EMAIL")
teams_token = os.getenv("COB_BOT_TOKEN")
bot_url = os.getenv("COB_BOT_URL")
bot_app_name = os.getenv("COB_BOT_APP_NAME")
meraki_api_key = os.getenv("MERAKI_API_KEY")
umbrella_management_key = os.getenv("UMBRELLA_MANAGEMENT_KEY")
umbrella_management_secret = os.getenv("UMBRELLA_MANAGEMENT_SECRET")
umbrella_org_id = os.getenv("UMBRELLA_ORG_ID")
image_upload_url = os.getenv("IMAGE_UPLOAD_URL")
media_path = os.getenv("MEDIA_PATH")

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


def get_meraki_org_networks():
    dashboard = meraki.DashboardAPI(meraki_api_key, output_log=False)
    orgs = dashboard.organizations.getOrganizations()
    org = orgs[0]["id"]
    networks = dashboard.networks.getOrganizationNetworks(org)
    return [(network["name"], network["id"]) for network in networks]


def get_meraki_network_traffic(network_id):
    dashboard = meraki.DashboardAPI(meraki_api_key, output_log=False)
    network_traffic = dashboard.networks.getNetworkTraffic(network_id, timespan=86400)
    destinations_and_totals = {}
    for entry in network_traffic:
        if entry["application"] == "Miscellaneous web" or entry["application"] == "Miscellaneous secure web":
            if any(c.isalpha() for c in entry["destination"]):
                if entry["destination"] not in destinations_and_totals:
                    destinations_and_totals[entry["destination"]] = entry["sent"] + entry["recv"]
                else:
                    destinations_and_totals[entry["destination"]] = destinations_and_totals[entry["destination"]] + entry["sent"] + entry["recv"]
    network_traffic_desc = sorted(destinations_and_totals.items(), key=lambda x: x[1], reverse=True)
    return network_traffic_desc


def generate_network_traffic_chart(network_traffic_desc):
    top10_dests = network_traffic_desc[:10]
    labels = [dest[0] for dest in top10_dests]
    values = [dest[1] for dest in top10_dests]
    plt.switch_backend('agg')
    patches, texts = plt.pie(values, startangle=90)
    plt.legend(patches, labels, bbox_to_anchor=(1,0.5), loc="center right", fontsize=10, bbox_transform=plt.gcf().transFigure)
    plt.subplots_adjust(left=0.0, bottom=0.1, right=0.55)
    # # Set aspect ratio to be equal so that pie is drawn as a circle.
    # plt.axis('equal')
    # plt.tight_layout()
    # plt.show()
    plt.savefig(media_path + 'network_traffic.png')
    return "network_traffic.png"


# This function generates a basic adaptive card and sends it to the user
# You can use Microsofts Adaptive Card designer here:
# https://adaptivecards.io/designer/. The formatting that Webex Teams
# uses isn't the same, but this still helps with the overall layout
# make sure to take the data that comes out of the MS card designer and
# put it inside of the "content" below, otherwise Webex won't understand
# what you send it.
def show_operations_card(incoming_msg):
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
                                    "type": "Input.Text",
                                    "placeholder": "Placeholder text",
                                    "isVisible": false,
                                    "id": "card_type",
                                    "value": "choose_operation"
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
                                            "value": "meraki_network_traffic"
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


def show_meraki_networks_card_demo(roomId):
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
                                    "text": "Choose a Network",
                                    "weight": "Bolder",
                                    "size": "Medium"
                                },
                                {
                                    "type": "Input.Text",
                                    "placeholder": "Placeholder text",
                                    "isVisible": false,
                                    "id": "card_type",
                                    "value": "meraki_choose_network"
                                },
                                {
                                    "type": "TextBlock",
                                    "size": "Small",
                                    "text": "Network"
                                },
                                {
                                    "type": "Input.ChoiceSet",
                                    "id": "network_id",
                                    "placeholder": "Choose an organization network...",
                                    "choices": [
                                        {
                                            "title": "Chicago - HQ",
                                            "value": "dummy1"
                                        },
                                        {
                                            "title": "Orlando - Branch",
                                            "value": "dummy2"
                                        },
                                        {
                                            "title": "New York - DC",
                                            "value": "dummy3"
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
    attachment = attachment_start + attachment_insert.rsplit(',', 1)[0] + attachement_end
    backupmessage = "This is an example using Adaptive Cards."

    c = create_message_with_attachment(roomId,
                                       msgtxt=backupmessage,
                                       attachment=json.loads(attachment))
    print(c)
    return ""


def show_meraki_networks_card(roomId):
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
                                    "text": "Choose a Network",
                                    "weight": "Bolder",
                                    "size": "Medium"
                                },
                                {
                                    "type": "Input.Text",
                                    "placeholder": "Placeholder text",
                                    "isVisible": false,
                                    "id": "card_type",
                                    "value": "meraki_choose_network"
                                },
                                {
                                    "type": "TextBlock",
                                    "size": "Small",
                                    "text": "Network"
                                },
                                {
                                    "type": "Input.ChoiceSet",
                                    "id": "network_id",
                                    "placeholder": "Choose an organization network...",
                                    "choices": [
    '''
    attachment_insert = ''''''
    networks = get_meraki_org_networks()
    for network in networks:
        attachment_insert += '''
        {
            "title": "''' + str(network[0]) + '''",
            "value": "''' + str(network[1]) + '''"
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


# This function generates a basic adaptive card and sends it to the user
# You can use Microsofts Adaptive Card designer here:
# https://adaptivecards.io/designer/. The formatting that Webex Teams
# uses isn't the same, but this still helps with the overall layout
# make sure to take the data that comes out of the MS card designer and
# put it inside of the "content" below, otherwise Webex won't understand
# what you send it.
def show_meraki_traffic_card(roomId, network_id):
    network_traffic_desc = get_meraki_network_traffic(network_id)
    image_name = generate_network_traffic_chart(network_traffic_desc)
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
                                    "text": "Top Network Traffic Destinations",
                                    "weight": "Bolder",
                                    "size": "Medium"
                                },
                                {
                                    "type": "Image",
                                    "url": "''' + image_upload_url + image_name + '''",
                                    "size": "auto"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }
    '''
    backupmessage = "This is an example using Adaptive Cards."

    c = create_message_with_attachment(roomId,
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
                                    "type": "Input.Text",
                                    "placeholder": "Placeholder text",
                                    "isVisible": false,
                                    "id": "card_type",
                                    "value": "umbrella_destination"
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
    card_type = m["inputs"]["card_type"]
    if card_type == "choose_operation":
        selected_operation = m["inputs"]["operation"]
        if selected_operation == "umbrella_destination":
            show_umbrella_destination_card(incoming_msg["data"]["roomId"])
        elif selected_operation == "meraki_network_traffic":
            # show_meraki_networks_card(incoming_msg["data"]["roomId"])
            show_meraki_networks_card_demo(incoming_msg["data"]["roomId"])
    elif card_type == "umbrella_destination":
        domain = m["inputs"]["domain"]
        destination_list = m["inputs"]["destination_list"]
        status_code = add_domain_to_destination_list(domain, destination_list)
        if status_code == 200:
            return "Destination added successfully!"
        else:
            return "Error occurred during destination submission."
    elif card_type == "meraki_choose_network":
        network_id = m["inputs"]["network_id"]
        # show_meraki_traffic_card(incoming_msg["data"]["roomId"], network_id)
        show_meraki_traffic_card(incoming_msg["data"]["roomId"], "L_575334852396581790")

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
bot.add_command("/operations", "Show Cloud Operations", show_operations_card)
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