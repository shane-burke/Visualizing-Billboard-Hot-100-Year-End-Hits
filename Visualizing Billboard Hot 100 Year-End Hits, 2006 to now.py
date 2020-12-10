#!/usr/bin/env python
# coding: utf-8

# ### Shane Burke

# ### <b>Importing packages</b>:

# In[4]:


import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
from pprintpp import pprint as pp
import time


# # <i>Part 1:</i> Gathering songs from Billboard:
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


df = pd.DataFrame(songs)


# In[ ]:


df.artist.value_counts()
#Gives us the artists with the most year-end entries


# ***************
# # <i>Part 2:</i> Pulling artists' genres (and some geographic information) with the Musicbrainz.com API
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
#df.to_csv(r'/Users/shaneburke/Desktop/Billboard_Scrape.csv', index=False)


# In[43]:


#df_billboard.head()


# ***********************
# # <i>Part 3:</i> Scraping Google's Knowledge Graph for more accurate birthplaces, age, and descriptions
# While Musicbrainz has a lot of information and might serve us better for aritsts who were born in one place but moved and rose out of another scene, it is imperfect. The values are all at different levels -- for instance, sometimes there will be cities, states, and countries in the same column. 
# 
# Google's artist bio information is a little more robust and accurate for most artists. They have an API for the knowledge graph, but it does not provide the full information we need, so I used Selenium to automatically load each artist's page and scrape Google with a big delay, to avoid being blocked.
# 
# We are going to continue using the Genres from musicbrainz, as those are more accurate than the birthdates and not availble on Google's graph.

# ### Steps:
# * Importing selenium
# * Gathering unique artist names based on value counts -- it ends up being a bit over 500 artists.
# * Loading each artist's search result page and scraping it based on the xpath, skipping those that don't fit. Xpath is the easiest way in this HTML to do it.
#     * The structure isn't the same for all artists, so a little cleaning is required after.
#     * Bands also sometimes have members within xpath where artists would be.
#     * We are going to skip the ones who don't fit for now and clean up our CSV.
# * Creating a new dataframe with just artists. We'll merge this to the original later.

# In[15]:


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait


# In[ ]:


artists = df.artist.value_counts().index


# In[ ]:


driver = webdriver.Chrome()


# In[ ]:


artist_data = []

for artist in artists:
    time.sleep(11.36)
    url = f'http://www.google.com/search?q={artist}'
    driver.get(url)
    try:
        origin = driver.find_element_by_xpath("/html/body/div[8]/div[2]/div[10]/div[1]/div[3]/div[1]/div/div[1]/div[2]/div/div/div[2]/div/div/div/div[2]/div/div/div/span[2]/a").text.strip()
        solo_or_group = "solo"
        born = driver.find_element_by_xpath("/html/body/div[8]/div[2]/div[10]/div[1]/div[3]/div/div/div[1]/div[2]/div/div/div[2]/div/div/div/div[2]/div/div/div/span[2]").text.strip()
        description = driver.find_element_by_xpath("/html/body/div[8]/div[2]/div[10]/div[1]/div[3]/div/div/div[1]/div[2]/div/div/div[2]/div/div/div/div[1]/div/div/div/div/span[1]").text.strip()


        
    except:
        origin = "n/a"
        born = "n/a"
        description = "n/a"

    
    print(artist, "...", origin)
    print(description)
    
    artist_data.append({'artist' : artist,
                        'origin' : origin,
                        'born' : born,
                        'description' : description
                        })

driver.close()


# In[ ]:


#print(artist_data.head(10))


# In[ ]:


df = pd.DataFrame(artist_data)


# In[19]:


#Save the artist information to a CSV and update some empty but important values.

#df.to_csv("artist_google_scrape.csv", index=False)


# In[ ]:


#Then I opened this CSV to fix values. 


# In[35]:


#df_artists = pd.read_csv("artist_google_scrape_update.csv")


# In[45]:


#df_artists.tail()


