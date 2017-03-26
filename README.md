
# PyTorrent - Python BitTorrent


PyTorrent is a cli tool that downloads files from the BitTorrent network.

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

But you can’t :
-	Download more than one torrent at a time
-	Upload data to the BitTorrent network
-	Benefit of a good algorithm to ask your peers for blocks (like the rarest piece algo)
-	And a lot of other things

Don't hesitate to ask me questions if you need help, or send me a pull request for new features or improvements.

### Todo
- Resume a download stopped
- Leech or Seed to other peers

### Installation
You can run the following command to install the dependencies using pip

`pip install -r requirements.txt`

:boom: Because it's using the "select" function, this code will not be able to run on Windows: [python-select-on-windows](http://stackoverflow.com/questions/22251809/python-select-select-on-windows)

### Running the program
If you want to specify a torrent file, you need to add it manually in the main.py file:  
``` self.torrent = Torrent.Torrent("your_torrent_file.torrent") ```

Then simply run:
`python run.py`

### Sources :

I wouldn't go that far without the help of
[Lita] (https://github.com/lita/bittorrent "Lita"), 
[Kristen Widman's blog] (http://www.kristenwidman.com/blog/how-to-write-a-bittorrent-client-part-1 "Kristen Widman's blog") and
[Bittorrent Unofficial Spec] (https://wiki.theory.org/BitTorrentSpecification "Bittorrent Unofficial Spec"), so thank you.



