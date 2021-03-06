import os
import time
import re
from slackclient import SlackClient
import requests
import pandas as pd
import datetime


# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 3 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "getcurrency"
MENTION_REGEX = "^<@(|[WU].+)>(.*)"

cont = 0
CurrencyStats = 'getstats'

#################
##### Function that are called

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Sorry, something went wrong... Try again..."

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    command = command.lower()

    if command.startswith('help'):
        response = 'List of Available Commands:\ntop10 --> get top 10 currencies\ngetstats [currency1] [currency2] ... --> get specific currency'

    elif command.startswith('saluta'):
        response = 'Ciao ragazzi sono Orion! Potete chiamarmi per richiedere informazioni riguardo le quotazioni delle monete...'

    elif command.startswith('task'):
        pass

    elif command.startswith(CurrencyStats):
        response = ''
        lista = command.split()[1:]
        for el in lista:
            basepath = 'https://api.coinmarketcap.com/v1/ticker/{}/'.format(el)
            req = requests.get(basepath)
            result = req.json()
            response = response + result[0]['symbol'] + ': '+result[0]['price_usd'] + ' $' + '\n'


    elif command.startswith('top10'):
        response = ''
        basepath = 'https://api.coinmarketcap.com/v1/ticker/?limit=10'
        req = requests.get(basepath)
        result = req.json()
        for e in result:
            response = response + e['symbol'] + ': ' + e['price_usd'] + ' $' + '\n'

    elif 0:

        response = "Sure...write some more code then I can do that!"




    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


def evaluateDiff():

    # init
    if os.path.isfile('./data.csv'):
        fullDF = pd.DataFrame.from_csv('./data.csv')
    else:
        fullDF = pd.DataFrame()
    baseURL = 'https://api.coinmarketcap.com/v1/ticker/'

    # processing

    timeStamp = datetime.datetime.now()
    message = requests.get(baseURL).json()

    data = [timeStamp]
    col = ['TimeStamp']
    for c in message:
        name = c['name']
        price = c['price_usd']

        data.append(price)
        col.append(name)

    dfTMP = pd.DataFrame([data], columns=col)
    dfTMP.set_index('TimeStamp', inplace=True)


    fullDF = fullDF.append(dfTMP)
    fullDF.to_csv('./data.csv')

    # Analysis Data

    delay = 5 * 60  # in S
    delayM = delay / 60

    a = (timeStamp - fullDF.index).seconds > delay
    listPosition = [i for i in range(len(a)) if a[i] == True]

    if len(listPosition) > 0:
        position = max(listPosition)
        ref = fullDF.index[position]

        for e in dfTMP.columns:
            if e in fullDF.columns:
                differenza = 100 * (float(dfTMP.loc[timeStamp][e]) - float(fullDF.loc[ref][e])) / float(fullDF.loc[ref][e])
                minuteDistance = (timeStamp-ref).seconds/60

                
                # print (e)
                stringa = 'Attuale: ' + str(float(dfTMP.loc[timeStamp][e])) + ' , Precedente: ' + str(
                    float(fullDF.loc[ref][e])) + ' , Differenza: ' + str(differenza)
                # print (stringa)

                if differenza > 7.5 or differenza < -7.5:
                    stringa = '{}: {:+.2f}% negli ultimi {} minuti'.format(e,differenza,minuteDistance)
                    print (stringa)
                    slack_client.api_call(
                        "chat.postMessage",
                        channel='C8G63MA2G',
                        text=stringa
                    )



#### MAIN LOOP
if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())


            if command:
                handle_command(command, channel)
                # mHandler.gigio(slack_client,channel,command)
#            print(cont)

            if cont > 300:
                evaluateDiff()
                cont = 0


            time.sleep(RTM_READ_DELAY)

            cont = cont + RTM_READ_DELAY

    else:
        print("Connection failed. Exception traceback printed above.")

