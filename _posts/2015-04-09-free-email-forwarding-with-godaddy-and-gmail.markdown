---
layout: post
title:  "Setting Up Email Forwarding with a Goddady Domain to a Gmail account"
date:   2015-04-09
---

If you own a domain at Godaddy, lets say `mycustomdomain.com`, you can actually set up to 100 email addresses at that domain as free forwards to a real email storage service, such as gmail.

So let's imagine we are setting up `newemail@mycustomdomain.com` forwarding to `myoldemail@gmail.com.`

# Steps

1. **Set up Goddady Email Forwarding**: Using Godaddy's [helpful email forwarding page][godaddy-email-forward-help] you should be able to create email addresses and MX records in your customer domain.  This took about 15-20 minutes to finish setting up completely after the MX records were set.

2. **Enable Google 2 Step Verification**: While you are waiting, you will need to turn on [2-step verification][gmail-2step] on your `myoldemail@gmail.com` account.

3. **Teach Gmail How to Receive and Send Custom Email**: Thanks to a very helpful [blog post with screenshots][gmail-blog-post], you can then
*  set up your gmail account as a place to receive the emails from newemail@mycustomdomain.com, and
* set up your gmail account as a place to respond to newemail@mycustomdomain.com using that identity.

Hope this helps.

[godaddy-email-forward-help]: https://support.godaddy.com/help/article/7598/setting-up-forwarding-accounts-in-the-workspace-control-center
[gmail-2step]: https://www.google.com/landing/2step/
[gmail-blog-post]: http://ellisbenus.com/web-design-columbia-mo/workaround-using-gmail-alias-forwarded-email-addresses/
