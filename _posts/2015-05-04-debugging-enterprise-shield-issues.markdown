---
layout: post
title:  "Debugging Issues with Enterprise Shield™"
date:   2015-05-04
---

When I worked at Kaazing, I wrote the first implementation of their [Enterprise Shield™][enterprise-shield-doc] (a.k.a reverse connections) feature for the networking gateway.
Being the first implementation, I will be first to admit that it was the one with ALL the bugs.  Fortunately Kaazing's automated testing regime is still the best I've seen for their class of products.
So I was thinking back to a set of related issues that were discovered during the early adoption phase of that feature, and thought they might make interesting reading.

* TOC
{:toc}

## What is Enterprise Shield™?

The essential idea of the "Enterprise shield™" is to close all incoming ports on a firewall, protecting the internal network from direct access through any port.
To do this, we install a gateway server outside the firewall in the DMZ, and one internal gateway server inside the DMZ.  The DMZ gateway accepts connections from real clients, but simply queues up the connection requests as they occur.  The internal gateway is configured to reach out in "reverse" to the DMZ gateway, to "pick off" the pending connections from real cients and form a collection of connections through to the internal network.

<img src="http://developer.kaazing.com/documentation/jms/4.0/images/f-dmz-trustednetwork-860-02.png"/>
(image owned by kaazing.com, used for reference purposes only)


Now there were a myriad of practical concerns with this feature.  (See the [Kaazing documentation][enterprise-shield-doc] for more details as to how these concerns are configurable.)

