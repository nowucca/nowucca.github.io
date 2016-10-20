---
layout: post
title:  "Free up disc space on a Mac using command line utilities"
date:   2016-10-20
comments: true
---

Recently I have had to backup some iPhones because they broke down or were dropped.
This necessitated getting good at freeing up space on my 512MB SSD disk.

I'm NOT going to enabled document syncing on MacOS Sierra, so this had to be a legitimate purge.

Here is my fishing rod: from your home directory:

    $ cd && du -g | sort -n

This will give me a sorted list of folders with numbers in gigabytes.
For me, this shows I have 127G of pictures, and a bunch of space-hungry apps.

    55	./Music
    55	./Music/iTunes
    66	./Library/Application Support
    95	./Library
    127	./Pictures

It's up to you to sort out how many MP3s have got to go!

For me, I found that removing some old iTunes phone backups saves the most.
These usually reside in ~/Library/Application Support/MobileSync on MacOS.

Hope this helps.
