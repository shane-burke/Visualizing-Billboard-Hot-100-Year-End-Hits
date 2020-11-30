#!/usr/bin/env python
# coding: utf-8

# ### Shane Burke

# ### <b>Importing packages</b>:

# In[ ]:


import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
from pprintpp import pprint as pp
import time


# ### <b>Gathering songs from Billboard:</b>
# * Defining the function to gather each year's top 100 songs and artists from site HTML.
#     * Separating featured artists with RegEx -- there are a few notations for features. Let's assume first listed is the "artist."
#     * Appending them all to a dictionary.
#     * Using the length of the "titles" section because some years have missing values. For instance, 2011 had no 7 
#         in its list.
# * Running the gathering function.
# * Bringing the dictionary to a dataframe.

# In[ ]:


songs = []

def info_gathering(year):

    url = f'https://www.billboard.com/charts/year-end/{year}/hot-100-songs'
    raw_html = requests.get(url).content
    soup_doc = BeautifulSoup(raw_html, "html.parser")

    titles = soup_doc.find_all(class_="ye-chart-item__title")
    artists = soup_doc.find_all(class_="ye-chart-item__artist")

    song_range = list(range(0, len(titles)))
    for song in song_range:
        ranking = song+1
        title = titles[song].string.strip()
        artist = artists[song].get_text().strip()  

        #Teasing out the main artist by removing featured artists with different notations
        featured_artist = "n/a"

        if ", " in artist:
            featured_artist = re.findall(r"^.+, (.+)$",artist)[0]
            artist = re.findall(r"^(.+),",artist)[0]

        if "Featuring" in artist:
            featured_artist = re.findall(r"^.+ \(?Featuring (.+)$",artist)[0]
            artist = re.findall(r"^(.+) \(?Featuring",artist)[0]

        if "&" in artist:
            featured_artist = re.findall(r"^.+ & (.+)$",artist)[0]
            artist = re.findall(r"^(.+) &",artist)[0]

        if " X " in artist:
            featured_artist = re.findall(r"^.+ X (.+)$",artist)[0]
            artist = re.findall(r"^(.+) X",artist)[0]

        songs.append({'year' : year, 'rank' : ranking, 'title' : title, 'artist' : artist, 'featured_artist' : featured_artist})


# In[ ]:


year_range = list(range(2006, 2020))

for year in year_range:
    info_gathering(year)


# In[ ]:


#Pretty printing the songs to see what the dictionary looks like
#pp(songs)


# In[ ]:


df = pd.DataFrame(songs)


# In[ ]:


#Looking at section of the dataframe 
#df.tail(10)


# In[ ]:


df.artist.value_counts()
#Gives us the artists with the most year-end entries


# ### <b> Pulling artists' hometowns with the Musicbrainz.com API </b>
# * Setting the dataframe up for our new columns
# * Defining genre with a function
# * Pulling location and genre from the API (takes half an hour)
# * Saving dataframe to CSV

# In[ ]:


#Setting up the dataframes to include tags for location and genre based on what musicbrainz has.

df['area_name'] = "n/a"
df['area_type'] = "n/a"
df['begin_area_name'] = "n/a"
df['begin_area_type'] = "n/a"
df['country'] = "n/a"
df['genre1'] = "n/a"
df['genre2'] = "n/a"
df['genre3'] = "n/a"

df


# In[ ]:


#Defining the genre based on the top 3 tags. 
#There are up to 10 tags per artist in a dictionary, with a "count" to decide how good a match they are to this tag.
#The top genres are not listed in order, so this function will loop through them, rank, and knock out any that aren't top 3.

def genre_tags(artist_data):
    tag1 = ''
    tag1count = 0
    tag2 = ''
    tag2count = 0
    tag3 = ''
    tag3count = 0

    for tag in artist_data['artists'][0]['tags']:
        if tag['count'] > tag1count:
            tag2 = tag1
            tag2count = tag1count
            tag1 = tag['name']
            tag1count = tag['count']
        elif tag['count'] > tag2count:
            tag3 = tag2
            tag3count = tag2count
            tag2 = tag['name']
            tag2count = tag['count']
        elif tag['count'] > tag3count:
            tag3 = tag['name']
            tag3count = tag['count']
    
    return [tag1, tag2, tag3]


# In[ ]:


#Pulling artist tags with the API
#The API limits requests to 1 per second, so we have a 1.75 second timer in case.
#This takes about half an hour to run. When each row is finished, it prints "~*~*~" to show progress.

#These queries generate a list of artists who might match. Usually the first one is correct.
#So we're pulling area and genre with the first element of each query's list, as indicated by the [0] in artist_guess.

musician_row = -1

for musician in df.artist:
    musician_row = musician_row+1
    
    url = f'https://musicbrainz.org/ws/2/artist/?query=artist:{musician}&fmt=json'
    response = requests.get(url)
    time.sleep(1.75)
    artist_data = response.json()
    
    artist_guess = artist_data['artists'][0]
    
    if "area" in artist_guess.keys():
        if "name" in artist_guess['area'].keys():
            df.iloc[musician_row, 5] = artist_guess['area']['name']
        if "type" in artist_guess['area'].keys():
            df.iloc[musician_row, 6] = artist_guess['area']['type']
    
    if "begin-area" in artist_guess.keys():
        if "name" in artist_guess['begin-area'].keys():
            df.iloc[musician_row, 7] = artist_guess['begin-area']['name']
        if "type" in artist_guess['begin-area'].keys():
            df.iloc[musician_row, 8] = artist_guess['begin-area']['type']

    if "country" in artist_guess.keys():
        df.iloc[musician_row, 9] = artist_guess['country']

    if "tags" in artist_guess.keys():
        tag_list = genre_tags(artist_data)
        df.iloc[musician_row, 10] = tag_list[0]
        df.iloc[musician_row, 11] = tag_list[1]
        df.iloc[musician_row, 12] = tag_list[2]
    
    print("~*~*~")


# In[ ]:


df


# In[ ]:


#Saving our dataframe to a CSV
df.to_csv(r'/Users/shaneburke/Desktop/Billboard_Scrape.csv')


# ## To be continued:
# * Cleaning location data
# * Mapping artists' presence across space over the years
# * Visualizing genre distribution over the year
# * Tracing trends -- like prominence of different cities' rap scenes, Spanish-language hits, "The British Invasion", and the impact of streaming on the geography of the music industry.

# In[ ]:




