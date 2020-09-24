---
layout: post
title: Testing XSRF and SameSite-Strict cookies
date: 2020-09-17 13:24:35 -0800
comments: true
---

# Testing XSRF and SameSite-Strict cookies

For my `$day-job`, we have to take security pretty seriously.  There is not much hope holding out for "security via obscurity" when you work for Netflix.

Every now and then a class of security issue arises that means you need to determine what happens when your site is wrapped by an iframe, or when it is linked to on another page.

Here we are investigating what happens if a cookie is marked SameSite=Strict.
When accessed form a third party page like this page, be it top level navigation/click or an iframe on the page, we should NOT send SameSite=Strict cookies.

We request iFrame protection on our site; so iFrames are already barred from being displayed, so not cookies are sent.  Thereforethis page is a series of links only to test whether or not that is true for Netflix DVD systems.


* [Steve's Dev Box](https://satkinson-dev-100-vip.eng.dvdco.netflix.com)
* [Web CI](https://web-test-ci.eng.dvdco.netflix.com). [Web Stable](https://web-test-stable.eng.dvdco.netflix.com), [Web  RC](https://web-test-rc.eng.dvdco.netflix.com)
* [Web-Stage](https://dvd2.netflix.com), [Web-Prod](https://dvd.netflix.com)

The idea once once enabled, our SameSite=Strict cookies should NOT be sent when these links are clicked.  This will simulate what Google search results will do as well.
