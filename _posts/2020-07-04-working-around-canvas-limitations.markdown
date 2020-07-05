---
layout: post
title:  "Working Around Canvas LMS HTML Limitations"
date:   2020-07-04
comments: true
---

The [Canvas learning management system](https://www.instructure.com/canvas/) lets instructors (among MANY other things) create assignments.

However, you do not have access to CSS styles within the assignment "HTML" editor.  This means you are seemingly stuck with styles baked into the editor.

Well folks after 3 years I finally spent an hour or two solving this issue.

There is a [community article](https://community.canvaslms.com/thread/39026-embed-css-in-canvas-page) asking about this, and from the many helpful comments I have managed to have Canvas content the way I want it.

Let me share the steps I use to publish some HTML with style into Canvas.

Let's assume you can geenrate some HTML, maybe with an external style.

## Remove and Import External Style Sheets into HTML

 **Copy styles into the `head`**.  Make sure any external style files are included in the `<head>`.

So instead of this:
```html
<head>
  <link rel="stylesheet" type="text/css" href="css/style.css" />
  ...

```

I copy the contents of the external style sheet into the head:
```html
<head>
  <style>
  .. paste in your style definitions here ..
  </style>
```

## Use a style inliner tool to inline the style rules

I use an [inliner tool](https://www.campaignmonitor.com/resources/tools/css-inliner/) to put style rules all through my document, making it unreadable.

This is really the key to how this all works.  An inliner tool systematically applies EVERY style rule from the `head` onto **each** element of your HTML.  It winds up looking awful as text but rendering nicely in a browser.

For example:
```html
<h2 style="font-weight:normal;color:blue;font-size:2em;margin-bottom:0.75em;margin-top:1.2em;" >Professional web designer&#39;s bookstore</h2>
....
```

## Paste into Canvas

For use inside Canvas, change the `<body>` tag the inliner tool produces, and make it a `<div>`.

Paste the `<div>` into Canvas.

## Fixing Broken Image Link.

Your images will appear as broken links perhaps if you had your own images along witht he external style sheet.

No matter - use the Canvas editor to select each broken image link.  In the editor toolbar click "Embed Image" and choose the "Canvas" tag.  This allows one to systematically upload each image in order from my assignment folder on disk into Canvas.  As you define each image you can resize it if needed and provide an alt tag for students requiring that.

This is an effective quick way to fix all the broken images by uploaded them from your server - not so bad only a little clunky.

Use Canvas' Rich text editor to touch up any last minute changes.

<br>
And publish your assignment!

---
<br>
<br>

### Post script: Create your HTML in the first place

I use [Ulysses editor](https://ulysses.app/) for creating assignments.  It lets me write elegant markdown, add images and shares notes across devices.

Ulysses lets you create your own styles (I forget this but go to `Ulysses | Preferences | Styles` to copy and edit styles in your editor.  I created one specifically for Canvas with nice blue headers and 0% margins since we need all the space we can get.

Then I export my assignment using that style to HTML.

