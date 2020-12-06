---
layout: post
title: Single Page Application vs Multi Page website, when to use which?
date: 2020-12-05 16:30:30 -0800
comments: true
---

# Single Page Application vs Multi Page website, when to use which?


![Single Page, Multi-Page and Multi-Apps](/images/spa-article-logo.png "spa-article-logo")

How do we know when to implement as single page application (SPA) vs Multi page application (MPA). Are there factors that help clearly determine when to use one or the other?

The short answer is: Use an SPA for a blog or small site, use an MPA for each business unit or small business, and use multiple separate web applications (MWA) for larger organizations.

# What's wrong with an SPA?

![](/images/spa-spa.png "spa-spa"){: width="200" }

For a larger system, it does NOT work well if we use an SPA, due to two main issues:
(1) If we have user roles such that the page structure or style varies for different user roles, managing that in code with v-if or conditional styles becomes error prone (people seeing links they shouldn't) tedious or hard-to-read-and-follow-for-the-next-poor-developer.
(2) There becomes a point at which too much code is in one application, and folks want to change bits at different times.  Techniques such as webpack entry points and modularising the Vuex store delay this pain, however it comes if your business grows.

# How is an MPA Better?

![](/images/spa-mpa.png "spa-mpa"){: width="200" }

An MPA solves the first of these pain points by allowing the separate pages to have separate styles, routes etc.  One can wrap passwords/security around paths to restrict access as required, and one can allow shared Javascript modules to exist, so that common functionality across roles (e.g. price filtering) can be shared across page-types. But pain point (2) can loom large still: it isn't easy to push just PART of an MPA site.

## Thinking about A Mini-Bookstore as an MPA

For example: if we made a small bookstore site using an MPA, one might have customer-facing pages and order fulfillment/administration sets of pages.

The customer-facing pages may well have a "shopping cart" concept.
The administration pages may have the notion of "current order".
Some code could be shared between these pages (such as price filtering).

One would likely split our shared client store (e.g. Vuex)  into "consumer" and "fulfillment" modules to house this different data.


# Multiple Web Applications (MWA)

![](/images/spa-mwa.png "spa-mwa"){: width="200" }

However, some organizations are large enough to have two or more separate business units, each needing their own websites.
An MPA is too restrictive at that time since each business unit wants to update their site at the same time in different ways.
At that point you need multiple web applications, each of which could be an SPA or an MPA.

Shared data if any could live in a shared database behind the scenes, but each application would use that data differently.

## Netflix as an MWA example

I'm going to take blog.dvd.netflix.com, dvd.netflix.com and www.netflix.com as examples here.

* [blog.dvd.netflix.com](#)(http://blog.dvd.netflix.com) COULD be considered an SPA (It's just a static blog site run on Squarespace right now)
* [dvd.netflix.com](#)(https://dvd.netflix.com) is an MPA run by the DVD division.  It is an MPA with 4 SPAs (non-member app, signup flow app, member browsing app and account management app).
* [www.netflix.com](#)(https://www.netflix.com) is an SPA run by Netflix streaming UI team.  I think it's an SPA at least - they are quite fancy and unload items etc with a custom framework that supports multiple teams and assembles the SPA.

The dvd and www netflix websites share data about accounts, billing and movie data and more, but that's all via access to shared data sources.   Each website has it's own API service (separate) and separate website clients.  Truly they are two websites, with a similar but-not-identical look and feel.


# Conclusion

Use an SPA when you are faced with one set of pages and a simple site or prototype.

Switch to an MPA when you need to support different types  of user-roles or user-activities in your web application, but are deploying all of them on the same release cycle.

Use multiple web applications (MWA) when you have separate teams working on different problems, perhaps with shared data, for the same business entity.