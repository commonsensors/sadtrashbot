import tweepy
import re
import random
import time
import os
from os import environ




CONSUMER_KEY = environ['CONSUMER_KEY']
CONSUMER_SECRET = environ['CONSUMER_SECRET']
ACCESS_KEY = environ['ACCESS_KEY']
ACCESS_SECRET = environ['ACCESS_SECRET']

USER_TO_COPY = environ['USER_TO_COPY']
NUM_OF_TWEETS = 2000

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
#api = tweepy.API(auth)
api = tweepy.API(auth, wait_on_rate_limit=True)




# function that grabs the last tweets from a user and returns all their words to a list
def fetch_words():
	sentences = []

	for tweet in tweepy.Cursor(api.user_timeline, screen_name=USER_TO_COPY, tweet_mode="extended").items(NUM_OF_TWEETS):
		if not hasattr(tweet, 'retweeted_status'):
			# remove mention handles (@sth) and URLs, if any
			t = re.sub(r'(@\S+)|(http\S+)', '', tweet.full_text.lower())
			#t = re.compile('[%s]' % re.escape(string.punctuation)).sub('', t)	#remove punctuation			
			sentences.append(t)

	# create a list of individual words from the sentences/tweets
	words = []

	for sentence in sentences:
		for word in sentence.split():
			words.append(word)

	return words




# function that creates triples of words from the word list
def triples():
	words = fetch_words()

	if len(words) < 3:
		return

	for i in range(len(words) - 2):
		yield (words[i], words[i+1], words[i+2])




# function that creates the markov chains and returns the dictionary
def markov():
	word_dictionary = {}

	for word_1, word_2, word_3 in triples():
		key = (word_1, word_2)
		if key in word_dictionary:
			word_dictionary[key].append(word_3)
		else:
			word_dictionary[key] = [word_3]

	return word_dictionary




# function that uses the markov chain dictionary to create tweets
def generate_tweet(word_dictionary):
	words = fetch_words()

	size = random.randint(3, 50)	# min and max words in a tweet

	# pick a random word of the list to start the sentence
	seed = random.randint(0, len(words)-3)
	seed_word, next_word,  = words[seed], words[seed+1]
	word_1, word_2 = seed_word, next_word

	#word_dictionary = markov()

	status_words = []

	# create the sentence of the tweet, word by word
	for i in range(size):
		status_words.append(word_1)
		word_1, word_2 = word_2, random.choice(word_dictionary[(word_1, word_2)])

	status_words.append(word_2)

	status = ' '.join(status_words)

	if(len(status) > 260):
		status = '\U0001F97A'

	print('\t\'' + status + '\'')

	return status




# function that searches for mentions and responds with a generated tweet
def reply_to_mentions(word_dictionary):
	# read the last mention the bot has seen, to only respond to the ones after it
	f = open('last_seen_mention_id.txt', 'r')
	last_seen_mention_id = int(f.read().strip())
	f.close()

	# scan for new mentions
	mentions = api.mentions_timeline(last_seen_mention_id, tweet_mode="extended")

	# write down the current mention you're about to respond and reply to it
	for mention in reversed(mentions):
		if mention.user.screen_name != api.me().screen_name:
			last_seen_mention_id = mention.id

			f = open('last_seen_mention_id.txt', 'w')
			f.write(str(last_seen_mention_id))
			f.close()

			print('generating mention reply...')
			api.update_status('@' + mention.user.screen_name + generate_tweet(word_dictionary), mention.id)




while True:
	print('creating the markov chain dictionary...')
	word_dictionary = markov()

	reply_to_mentions(word_dictionary)

    # post once for every 5000 tries
	#if random.randint(1, 5000) == 1:
	print('generating tweet...')
	api.update_status(generate_tweet(word_dictionary))

	print('sleep mode for 1 minute...\n')

	time.sleep(60)


