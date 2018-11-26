---
layout: post
title:  "How to set up a basic webapp using Digital Ocean"
date:   2018-11-25
comments: true
---


 

Prerequisites: a rough understanding of the command line and you have used ssh before.

 

So if you are interested in setting up a web application on a cloud machine from scratch, I have set up https://www.simpleaffablebean.org on my own Digital Ocean cloud machine.

 

 

* What is Digital Ocean?

 

Digital Ocean is an online cloud provider, simpler to use than Amazon Web Services or Google Cloud Platform.

You can sign up for them at do.co/twit (for a free $100 credit, should last 20 months if you choose the cheapest server).

 

When you sign up, you get to choose specifications for your "droplet" (aka your cloud box).

Choose an Ubuntu 16.04 server for now (I should choose 18.04 eventually but it's not a great idea to go so close to the bleeding edge).

 

We can now work through a series of excellent documentation pages.

 

* [Initial Server Setup with Ubuntu 16.04](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-16-04)

    - How to login as root
    - How to create a new user
    - Assign the new user root privileges
    - Add public key authentication so you can login using ssh keys
    - Disable Password Authentication so only the ssh key holder can access the machine
    - Login, Set up a basic Firewall

 

* [How To Install Apache Tomcat 8 on Ubuntu 16.04](https://www.digitalocean.com/community/tutorials/how-to-install-apache-tomcat-8-on-ubuntu-16-04)
    -    Install Java
    -    Create a "tomcat" user
    -    Install Tomcat (in /opt/tomcat)
    -    Update Tomcat permissions
    -    Create a systemd Service File
    
         Note: To save memory, I used the following instead of that suggested:
        `Environment='CATALINA_OPTS=-Xms512M -Xmx512M -server -XX:+UseParallelGC'`
            
    - Adjust the Firewall and Test the Tomcat Server
    - Configure Tomcat Web Management Interface
    - Access the Web Interface

 

* [UFW Essentials: Common Firewall Rules and Commands](https://www.digitalocean.com/community/tutorials/ufw-essentials-common-firewall-rules-and-commands)
    - I only allowed the following services:

      * Allow SSH        
      * Allow All Incoming HTTP, HTTPS  
      * Allow MySQL  (`sudo ufw allow 3306`)

 

* [Forwarding Ports 80, 443](https://serverfault.com/questions/238563/can-i-use-ufw-to-setup-a-port-forward)
    -    We have 8080 and 8443 open
    -    We need to tell the firewall to forward traffic from ports 80, 443 to 8080, 8443
    -    This is a little complex and it took me a while to find it (see link above).
        In case the link goes away, we need to edit /etc/ufw/before.rules before the filter section, right at the top of the file

        *nat
        :PREROUTING ACCEPT [0:0]
        -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
        -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 8443
        COMMIT

* [Install MySQL 8.0 On Ubuntu 16.04](https://websiteforstudents.com/install-mysql-8-0-on-ubuntu-16-04-17-10-18-04/)
    - Use a REALLY STRONG root password since we are exposing port 3306 directly.  I'd suggest a password tool like LastPass or Password1 or Dashlane should be used to generate a password, and it can be 24 characters or more long too.
    - Create a user
    
           mysql> create user 'yourDatabaseUserName'@'%' identified by 'yourStrongDatabaseUserPassword';
            
    - Create a database
    
            mysql> create database YourDB;
            mysql> grant all privileges on yourDatabaseUserName.* to 'YourDB'@'%';
            
    - Populate the Database
    
         * Connect using IntelliJ from your laptop to your database using the Database tool.  
         * Run the schema creation to create the tables and the sample data  
         * For me, I had these in `/src/main/db/tables.sql and src/main/db/data.sql.`

 

 

* DNS and Troubleshooting
     -    [Troubleshooting SSH Connectivity](https://www.digitalocean.com/docs/droplets/resources/troubleshooting-ssh/connectivity/): if you get into trouble being able to access your droplet.
     -   Using your own hostname (like simpleaffablebean.org) if you want to, otherwise stick with the raw IP address for now.
     
           * [An Introduction to Managing DNS](https://www.digitalocean.com/community/tutorial_series/an-introduction-to-managing-dns)           
           * [How to Point to DigitalOcean Nameservers From Common Domain Registrars](https://www.digitalocean.com/community/tutorials/how-to-point-to-digitalocean-nameservers-from-common-domain-registrars)
           * [How To Set Up a Host Name with DigitalOcean](https://www.digitalocean.com/docs/networking/dns/)

 

* Deploy Your Application
    -  On your laptop, update context.xml to use:
    
            <?xml version="1.0" encoding="UTF-8"?>
            <Context path="/">
                <Resource name="jdbc/YourJDBCName" auth="Container" type="javax.sql.DataSource"
                          maxTotal="5" maxIdle="2" maxWaitMillis="10000"
                          username="yourDatabaseUserName" password="yourStrongDatabaseUserPassword"
                           driverClassName="com.mysql.cj.jdbc.Driver"
                          removeAbandonedOnBorrow="true" removeAbandonedOnMaintenance="true"
                          removeAbandonedTimeout="60" logAbandoned="true" timeBetweenEvictionRunsMillis="300000"
                          url="jdbc:mysql://yourDropletIP_Or_HostName:3306/YourDB"/>
            </Context>
    
   - Build Your WAR File on your laptop
            `gradle clean build war -x test`
            
   - Deploy your WAR file to the Tomcat on your Droplet
   
     * Copy YourBookstoreFinal.war from your laptop to /opt/tomcat/webapps on your droplet  
     * Log on to your droplet  
     * Restart tomcat `systemctl restart tomcat`  
     * Go to https://yourDropletIP_Or_HostName/  
     * Hopefully see your web page!

 

That's all I learned from setting up www.simpleaffablebean.org, I hope you are as lucky.

 
