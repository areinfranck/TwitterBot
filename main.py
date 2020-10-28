import tweepy
import time
from datetime import datetime
from langdetect import detect

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


def format_message(tweet):
    # To timestamp the tweet.
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S %D")

    # The following gets printed to the console:
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
        english = detect(tweetString) != 'en'
        return english
    except tweepy.TweepError as languageError:
        print('\nUnable to determine language, tweet skipped.\n')
        print(languageError)
        return True


# Checks if tweet contains instagram link (currently unused).
def check_if_instagram(tweetString):
    splitString = tweetString.split()
    mediaLink = splitString[len(splitString) - 1]


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
                    language = (detect(tweetString) != 'en')
                except tweepy.TweepError as languageError:
                    print('\nUnable to determine language, tweet skipped.\n')
                    print(languageError)
                    return True

                try:
                    # Checks to see if the tweet contains blacklist keywords.
                    if blacklist_check(tweetString):
                        print("*** The following tweet has been discarded due to BLACKLIST KEYWORD: ***")
                        format_message(tweet)
                        return True
                    # Checks to see if tweet has media attachment.
                    elif media_attachment(tweetString):
                        print("*** The following tweet has been discarded due to NO MEDIA ATTACHMENT: ***")
                        format_message(tweet)
                        return True
                    # Checks to see if tweet is in English.
                    elif check_language(tweetString):
                        print("*** The following tweet has been discarded due to NON-ENGLISH CHARACTERS: ***")
                        format_message(tweet)
                        return True
                except tweepy.TweepError as error:
                    print("\nUnable to check criteria of tweet.")
                    print(error.reason + "\n")
                    return True

            if index_tweet(tweet.full_text.lower()):
                # Called if tweet does not meet criteria.
                return True
            else:
                tweet.retweet()
                print(">>>>>>> The following message has been RETWEETED: <<<<<<<")
                format_message(tweet)
                # After successfully retweeting, the bot won't tweet for another 10 minutes.
                print("======= The bot will now sleep for 30 minutes.... =======")
                time.sleep(1800)
                print("\n======= Bot has resumed listening to Twitter feed.... =======\n")
                return True

        except tweepy.TweepError as e:
            print("\n*** Unable to scan the contents of the tweet. ***\n")
            print(e.reason)
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
    print("An error has occurred while filtering stream. Will try again...")
    print(streamFilterError)
