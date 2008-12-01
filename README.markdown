# DryDrop

Dropping static web sites with love (for git lovers)

* DRY principle
* zero cost (thanks to [Google App Engine][appengine])
* zero maintenance (thanks to [GitHub][github])
* NO Python knowledge needed
* NO ponies included!

# How it works

- upload your static files to github project (easy step)
- generate drydrop scaffold site and deploy it to appspot (easy step)
- setup post commit hook in github project pointing to your drydrop site (easy step)

From now, every change pushed to github project will automatically propagate to your static site hosted by Google.

Pretty cool, huh?

# Current State

In planning, but some code exists. I need this for myself, so expect first version soon.

# Support

### Bugs / Feature requests
[The support forum is here][support].

## Issues filled in GAE

* [Hook into admin section][gae-admin-hook]

### IRC
IRC channel [#drydrop][irc] at freenode

# History

  * v0.1 (to be released) 
    * public alpha release

[appengine]: http://code.google.com/appengine
[github]: http://github.com
[homepage]: http://github.com/woid/drydrop
[contact]: mailto:antonin@hildebrand.cz
[workaround]: http://getsatisfaction.com/xrefresh/topics/unable_to_download_rainbow_for_firebug
[support]: http://drydrop.uservoice.com/
[irc]:irc://irc.freenode.net/#drydrop
[gae-admin-hook]:http://code.google.com/p/googleappengine/issues/detail?id=893