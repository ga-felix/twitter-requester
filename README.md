## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Modules](#modules)
* [Setup](#setup)

## General info
This software extracts data from Twitter and populates
a MySQL database. Therefore, the database is used to
create a network (graph) that can be used later for
research.

## Technologies
Project is created with:
* Python: 3.6
* MySQL Workbench: 8.0
* Networkx: 2.5.1
* pymysql: 1.0.2

Python, MySQL and mentioned python modules are
all requirements to run this software. 

## Modules
The software consist of these following modules,
all of them storaged on 'src' folder:
* extractor: extracts data from Twitter.
* database: populates SQL database.
* api: performs Twitter API calls.
* reporter: generates the graph.

'settings' and 'interface' modules are still
being created.

All database or Twitter API errors are reported
to 'logs' folder.

## Setup
To setup this project just run 'install' file,
available on root directory:

```
$ cd ../twittery
$ sudo pip3 install -r requirements.txt
```

Also, the 'twitter/src/api/keys' directory should 
contain a 'keys.json' file, which must have a
bearer token acquired on Twitter Developer Portal.
If you don't have a bearer token, click [here](https://developer.twitter.com/en/docs/authentication/oauth-2-0/bearer-tokens).
'keys.json' example:

```
{
  "twitter_acess_your_name": {
    "bearer_token": "YOUR_BEARER_TOKEN_HERE"
  }
}
```

The software can handle multiple keys.