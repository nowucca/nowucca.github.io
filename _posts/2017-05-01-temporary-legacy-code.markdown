---
layout: post
title:  "Code cleanup using temporary legacy code"
date:   2017-05-01 
---

When working with older code, there are times when you will build a new solution, and gradually need to switch over 
to that new solution.  However for fallback purposes, you still need the old code to be runnable in the same runtime.

In this post I'll show one strategy for handling temporary legacy code - that code you want to kill off but that needs to 
hang on until the newer solution is proven worthy in production.

Let's say you have some legacy code to choose some books to show customers when they are thinking of leaving your bookstore:

{% highlight java %}
        List<Integer> validBooks = new ArrayList<>(ContentQueries.getNonMemberNewReleasesBooks(maxBooks));
        // filter out books that we've already seen
        if (Customer.isDiscMember(customerId)) {
            final BookFilterSet filterSet = FilterSetManager.DONT_CANCEL_FILTER;
            filterSet.filterBooks(validBooks);
        }
{% endhighlight %}

Now perhaps it makes more sense to have a separate server to calculate this data.
Architecturally, let's assume it makes more sense to gather this data from a middle-tier REST server,
which is on the whole responsible for choosing lists of books for many other reasons already.
Besides, maybe we are also hitting a database directly here - better to use a middle-tier server if our site 
is large enough.

The basic idea is to centralize all the legacy code into a single class, called "TempLegacyCode".
This class owns any "switches" or "flags" to control the use of the old or new code, together with all the old code.
All the old code gets placed into  methods prefixed with "legacy" in their names.
(the effort it takes to refactor the old code into new legacy methods is the upfront cost involved in the strategy)

In this case, we can now rewrite the code snippet above as:

{% highlight java %}
        if (TempLegacyCode.USE_REMOTE_NEW_RELEASE_BOOK_CALL.enabled()) {
            validBooks = NewClient.getInstance().getNewReleaseBooks(customerId, maxBooks);
        } else {
            // Note that we move the old code inside TempLegacyCode if we can do so easily
            // ...less to clean up later.
            validBooks = TempLegacyCode.legacyGetNewReleasedBooks(customerId, maxBooks);
        }
        ...
{% endhighlight %}


So after a while, as long a USE_NEW_CALL has been true in production for a while, we are in good shape.

Why?  Because now when it comes time to remove all the legacy code, 
you can do a usage search on the class "TempLegacyCode" and be sure that 
all the old code is very easily removed - the switch and the call to the legacy method are killed, yielding:

{% highlight java %}
            validBooks = NewClient.getInstance().getNewReleaseBooks(customerId, maxBooks);
{% endhighlight %}

as if the code always existed that way.