# *************
# 
# # <i>Part 4:</i> Geocoding locations
# * We are going to use artists' birthplaces to map them. We have the location, but not geographical coordinates. We are going to use the GeoPy package to scrape these.

# In[ ]:


#!pip install geopandas
#!pip install geopy
import geopandas
import geopy
from geopy.geocoders import Nominatim

#Loading up our artist dataframe.
df = pd.read_csv("/Users/shaneburke/Desktop/Data_and_Databases/Mapping Year-End Billboard Hot 100 Hits/artist_google_scrape_copy.csv", encoding = "ISO-8859-1")
df['latitude'] = "-"
df['longitude'] = "-"


# In[ ]:


#Searching for each "origin" location's coordinates and plugging latitude and longitude into their proper cells in the dataframe.

artist_row = -1

for origin in df['origin']:
    artist_row = artist_row + 1
    
    try:
        locator = Nominatim(user_agent="myGeocoder")
        location = locator.geocode(origin)

        try:
            df.iloc[artist_row, 4] = location.latitude
            df.iloc[artist_row, 5] = location.longitude
        except:
            df.iloc[artist_row, 4] = "-"
            df.iloc[artist_row, 5] = "-"
            
        #print(location.latitude, location.longitude)
        
    except: 
        pass


# In[12]:


#df[df.latitude == '-']
#About 5 of over 500 artists were not covered by the geopy database. That's ok -- we can fill these in based on Google Maps coordinates either with pandas or in Excel.


# In[11]:


#Quick visualization scatter map

df[df['latitude'] != "-"].plot(kind='scatter', 
                 x = 'longitude',
                 y= 'latitude',
                figsize = [20, 10])


# *********************************
# # <i>Part 5:</i> Merging the Billboard/Musicbrainz Dataframe and the Cleaned Google Dataframe

# In[46]:


df_merged = df_billboard.merge(df_artists, left_on = "artist", right_on = "artist")


# In[222]:


df_merged.head(5)


# In[224]:


#df_merged.to_csv("merged_billboard_scrape.csv", index=False)


# ****************
# 
# ### <i>Quick detour</i>: 
# Some quick aggregate functions to understand the data

# In[50]:


#Artists with most charting songs as lead
df_merged.artist.value_counts()


# In[219]:


#Group or solo: Bands do not display an "age" on Google, but artists do.
df_bands = df_artists[(df_artists.born.str.contains("age ", na=False) == False)]
df_bands.head(5)


# ### Plotting Genre by Year

# In[2]:


df_hip_hop_or_rap_songs = df_merged[(df_merged.genre1.str.contains("hop", na=False))|
          (df_merged.genre2.str.contains("hop", na=False)) | 
          (df_merged.genre3.str.contains("hop", na=False)) | 
          (df_merged.genre1.str.contains("rap", na=False)) |
          (df_merged.genre1.str.contains("rap", na=False)) | 
          (df_merged.genre1.str.contains("rap", na=False))
         ]

df_rock_alt_songs = df_merged[(df_merged.genre1.str.contains("rock", na=False))|
          (df_merged.genre2.str.contains("rock", na=False)) | 
          (df_merged.genre3.str.contains("rock", na=False)) | 
          (df_merged.genre1.str.contains("alt", na=False)) |
          (df_merged.genre2.str.contains("alt", na=False)) | 
          (df_merged.genre3.str.contains("alt", na=False))
         ]

df_pop_songs = df_merged[(df_merged.genre1.str.contains("pop", na=False))|
          (df_merged.genre2.str.contains("pop", na=False)) | 
          (df_merged.genre3.str.contains("pop", na=False))
         ]

df_country_songs = df_merged[(df_merged.genre1.str.contains("country", na=False))|
          (df_merged.genre2.str.contains("country", na=False)) | 
          (df_merged.genre3.str.contains("country", na=False))
         ]


# In[6]:


print("Genres in Top 100 Year-End Songs by Year")