* **Firewalls killing idle connections**: Established connections from the internal to the DMZ gateway had a keep-alive mechanism deployed (not tcp-keepalive which was not supported on all customer's machines) to detect situations where the TCP connection was closed or half-closed.  In those situations the connection was shut down and an attempt was made to re-establish a connection.

* **Handling instant-on client connection demands**: Some applications will have many connections being established to the DMZ gateway when the system is brought online. It was possible to pre-prepare a large number of pending connections on the DMZ gateway, to "warm up" a large number of connections in the case where one expected a thundering herd of real-world clients to need access to the system immediately.  This tricked the internal gateway into repeatedly reaching out in reverse to consume all the "warm up" connections.

* **Gateway Deployment sequence**: the system should be designed to work with front-back or back-front deployments.  To support starting the internal gateway before the DMZ gateway, we made the internal gateway attempt to connect to the DMZ gateway with a capped exponential backoff in case the DMZ gateway would not start up.

* **Layered protocol approach**: to establish a connection between the internal and DMZ gateways, we used the SOCKS protocol on top of the TCP protocol to do a remote BIND from the internal gateway to the DMZ gateway.  Once the BIND is satisfied with the arrival of a client connection, the SOCKS handlers on the internal gateway received the BIND SUCCESS message and disappeared. At this stage a plain TCP connection is established. If the DMZ gateway was configured to connect over a specific protocol (e.g. WebSockets)  then a regular handshake (e.g. an HTTP request)  to establish the next protocol (WebSocket) would take place.

Having solved all of those issues in the initial implementation, we discovered a larger symptom....

## The Presenting Symptom

The stable state of the system was a collection of prepared connections between the internal and DMZ gateways, with an extra SOCKS remote bind request pending, waiting for any additional clients to arrive.

				+----------+                  +--------------+
				|          | <--(socks)------ |              |
				|          |                  |              |
				| dmz      | <--(prepared)--> | internal     |
				|          | <--(prepared)--> |              |
				+----------+                  +--------------+

Having taken care of all these concerns, we were faced with this challenge: **On very slow virtual machines, running Ubuntu, we were never reaching the stable state.  We would thrash, and would continue building and tearing down both the SOCKS and the prepared WebSocket connections.**

Recreating the same Ubuntu version on a VirtualBox machine and throttling the CPU fortunately reproduced the same errors.
Here's the issues that we encountered.

### Issue 1: Coalesced Buffers with Multiple Protocols

The virtual machine was slowing down TCP writes to the point they were coalesced into a single buffer. The DMZ
machine was sending the final SOCKS response and the HTTP websocket handshake in a single buffer.
The internal machine was receiving an IO buffer with content from multiple protocols.

    { <socks-response-bytes><http handshake bytes> }

The problem was, as soon as our decoder finished decoding the final SOCKS message, we removed the Codec
from the filter chain.
That means we were never delivering the HTTP handshake bytes, and so we were tearing down the connection.
We had seen this issue before for WebSocket handshakes when the same packet might have 101 and the first WebSocket frame, e.g.

    { <http-101-response><web-socket-frame> }

Effectively, when we know we are at the end of the conversation, we need to write any extra content buffer to the
decoder "out" product (using Apache Mina's codec conventions):

{% highlight java %}
    private boolean decodeCommandResponse(IoSession session, IoBuffer in,
                                          ProtocolDecoderOutput out) throws
            Exception {
        ...
        session.setAttribute(DECODER_STATE_KEY, state);
        // Make sure we flush any data present in the buffer after the
        // SOCKS connection is made, and before this filter is removed from the chain.
        if (state == DecoderState.CONNECTED) {
            decodeExtraContentBuffer(in, out);
        }
        return true;
    }

    static boolean decodeExtraContentBuffer(IoBuffer in, ProtocolDecoderOutput out)
            throws Exception {
        if (in.hasRemaining()) {
            out.write(in.duplicate());
            in.position(in.limit());
        }
        return true;
    }
{% endhighlight %}

### Issue 2: Dispatching with Coalesced Buffers

As before in Issue 1, the virtual machine was slowing down TCP writes to the point they were coalesced into a
single buffer. The DMZ machine was now correctly sending the final SOCKS response and the HTTP websocket handshake in a
single buffer.  The internal machine was correctly receiving an IO buffer with content from multiple protocols.

    { <0x05 remaining-9-socks-response-bytes> <47('G' for GET) remaining-http-handshake-bytes> }
    #  [buffer.position=10 tells us we should read HTTP bytes only]

We were now passing this buffer to some dispatching logic: Briefly, the dispatch filter has the job of inspecting the first byte of the buffer it sees, and tries to work out whether we are talking RTMP, HTTP, or SOCKS protocols so we know how to process the buffer.  When we were reading the first byte, we were reading always from position "0", which for coalesced buffers ended up being the 0x05 byte from the SOCKS command.

But we really wanted the 0x47 byte (G for GET) so we knew we had shifted to HTTP.

The bad and fixed code:

{% highlight java %}
// Bad code reads from position 0

  @Override
    public void messageReceived(NextFilter nextFilter, IoSession session,
                                Object message) throws Exception {
        IoBuffer buffer = (IoBuffer) message;
        int discriminator = buffer.get(0) & 0xff;
    }

// Good code is smarter for coalesced buffers.

    @Override
    public void messageReceived (NextFilter nextFilter, IoSession session,
            Object message)throws Exception {
        IoBuffer buffer = (IoBuffer) message;
        int discriminator = buffer.get(buffer.position()) & 0xff;
    }
{% endhighlight %}

### Issue 3: Being Too Idle

Now our SOCKS connections were stable, but we were still thrashing our prepared connections.

The last issue was a race condition whereby if we enabled WebSocket ping/pong as a keep-alive mechanism every 10 seconds or
so, we would become unstable, even with other fixes.  The problem was that if the PONG came back really fast, just after the PING, we did not "see" it and we then thought the session became IDLE, and we closed the WebSocket connection.
THe fix was to avoid the race condition by making it impossible to receive a PONG for the session before we expected to.  This explained why prepared connections were thrashing.



## Takeaway thoughts

* Sometimes you have to dig in and set up reproducible environments carefully.
* Wireshark was of great assistance in proving that TCP writes were being coalesced
* Sometimes solving one issue exposes another, and another.  Perseverance through multiple solutions is not often the norm, but is sometimes required.
* It can be valuable to think about the crazy overloaded VM environments your software can be deployed upon during quality control.

## For More Information about Kaazing

If you are interested in the Kaazing Gateway and the Enterprise Shield features, head on over to:

* the [open source community edition of the Kaazing WebSocket Gateway][kaazing-org],
* download the free fully functional version of the [commercial Kaazing WebSocket Gateway](http://developer.kaazing.com/downloads/)  or
* browse the [documentation explaining Enterprise Shield][enterprise-shield-doc].

[enterprise-shield-doc]: http://developer.kaazing.com/documentation/5.0/reverse-connectivity/o_rc_checklist.html
[kaazing-org]: http://kaazing.org/
