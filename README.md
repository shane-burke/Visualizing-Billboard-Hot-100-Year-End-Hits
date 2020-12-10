# Mapping Music: Visualizing Billboard's Year-End Top 100, 2004 to now

Since August of 1958, Billboard has released a weekly chart ranking the top songs in America based on sales, radio play, and digital streams on platforms like Spotify, Apple Music, and YouTube (added to the count in 2018). At the end of the year, they release their top 100 songs of the year. Year-end charts since 2004 are available on their website. 

Much has changed in music since 2004. A lot of this owes to the internet. With the advent of pirating, and later streaming, users are not paying for songs like before. They are not beholden to the sounds of the radio -- they can listen to what they want, whenever, and experiment more music like it. Streams are a new source of revenue, too, though each stream generates a small fraction of a record sale's revenue. 

At the same time, the internet has given a platform to artists who might not have made it big in the old power structure.

Take "Old Town Road" by Lil Nas X. Lil Nas X posted the song as an indie rapper in 2019. The playful song went insanely viral on TikTok, fueling streams and sales. (Billboard's initial disqualification of this song from the country charts--as a rap country song--also created buzz that propelled this song upward.) The song became the longest-running Hot 100 #1 yet, staying there for 17 weeks. 

Theoretically, artists' genres and geographies would matter less in the digital milieu. This map visualizes the origins and genres of musicians in Billboard's year-end chart from 2004 onward to see if that's true.

Here are the steps I took to execute this project:
* I scraped the Billboard website for its year-end hits using Python's <b>BeautifulSoup</b> package.
* I scraped Google's knowledge graph results for artists' birthplaces and descriptions using <b>Selenium</b> with Python.
* I gathered information from JSONS via the API of MusicBrainz, an artist database, to gather information on artists' genres.
* Managed data along the way with Python's <b>Pandas</b> package and <b>Excel</b>.
* Exported my data as a GeoJSON and used <b>MapBoxGL</b> to map it.
* Styled the webpage with HTML and CSS.

Here is a screenshot of the interactive map, which I plan to post online momentarily:
<img src="https://i.imgur.com/uSCnSAB.png"/>