ax = df_hip_hop_or_rap_songs.year.value_counts(sort=False).plot(label = "hiphop/rap")
df_rock_alt_songs.year.value_counts(sort = False).plot(label = "rock/alt", ax=ax)
df_country_songs.year.value_counts(sort = False).plot(label = "country", ax=ax)
df_pop_songs.year.value_counts(sort = False).plot(label = "pop", ax=ax)

ax.legend(loc='upper right')

#From this, we can see a steep decrease in pop artists' charting in recent years, as well as a slight increase in country and rap. 


# **************
# # <i> Part 6: </i> Preparing dataframe for geoJSON treatment
# * To fit JSON format, we are going to eventually need a dataframe that only contains certain geometry and article variables. We are going to add these all to the merged dataframe and then duplicate what we need into a new JSON-friendly frame.

# In[ ]:


#Adding in JSON columns. Some are placeholders for now, but we'll add them in soon.

#Type and ID
df_merged['type'] = "Feature"

df_merged = df_merged.reset_index()
df_merged['id'] = df_merged['index'] + 1

#Geometry Features
df_merged['geometry.type'] = "Point"
df_merged['geometry.coordinates'] == "-"

#Properties
df_merged['properties.headline'] = "<b>“" + df_merged['title'] + "”</b> by " + df_merged['artist'] + ", " + df_merged['year'].apply(lambda x: str(x))
df_merged['properties.article'] = "<b>“" + df_merged['title'] + "”</b> by " + df_merged['artist'] + ", " + df_merged['year'].apply(lambda x: str(x)) + "<br/><br/><b>Born</b>:" + df_merged['born'] + "<br/><br/>" + df_merged['description']
df_merged['properties.radius'] = "7"
df_merged['properties.name'] = df_merged['title'] + " by " + df_merged['artist']
df_merged['properties.color'] = "-"

df_merged['properties.group_id'] = df_merged['year'] - 2006
df_merged['properties.group_name'] = df_merged['year']


# In[ ]:


#To add in coordinates in list format, which JSON needs.
def get_coords(row):
    row['geometry.coordinates'] = [row['longitude'], row['latitude']]
    return row

df_merged = df_merged.apply(get_coords, axis=1)


# In[ ]:


#Points' colors are based on artist genre. We are going to run a function to simplify genre into 7 bins.
#The genres detected are based on looking at popular value counts of the first genre tag.
#A few of the newer artists have empty genres, but that can be cleaned up in Excel.

def genre_simplified(genre):
    
    if "boy band" in genre:
        return "pop" 
    
    if "indie" in genre:
        return "rock/alternative"
    
    if "pop" in genre:
        return "pop"
    
    if "rock" in genre:
        return "rock/alternative"
    
    if "punk" in genre:
        return "rock/alternative"
    
    if "alt" in genre:
        return "rock/alternative"
    
    if "new wave" in genre:
        return "rock/alternative"
    
    if "latin" in genre:
        return "latin/reggaeton"

    if "reggaeton" in genre:
        return "latin/reggaeton"

    if "hop" in genre:
        return "hip-hop/rap"
    
    if "rap" in genre:
        return "hip-hop/rap"
    
    if "r&b" in genre:
        return "r&b/soul"
    
    if "soul" in genre:
        return "r&b/soul"
    
    if "country" in genre:
        return "country"
    
    else:
        return "other"


# In[ ]:


df_merged['genre_simplified'] = df_merged['genre1'].fillna(value="-").map(genre_simplified)


# In[ ]:


#Now we are assigning color based on genre. This is a highlighter color palette.


# In[ ]:


def genre_color(genre):
    
    if genre == "pop":
        return "#ff66e1"
    
    if genre == "rock/alternative":
        return "#ff8c2c"
    
    if genre == "hip-hop/rap":
        return "#e8ff2c"
    
    if genre == "r&b/soul":
        return "#C486FF"
    
    if genre == "latin/reggaeton":
        return "#3dddff"

    if genre ==  "country":
        return "#47ff37"
    
    if genre == "other":
        return "#A5A5A5"


# In[ ]:


