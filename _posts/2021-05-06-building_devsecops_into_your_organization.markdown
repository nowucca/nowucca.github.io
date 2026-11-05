---
layout: post
title: Building DevSecOps into your Organization
date: 2021-05-06 12:47:20 -0800
comments: true
---

# Building DevSecOps into your Organization

DevSecOps is an operations term that integrates security into a continuous deployment model for software. My colleague Jimmy Sanders has a [great interview (text and video) here](#)(https://www.secureworldexpo.com/industry-news/devsecops-methodology-dev-sec-ops) explaining what that term means.

If you were starting up a modern service-based software organization today, what facilities would you need to put in place to have a functioning DevSecOps method for software deployment?

This diagram captures the general idea.
![](/images/dev-sec-ops-process.jpeg "dev-sec-ops-process"){: width="1000" }

Let us describe the components above.

* *Version control* that includes deployment descriptors (be it Dockerfiles or YAML or other things)

* *Build processing* that detects checkins and runs a build using the deployment descriptors (think Jenkins, GitHub actions, tons of other ones for different technologies)

* *Artifact Repository*: A way of storing build artifacts for use in deployments and for debugging (think Artifactory)
> > * This gives you a way of controlling where your libraries come from during a build - if you rely on public repositories (npm, maven central, whatever C# uses) during your build, that's a huge security risk.
> > * Generally you may separate testing artifacts from production artifacts - and "promote" testing artifacts when they are ready for production.

* *Multiple testing and production environments*. Your build processor then deploys to a few different environments:
> > * a stable nightly deployment for the QA team to regress (a "stable" environment)
> > * an up-to-the-minute deployment for the DEV team to integrate and catch conflicts/backwards compatibility bugs
> > * a release-candidate environment for integration testing before release
> > * a staging environment in production for testing in production without exposing new code to customers
> > * the production environment itself.

* *Standard deployment enforcement* Having a standard file layout for each deployed machine/container enforced by a system like Ansible/Puppet/Chef or even code (see Amazon's CDK).  The logs go here, these files are required here etc etc.


* *Production push tooling*. There needs to be a system to manage production deployments with QA in the loop - some folks burn past this step and do continuous deployments: I think it might work for some businesses, but it's not my default option.  (Think AWS console, Spinnaker from netflix...)
> > * You need a way to push new code to some servers only (we call this a canary) and be able to check metrics on old vs new code to see if there are regressions in response times, data, more errors etc.
> > * You need to try to minimize disruption to traffic, so this system often needs to access networking equipment for taking servers out of the mix while code deploys.

* *Operations Tooling*. Generally there's a theme of visibility and security forming operations tooling.   We need to see what is happening, and monitor for operational issues, and alert when they occur.  Bothering humans about every alert is something to avoid unless alerts are persistent for a little bit of time.

> > * *Monitoring and Alerting tools*. Every unit of deployment should have standard and custom monitors that alert when issues arise - these alerts should be tested as a matter of priority so there are few surprises.

> > * *Log Capture and Analysis tools*. For search popularity, operational metrics, canary analysis, network appliance logs, and business intelligence among many other reasons, you'll need one or more log capture and analysis tools.  Every network Popular choices include Kibana, Splunk, and Snowflake.

> > * *Network Analysis tools*. There are systems to mirror and capture network traffic for problem analysis and forensics. When your response times vary, it can help to disprove/prove network issues. Think Extrahop or Gigamon as example companies.

> > * *Security tools*. Many load balancers and application firewalls have security features built in. Some companies run war games from outside the network and some use agents running on each host for forensics.  We worry about edge protection, application security, network security etc.

* *Data Layer Refresh* For those data stores where it is relevant, one should on a cadence refresh data from production, anonymize personal information, and install the data into the test data stores for testing. As schemas change this will ensure that developers are writing code that will work on production.

* *Tooling Updates*.  All these tools and facilities will need updates for legacy-cost and security reasons eventually.  You need to plan for a cadence for updating the build processor, artifact repository, push tooling, together with updating of operating systems/virtual machines/containers/libraries/language versions - the idea is to make the common updates repeatable as much as possible.

That covers the DevSecOps facilities in a modern service-based software organization today.
