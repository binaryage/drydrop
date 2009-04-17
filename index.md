---
title: DryDrop
layout: wikistyle
repo: http://github.com/darwin/drydrop
support: http://github.com/darwin/drydrop/issues
download: 
version: To be released
---

Dropping static web sites on Google App Engine with love (for git lovers)

* DRY principle
* zero cost (thanks to [Google App Engine][appengine])
* zero maintenance (thanks to [GitHub][github])
* NO Python knowledge needed

# How it works

- upload your static files to github project (easy step)
- generate drydrop scaffold site and deploy it to GAE (easy step)
- setup post commit hook in github project pointing to your drydrop site (easy step)

Since then, every change pushed to github project will automatically propagate to your static site hosted by Google.

# Current State

In planning, but some code exists. I need this for myself, so expect first version soon.

# Support

### Bugs / Feature requests

* [The support forum is here][support].

### Issues filled in GAE

* [Hook into admin section][gae-admin-hook]

# History

  * v0.1 (to be released) 
    * public alpha release

[appengine]: http://code.google.com/appengine
[github]: http://github.com
[homepage]: http://github.com/darwin/drydrop
[contact]: mailto:antonin@hildebrand.cz
[workaround]: http://getsatisfaction.com/xrefresh/topics/unable_to_download_rainbow_for_firebug
[support]: http://drydrop.uservoice.com/
[gae-admin-hook]:http://code.google.com/p/googleappengine/issues/detail?id=893