df_merged['properties.color'] = df_merged['genre_simplified'].map(genre_color)


# In[ ]:


df_merged.origin.value_counts()


# In[ ]:


#Adding some noise to the latitude and longitude values around cities with a lot of people so they don't overlap.
#Creating a scrap dataframe with artists from the most popular origins and randomizing their coordinates and join back.

df_scrap = df[['artist', 'origin', 'longitude', 'latitude', 'geometry.coordinates']]
df_scrap = df_scrap.drop_duplicates() 


# In[ ]:


df_scrap = df_scrap[(df_scrap.origin == "Los Angeles, CA") |
        (df_scrap.origin == "Atlanta, GA") |
        (df_scrap.origin == "Toronto, Canada") |
        (df_scrap.origin == "London, United Kingdom") |
        (df_scrap.origin == "Nashville, TN") |
        (df_scrap.origin == "New York, NY") |
        (df_scrap.origin == "Miami, FL") |
        (df_scrap.origin == "Paris, France") |
        (df_scrap.origin == "Las Vegas, NV") |
        (df_scrap.origin == "Brooklyn, New York, NY") |
        (df_scrap.origin == "Chicago, IL") |
        (df_scrap.origin == "Manhattan, New York, NY")]


# In[ ]:


#Functions to add a fractional amount of random noise to longitudes and latitudes so they won't overlap.

from random import randint

def add_noise_lat(row):
    try:
        random_num = randint(-3, 3) * .01
        random_num = float(random_num)
        row['latitude'] = float(row['latitude']) + random_num
        return row
    except:
        pass
    
def add_noise_long(row):
    try:
        random_num = randint(-3, 3) * .01
        random_num = float(random_num)
        row['longitude'] = float(row['longitude']) + random_num
        return row
    
    except:
        pass


# In[ ]:


df_scrap = df_scrap.apply(add_noise_lat, axis=1)
df_scrap = df_scrap.apply(add_noise_long, axis=1)


# In[ ]:


#Compiling the new coordinates with noise
df_scrap = df_scrap.apply(get_coords, axis=1)


# In[ ]:


df_use = df_merged.merge(df_scrap, left_on = "artist", right_on = "artist", how="outer", suffixes=(None, 'updated'))


# In[ ]:


#Combining the frames of old and new coordinates
df_use['new_coords'] = df_use['geometry.coordinatesupdated'].combine_first(df_use['geometry.coordinates'])
df_use['geometry.coordinates'] = df_use['new_coords']


# In[ ]:


df = df_use


# **************
# # <i> Part 7: </i> JSON time!

# In[ ]:


#Taking only the JSON variables we need from our mega dataframe.
output = df_merged[['type', 'id', 'geometry.type', 'geometry.coordinates', 'properties.headline', 'properties.article', 'properties.radius', 'properties.name', 'properties.color', 'properties.group_id', 'properties.group_name']]
output.head()


# In[ ]:


ok_json = json.loads(output.to_json(orient='records'))
ok_json


# In[ ]:


def process_to_geojson(file):
    geo_data = {"type": "FeatureCollection", "features":[]}
    for row in file:
        this_dict = {"type": "Feature", "properties":{}, "geometry": {}}
        for key, value in row.items():
            key_names = key.split('.')
            if key_names[0] == 'geometry':
                this_dict['geometry'][key_names[1]] = value
            if str(key_names[0]) == 'properties':
                this_dict['properties'][key_names[1]] = value
        geo_data['features'].append(this_dict)
    return geo_data


# In[ ]:


geo_format = process_to_geojson(ok_json)
geo_format


# In[ ]:


#Variable name
with open('geo-data.js', 'w') as outfile:
    outfile.write("var infoData = ")
#geojson output
with open('geo-data.js', 'a') as outfile:
    json.dump(geo_format, outfile)


# In[ ]:


#This links up with our HTML file to display in MapBox GL!


# ***********
# # Steps After Python
# * Editing the HTML and CSS of the map page to display what we want -- text, legends, etc.

# In[ ]:




