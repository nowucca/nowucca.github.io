---
layout: post
title:  "Setting Java Home for Centos and Ubuntu Systems"
date:   2017-05-01 
---

Here is a shell script designed to work on Centos and Ubuntu, to establish
the JAVA_HOME and JRE_HOME variables.

Some of the requirements were that for Centos 5, we default to /usr/bin/java,
and for Centos 6 we should default to whatever the alternatives java link points to.

It will work for Ubuntu as well, perhaps with some extension.

UPDATE: the old script failed on Centos 7 - this fixed it.

{% highlight bash %}


function readDistributor()
{
    if [ -x /usr/bin/lsb_release -a -x /usr/bin/awk ]; then
       echo $(/usr/bin/lsb_release -i | /usr/bin/awk '{print $3}');
    else
       echo "Unknown_Distributor" # by default
    fi
}

function readOSVersion()
{
    if [ -x /usr/bin/lsb_release -a -x /usr/bin/awk ]; then
       echo $(/usr/bin/lsb_release -r | /usr/bin/awk '{print $2}');
    else
       echo "0" # by default
    fi
}

function setFallbackJavaJreHome()
{
    JRE_HOME=/usr/bin/java
    JAVA_HOME=$JRE_HOME
    echo $1
    echo "WARNING: Using fallback java default JAVA_HOME=$JAVA_HOME"
}

function establishJavaHomeVars()
{
    # Will be reading JAVA_VERSION from /etc/sysconfig/environment
    # default to system default (Java 6 on Centos 5.x, Java 7 or 8 on Centos 6.x)

    local DISTRIBUTOR=$(readDistributor)
    local OS_VERSION=$(readOSVersion)


    case "$DISTRIBUTOR-$OS_VERSION" in
       CentOS-5*)
		if [ $1 ] && [ $1 = "7" ] && [ -d "/usr/lib/jvm/jre-1.7.0" ] ; then
		    JRE_HOME="/usr/lib/jvm/jre-1.7.0"
		else
		    JRE_HOME=/usr/java
		fi
		JAVA_HOME=$JRE_HOME
                ;;

       # Centos 6.x java home settings, expect alternatives is set up
       CentOS-[67]*)
		JAVA_ALTERNATIVES_HOME="$(readlink -f /usr/bin/java | sed s:/bin/java::)"

		if [ ! -z $JAVA_ALTERNATIVES_HOME ]; then
		    JRE_HOME="$JAVA_ALTERNATIVES_HOME"
		    JAVA_HOME=$JRE_HOME
		else
		    setFallbackJavaJreHome "Missing expected directory: /usr/bin/java"
		fi
                ;;

       # Default settings for any other strange environments
       *)
                setFallbackJavaJreHome "Unknown OS/Version: $DISTRIBUTOR / $OS_VERSION"
                ;;
    esac
}

establishJavaHomeVars "$JAVA_VERSION"

export JAVA_HOME
export JRE_HOME
{% endhighlight %}
