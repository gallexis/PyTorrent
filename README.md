
# PyTorrent - Python BitTorrent


PyTorrent is a CLI tool that downloads files from the BitTorrent network.

I wanted to make my own functional and straightforward program to learn how does BitTorrent protocol work and improve my python skills.

It is almost written from scratch, python 2.7 without twisted.
Only the pubsub library was used to create events, when a new peer is connected, or when data is received from a peer.

This tool needs a lot of improvements, but it does its job, you can :
-	Read a torrent file
-	Scrape udp or http trackers
-	Connect to peers
-	Ask them for the blocks you want
-	Save a block in RAM, and when a piece is completed and checked, write the data into you hard drive
-	Deal with the one-file or multi-files torrents
-	Leech or Seed to other peers

But you can’t :
-	Download more than one torrent at a time
-	Benefit of a good algorithm to ask your peers for blocks (code of rarest piece algo is implemented but is not used)
-	Pause and resume download

Don't hesitate to ask me questions if you need help, or send me a pull request for new features or improvements.

### Installation
You can run the following command to install the dependencies using pip

`pip install -r requirements.txt`

:boom: Because it's using the "select" function, this code will not be able to run on Windows: [python-select-on-windows](https://stackoverflow.com/a/22254123/3170071)

### Running the program
If you want to specify a torrent file, you need to edit it manually in the run.py file:  
``` python
self.torrent = Torrent.Torrent("path_to_your_torrent") 
```
Then simply run:
`python main.py`

The files will be downloaded in the same path as your run.py script.

### Sources :

I wouldn't go that far without the help of
[Lita](https://github.com/lita/bittorrent "Lita"), 
[Kristen Widman's](http://www.kristenwidman.com/blog/how-to-write-a-bittorrent-client-part-1 "Kristen Widman's blog") & the
[Bittorrent Unofficial Spec](https://wiki.theory.org/BitTorrentSpecification "Bittorrent Unofficial Spec"), so thank you.



