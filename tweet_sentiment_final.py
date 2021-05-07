#!/usr/bin/env python
# coding: utf-8

# In[139]:


# Imports

#!pip install tweepy
#!pip install ipywidgets

import boto3
import json
import tweepy as tw
import os
import string
import numpy as np
import ipywidgets as widgets

# Access Twitter

consumer_key= 'RM9A4H79z1I2IYWA8FsqniUFt'
consumer_secret= 'IjtxnSWFvCWdqpbnDsU76eIPwvDZuRMPPOX9zJBZvGFx7PP27K'
access_token= '1230590210251067392-PYlf9tNwUzRllGlBa0MnCZHm6K5Hqv'
access_token_secret= 'Tsquav2CkiDG62nV3BgTFHkQte15Hz00Rc3VXSbjodz9w'

auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tw.API(auth, wait_on_rate_limit=True)

# Enable Use of Amazon Comprehend

comprehend = boto3.client('comprehend', region_name='us-east-1')


# Extract and run sentiment analysis on the Tweets
def get_tweets(tag_name, tweet_count=25):
    """
    Uses the Twitter API and tweepy to scrape the 50 most recent
    tweets using a hashtag determined by the user
    Parameter: the tag to be determined in the hashtag
    Return: The dictionary containing the scores for each of the
    four different sentiments (Positive, Negative, Neutral, and Mixed)
    """
    tag_name = '#' + tag_name
    
    tweet_data = api.search(q = tag_name, lang = 'en', result_type = 'mixed', count = tweet_count, tweet_mode = 'extended')
    
    tweets = []
    followers = []
    for i in range(len(tweet_data)):
        status = api.get_status(tweet_data[i].id, tweet_mode = 'extended')
        user = tweet_data[i].user
        followers.append(user.followers_count)
        if hasattr(status, 'retweeted_status'):  # Check if Retweet
            tweets.append(tweet_data[i].retweeted_status.full_text)
        else:
            tweets.append(tweet_data[i].full_text)
    return tweets, followers


def run_comprehend(tweets):
    """
    Takes in a list containing the text of popular tweets
    returns a dictionary with the 4 sentiment values as the keys
    the values are the lists of each sentiment for each tweet
    e.g.
    {'Positive':[0.1, 0.2, ..., 0.8], ..., 'Mixed':[0.1, 0.2, ..., 0.8]}
    """
    
    sentiment_scores = {'Positive':[], 'Negative':[], 'Mixed':[], 'Neutral':[]}
    for i in range(len(tweets)):
        sentiments = (comprehend.detect_sentiment(Text=tweets[i], LanguageCode='en'))['SentimentScore']
        for key, value in sentiments.items():
            sentiment_scores[key].append(value)
    
    return sentiment_scores


def get_relevance(followers):
    """Factors in the number of followers a tweet's owner has to determine
        how relevant that Tweet is (how many people see it/are affected by it)
        Parameters:
        - followers: the number of followers a Tweet's owner has
    """
    for i in range (len(followers)):
        followers[i] = np.sqrt(followers[i])
    total_followers = sum(followers)
    relevances = []
    for i in range(len(followers)):
        relevances.append(followers[i] / total_followers)
    return relevances


def overall_tweet_sentiment(sent_dict):
    """Computes the average sentiment for each Tweet
    - combining each of the four sentiments (Positive, Negative, Neutral, and Mixed)
    - Parameter: sent_dict:
        - structured as {'sentiment1': [score1, score2, ..., scoren], ..., sentiment4: [score1, score2, ..., scoren]}
    - return: a float value between -200 and 200 that reflects the overall sentiment of the article
    """
    sent_list = []
    for i in range(len(sent_dict['Positive'])):
        score = 200 * sent_dict['Positive'][i] + 0 * (sent_dict['Mixed'][i] + sent_dict['Neutral'][i]) - 200 * sent_dict['Negative'][i]
        sent_list.append(score)
    return sent_list


def compute_total_score(sent_list, relevances):
    """Takes in a list of several tweet sentiment scores
    - multiplies each score by that tweet's corresponding relevance
    - sums those all together for the overall score
    - return: a float value between -100 and 100 that reflects the sentiment score of the overall company
    """
    final_score = 0
    sentiment = ''
    
    for i in range(len(sent_list)):
        final_score += relevances[i] * sent_list[i]
    final_score = round(final_score, 2)
    if final_score >= 20:
        sentiment = 'Positive'
    elif final_score <= -20:
        sentiment = 'Negative'
    elif final_score <= 20 and final_score >= 10:
        sentiment = 'Neutral-Positive'
    elif final_score >= -20 and final_score <= -10:
        sentiment = 'Neutral-Negative'
    else:
        sentiment = 'Neutral'
    return final_score, sentiment


def main():
    #company = input('Enter the company\'s name (in one word): ')
    #tweet_count = input('Enter the number of Tweets to factor in (max of 100 for optimal runtime): ')
    
    input_text = widgets.Text(description = "Company")
    output_text1 = widgets.Text(description = "Score")
    output_text2 = widgets.Text(description = "Sentiment")
    display(input_text)
    slider = widgets.IntSlider(min=1, max=100, step=1, description="# of Tweets", value=25)
    
    display(slider)
    
    button = widgets.Button(description = "Run")
    display(button)
    
    def bind(sender):
        name = input_text.value
    def run_analysis(button):
        output_text1.value = ''
        output_text2.value = ''
        tweets, followers = get_tweets(input_text.value, slider.value)
        relevances = get_relevance(followers)
        sent_dict = run_comprehend(tweets)
        sent_list = overall_tweet_sentiment(sent_dict)
        total_score, sentiment = compute_total_score(sent_list, relevances)
        output_text1.value = str(total_score)
        output_text2.value = sentiment
    
    input_text.on_submit(bind)
    button.on_click(run_analysis)
    display(output_text1, output_text2)
    
    
# Main Execution

if __name__ == '__main__':
    main()


# In[ ]:




