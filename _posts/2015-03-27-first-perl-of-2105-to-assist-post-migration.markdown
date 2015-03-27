---
layout: post
title:  "First PERL script of 2015!"
date:   2015-03-27 06:28:11
categories: tech admin
---

I used a Ruby GEM "jekyll import" to convert my wordpress.xml file into Jekyll-style posts.
It left a bunch of information showing up on the page that I did not want.

I needed to translate file like this:

    ---
    ...some YAML...
    meta:
    ...extra meta and except stuff that was poorly done...
    ---
    post content

into a file like this:

    ---
    ...some YAML...
    ---
    post content

So I wrote my first perl script of this year to strip from meta to dashes.

The cool part is I can run it with

    perl fixup.pl *.html 

{% highlight perl linenos %}
#!/usr/bin/perl
use strict;

my $seenMeta = 0;
my $seenDashes = 0;
my $currentFile = "ss";
while(<>) {
   if ($currentFile ne $ARGV) {
     $seenMeta = 0;
     $seenDashes = 0;
     $currentFile = $ARGV;
     open FILE, ">", $currentFile.".new" or die $!;
   }
   $seenMeta = 1 if /^meta:/;
   if ($seenMeta == 1) {
     $seenDashes = 1 if /^---/;
   }
   if ($seenMeta == 1 && $seenDashes == 0) {
      next; #print "$ARGV -- $currentFile --  SUPPRESS " .  $_;
   } else {
      print FILE $_;
   }
} 
{% endhighlight %}
