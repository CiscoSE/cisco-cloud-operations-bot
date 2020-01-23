# Cisco Cloud Operations Bot (COB)

For the FY20Q2 ASIC challenge, we wanted to explore and interact with our ever-growing cloud offerings. Cloud Operations Bot was created to show how Cisco's cloud offerings - with their API-driven designs - can be interfaced without even accessing the various dashboards that exists. For this submission, our focus was to prove the ease of interoperability between Webex Teams, Meraki Dashboard, and Umbrella. We were specifically excited to work with the newest addition to Webex Teams: Adaptive Cards.


## Business/Technical Challenge

Cloud Operations Bot seeks to prove the value and ease that comes from having cloud offerings with API-first mentalities. Because of this foundation, we can work across multiple products through an easy-to-use interface presented by cards within Webex Teams. This is extremely beneficial for everything from unitask requirements like pulling a particular report to more complicated workflows.


## Proposed Solution

Cisco Cloud Operations Bot is a solution that further extends Cisco's vision for unified cloud-based visibility and the benefits that customers gain by going all-in with Cisco! We accomplish this by providing a Webex Teams bot that has access to all of the customer's cloud accounts. COB provides a card-based system that makes it easy for users to not only read output from these accounts, but even provide complex inputs in a user-friendly manner. 

We focused on proving the ease of connecting 3 of Cisco's different cloud offerings: Webex Teams (collab), Meraki Dashboard (EN), and Umbrella (security). But this merely scratches the surface given Cisco's focus on cloud platforms. COB could easily be expanded to interact with Defense Orchestrator, DNA Center Cloud, Intersight, Webex Calling, and more!

As we like to say... *"The sky's the limit with Cloud Operations Bot!"*


## Cisco Products Technologies/ Services

Our solution levegerages the following Cisco technologies:

* [Meraki Dashboard](https://meraki.cisco.com/)
* [Umbrella](https://umbrella.cisco.com/)
* [Webex Teams](https://www.webex.com/team-collaboration.html)

Going forward, our solution could leverage these Cisco technologies as well:

* [Defense Orchestrator](https://www.cisco.com/c/en/us/products/security/defense-orchestrator/index.html)
* [DNA Center Cloud](http://dnacentercloud.cisco.com/)
* [Intersight](http://intersight.com/)
* ... and more!

## Team Members

* Bradford Ingersoll <bingerso@cisco.com> - US Commercial East
* Eric Scott <eriscott@cisco.com> - US Public Sector North East


## Solution Components

* [Python 3.7.3](https://www.python.org/)
* [Python Library - webexteamsbot](https://github.com/hpreston/webexteamsbot)
* [Python Library - Meraki Dashboard API](https://github.com/meraki/dashboard-api-python)
* [Python Library - matplotlib](https://matplotlib.org/)


## Usage

Being a Webex Teams bot, running Cloud Operations Bot simply requires filling out an .env file with the specified account parameters and a python-based environment that can host the bot to remain running.

Once the bot is running, join a 1:1 converstation or add Cloud Operations Bot to a room and begin using it!


## Installation

1. Clone this repo

```
git clone https://github.com/CiscoSE/cisco-cloud-operations-bot.git
```

2. Create a Python 3 environment (virtualenv preferred)

```
python3 -m venv venv
```

3. Activate the virtual environment
```
source venv/bin/active
```

4. Install the required modules using the requirements.txt

```
pip install -r example-requirements.txt
```

## Documentation

* [Webex Teams - Adaptive Cards](https://developer.webex.com/docs/api/guides/cards)
* [Adaptive Cards](https://adaptivecards.io/)
* [Meraki Dashboard API Docs](https://developer.cisco.com/meraki/api/#/rest)
* [Umbrella API Docs](https://docs.umbrella.com/umbrella-api/reference)


## License

Provided under Cisco Sample Code License, for details see [LICENSE](./LICENSE.md)

## Code of Conduct

Our code of conduct is available [here](./CODE_OF_CONDUCT.md)

## Contributing

See our contributing guidelines [here](./CONTRIBUTING.md)
