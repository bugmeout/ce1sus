0.11.X is still Under Development

#ce1sus

ce1sus is a threat information database.

When the development of ce1sus started there were not many tools available to store Indicators of compromise (IOCs) available.
Moreover the shared IOCs were received in many different formats, and often there was no real context given.  

ce1sus has the goal to facilitate:

1. Central database: Storing any information around all kinds of threats (i.e. scam, malware, phishing, ...). in a structured manner 
2. Sharing: Be compatible with open standards (STIX/CybOX) / or the most commonly used formats to facilitate the sharing trusted partners
3. Automatized Import/Export: Synchronization of instances between trusted partners
4. Ease of use: Generate information out of the obvious automatically (i.e. hashes, parsing of email headers, etc)
5. Correlation: Automatically creating relations between seen threats
6. Visualization: Represent the real-life case as closely as possible

The structure of a threat provides context to others with nearly no efforts. An Example 

Example:
Email with a malicious attachment

In such cases the event should start with an email object. 
That object can then have all the attributes (i.e. email_from, email_body, ...) required to represent an email. 
This object will then get a child object representing the attachment. 
If this file is just a dropper, then the dropped file should be a child of the previous object and so forth.

For this scenario one can directly deduce that then a child file was found that it is highly probable that the file came from this specific dropper
and if the dropper file was not found one at least knows that the cases are related.  

Such structures improve the understanding of how the different attributes are related, and leads to a better overview on the relationship between events.

##Note

There are several branches, which are primarily used for development the master branch will be the release which is considered as stable

This is still not the final release, we are still developing ce1sus.

For any questions feel free to ask

##Features

* Creates relations between events through their attributes
* Stores and presents the event in a structured manner
* Different levels of sharing
** Events can be shared with groups
** Attributes can be shared on desired basis
* Easy maintenance
* Flexible configuration and taxonomy
* Easy installation
* Completely open source
* Search
* STIX Compatible (Currently supports Observables, Indicators, Markings, Kill-Chains)
* Completely interfaceable (REST API)
* Can be used without the graphical web interface
* Attribute handlers which can enrich your attribute
* Genuine MISP v2.x integration of push/pull requests
* CybOX naming convention
* Synchronization between ce1sus instances
* Web-interface sync-server management (MISP and ce1sus)
* Mail notifications
* Attributes/Objects/Observables additionally can be shared via TLP level


##Requirements

- python
  * python (2.7+)
  * SQLAlchemy (0.7.8+)
  * mysqldb (1.2.3)
  * python-magic (0.4.6+)
    ** https://github.com/ahupp/python-magic
  * python-ldap (2.4.10+) (optional)
  * dateutil (1.5+)
  * cherrypy3 (3.2.2+)
  * memcache
  * rtkit (optional)
  * gnupg (0.3.5+)
  * eml_parser (https://github.com/sim0nx/eml_parser/
- MySQL (5.1+)
- Nginx (1.4+)
- uWSGI (1.2.3+, with python-2 support)
- memcached

##Roadmap

###v0.11.1

* Relation of attributes can be done over groups of attributes

###v0.11.2

* TAXII server integration


##Up the road 0.11.x

* Profile management
* More handlers
* Improved search
* Export of events (i.e. CSV)
* Enhanced STIX/CybOX support
* Show statistics on Home page
* Password protection for compressed files

##Installation

 
For the installation please refer to the Documentation files

##Remarks


For any questions feel free to ask.
