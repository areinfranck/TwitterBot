import requests
import re
import tweepy
import time
from datetime import datetime
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

# A list of authentications keys for the twitter API.
authenticationKeys = []
# A list of hashtags/keywords the bot will not retweet.
blacklist = []

with open('authentication-keys', 'r') as fileHandle:
    for line in fileHandle:
        key = line[:-1]
        authenticationKeys.append(key)

with open('blacklist', 'r') as fileHandle:
    for line in fileHandle:
        keyword = line[:-1]
        blacklist.append(keyword)

auth = tweepy.OAuthHandler(authenticationKeys[0], authenticationKeys[1])
auth.set_access_token(authenticationKeys[2], authenticationKeys[3])

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
user = api.me()

# Username of logged in account.
print("*** Account Username: " + user.name + " ***\n")
print("Now listening...")


def format_message(tweet, reason, discardedTweet):
    # The following gets printed to the console:
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S %D")

    if discardedTweet:
        print("*** The following tweet has been discarded due to " + reason + ": ***")
    else:
        print(">>>>>>> The following message has been RETWEETED: <<<<<<<")

    print("Tweet ID: ", tweet.id)
    print("Username: " + tweet.user.name)
    print("Message: \"" + tweet.full_text + "\"\n")
    print("Received at: " + current_time)
    print("--------------------------------")


# Checks if tweet contains a blacklisted keyword.
def blacklist_check(tweetString):
    splitString = tweetString.split()
    return any(item in splitString for item in blacklist)


# Checks if tweet contains media attachment.
def media_attachment(tweetString):
    mediaAttachment = "https://t.co/"
    return tweetString.count(mediaAttachment) == 0


# Checks language of tweet.
def check_language(tweetString):
    try:
        noURLString = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', tweetString)
        if not noURLString:
            return True
        return detect(noURLString) != 'en'
    except LangDetectException as languageError:
        print('\nUnable to determine language, tweet skipped.\n', languageError, "\n")
        print("--------------------------------")
        return True


# Checks if media attachment redirects to Instagram.
def is_instagram_link(tweetString):
    try:
        splitString = tweetString.split()
        URL = splitString[len(splitString) - 1]

        request = requests.head(URL, allow_redirects=True)
        if request.url[:26] == "https://www.instagram.com/":
            return True
        else:
            return False
    except requests.RequestException as requestException:
        print("\nUnable to determine link destination.\n", requestException, "\n")
        print("--------------------------------")
        return True


class TwitterStreamListener(tweepy.streaming.StreamListener):

    def on_status(self, status):

        try:
            tweet = api.get_status(status.id, tweet_mode="extended")
        except tweepy.TweepError:
            print("\n---No status found with that ID---\n")
            return True
        try:
            def index_tweet(tweetString):
                try:
                    if blacklist_check(tweetString.lower()):
                        format_message(tweet, "BLACKLIST KEYWORD", True)
                        return True
                    elif media_attachment(tweetString):
                        format_message(tweet, "NO MEDIA ATTACHMENT", True)
                        return True
                    elif is_instagram_link(tweetString):
                        format_message(tweet, "EXTERNAL LINK", True)
                        return True
                    elif check_language(tweetString):
                        format_message(tweet, "NON-ENGLISH CHARACTERS", True)
                        return True
                except tweepy.TweepError as error:
                    print("\nUnable to check criteria of tweet.\n" + error.reason + "\n")
                    return True

            if index_tweet(tweet.full_text):
                # Called if tweet does not meet criteria.
                return True
            else:
                tweet.retweet()
                format_message(tweet, "RETWEETED", False)
                print("\n======= The bot will now sleep for 30 minutes.... =======\n")
                time.sleep(1800)
                print("\n======= Bot has resumed listening to Twitter feed.... =======\n")
                return True

        except tweepy.TweepError as e:
            print("\n*** Unable to scan the contents of the tweet. ***\n" + e.reason)
            return True

    def on_error(self, status_code):
        print('Error while listening to stream: ' + str(status_code))
        return True

    def on_timeout(self):
        print('Network issue, unable to reach API and/or request limit met...')
        return True


try:
    listener = TwitterStreamListener()

    stream = tweepy.streaming.Stream(auth, listener)

    stream.filter(track=["#Husky"])
except tweepy.TweepError as streamFilterError:
    print("\nAn error has occurred while filtering stream. Will try again...\n", streamFilterError)
