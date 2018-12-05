---
layout: post
title:  "Monitoring Currency Rates with CasperJS and AppleScript"
date:   2016-03-17
---

# What is USForex?
I use the [USForex] currency exchange for sending money from Australia to the USA.
They offer a service where they quote you an exchange rate at which you can transfer money between countries,
without the cost and hassle of a wire transfer.

I really like their service: you can set up regular payments if you don't mind what the exchange rates are, or you can
use spot deals to transfer at the latest possible exchange rate.  Their fees are built in to their quotes,
and you simply transfer money to their account in Australia, and they pay into your US account (or vice-versa) a day or two later.

One feature they offer is a built-in alert system where you can be notified if the rate changes above or goes below specified thresholds.
Their built-in alert system was terrible, mainly because it was too slow - by the time you received a text or read an email, the rate had changed,
often significantly.

## The solution

I wanted to solve this problem by having a screen scraper log in, get a quote for an exchange rate
and make that available to me on my laptop during the day.

Below shows the final result - GROWL-style notifications popping up every 20 minutes.
This provides that flexibility to properly monitor the exchange rate.

![macox visual alerts](/images/usforex-notifications.png)

So, how did we achieve this?

# Using CasperJS as a scraper

After looking at all sorts of Java HTTP/HTML solutions like htmlclient and Selenium,
I finally settled on using headless browser technology to scrape websites.

The [CasperJS] on top of [PhantomJS] solution offers excellent full-blown WebKit
features, with the ease of a domain-specific language in Javascript.

I highly recommend grabbing [Resurrectio], a chrome extension that really helps you learn how casper works,
and make authoring scripts by example a breeze.

After installation, the Javascript flavor you author scrapers in is reasonably high level.

Full code is available at [this GitHub repository][2].

Here is a sample of the top of the scraper for us forex:

{% highlight javascript %}
var casper = require('casper').create({...});
var mouse = require("mouse").create(casper);
var fs = require('fs');
var utils = require('utils');

# Read in credentials
var config = JSON.parse(fs.read('./src/test/resources/usforex.config'));
var url = 'https://www.ofx.com/en-us/login/login';

casper.start(url, function openedLoginPage() {
    this.echo(this.getTitle());
});
...
casper.waitForSelector('#quoteDetails',
  function detailsAppeared() {
      this.echo(this.getHTML('#quoteDetails'));
      this.captureSelector("usforex.png", '#quoteDetails');
  },
  function detailsTimeout() {
      this.echo("No details - timed out.");
  },
  10000
);

casper.run();
{% endhighlight %}


# Using AppleScript for Notifications

It turns out you can create notifications from a Terminal command line,
following the instructions in [this article][1].

Armed with this knowledge, I created the following shell script that runs the scraper,
grabs the exchange rate, and displays a notification.  It does so every 20 minutes.

{% highlight bash %}
# Do this 120 times, meaning every 20 minutes for
# 6 days which is the trading window of AUD to USD
$ for i in `seq 1 120`
  do
      # Run the scraper from maven and grab the exchange rate and date
      export XCHANGE="$(date) $(mvn clean verify | grep "AUD/USD")" ;

      # Construct the notification as a string with the xchange rate
      export NTF=$(echo "display notification \"$XCHANGE\" with title \"Usforex\"") ;

      # Display the notification
      osascript -e "$NTF";

      # Wait for 20 minutes
      sleep 1200;
  done
{% endhighlight %}

[USForex]: https://www.ofx.com/en-us/
[CasperJS]: http://casperjs.org
[PhantomJS]: http://http://phantomjs.org/
[Resurrectio]: https://github.com/ebrehault/resurrectio
[1]: http://apple.stackexchange.com/questions/57412/how-can-i-trigger-a-notification-center-notification-from-an-applescript-or-shel
[2]: https://github.com/nowucca/progmetrix
