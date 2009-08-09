---
title: DryDrop
subtitle: deploy GAE sites by pushing to GitHub
layout: product
icon: /shared/img/drydrop-icon.png
repo: http://github.com/darwin/drydrop
support: http://github.com/darwin/drydrop/issues
downloadtitle: Install v0.2
download: http://github.com/darwin/drydrop
downloadboxwidth: 120px
donate:
subdownload: 
subdownloadlink:
mainshot: /shared/img/drydrop-mainshot.png
mainshotfull: /shared/img/drydrop-mainshot-full.png
overlaysx: 1109px
overlaysy: 856px
overlaycx: 25px
overlaycy: 10px
---

<div class="advertisement">
	<div class="plug">Recommended reading:</div>
	<a href="http://www.amazon.com/gp/product/0596009259?ie=UTF8&tag=firepython-20&linkCode=as2&camp=1789&creative=9325&creativeASIN=0596009259"><img border="0" src="/shared/img/amazon/41QbTFszYTL._SL110_.jpg"></a><img src="http://www.assoc-amazon.com/e/ir?t=firepython-20&l=as2&o=1&a=0596009259" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />
	
	<a href="http://www.amazon.com/gp/product/0596158068?ie=UTF8&tag=firepython-20&linkCode=as2&camp=1789&creative=9325&creativeASIN=0596158068"><img border="0" src="/shared/img/amazon/41Mu5RWG-1L._SL110_.jpg"></a><img src="http://www.assoc-amazon.com/e/ir?t=firepython-20&l=as2&o=1&a=0596158068" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />

	<a href="http://www.amazon.com/gp/product/0596007973?ie=UTF8&tag=firepython-20&linkCode=as2&camp=1789&creative=9325&creativeASIN=0596007973"><img border="0" src="/shared/img/amazon/41S-nPeF89L._SL110_.jpg"></a><img src="http://www.assoc-amazon.com/e/ir?t=firepython-20&l=as2&o=1&a=0596007973" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />
	
	<a href="http://www.amazon.com/gp/product/1430210478?ie=UTF8&tag=firepython-20&linkCode=as2&camp=1789&creative=9325&creativeASIN=1430210478"><img border="0" src="/shared/img/amazon/516STCBRnOL._SL110_.jpg"></a><img src="http://www.assoc-amazon.com/e/ir?t=firepython-20&l=as2&o=1&a=1430210478" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />
	
	<a href="http://www.amazon.com/gp/product/059652272X?ie=UTF8&tag=firepython-20&linkCode=as2&camp=1789&creative=9325&creativeASIN=059652272X"><img border="0" src="/shared/img/amazon/513CiT5BtYL._SL110_.jpg"></a><img src="http://www.assoc-amazon.com/e/ir?t=firepython-20&l=as2&o=1&a=059652272X" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />
	
	<div class="offer"><a href="mailto:antonin@binaryage.com">advertise here</a></div>
</div>
<script type="text/javascript" src="http://www.assoc-amazon.com/s/link-enhancer?tag=firepython-20&o=1">
</script>

## Features

#### Host your static site on Google App Engine and update it by pushing to GitHub.

* DRY principle (set it up and forget)
* Zero cost (thanks to [Google App Engine][appengine])
* Zero maintenance (thanks to [GitHub][github])
* No Python knowledge needed, but you need to know basics of Git

### How it works

It is simple. Let's say you have GitHub repo called 'my-static-site' and you want to host it on App Engine. DryDrop is an application ready to be uploaded as your App Engine project. When you upload it first time, you should setup post-receive hook in your GitHub repo to point to your App Engine project, so every change you push to GitHub can be reflected on your App Engine site immediately.

Let's say someone visits your App Engine site. DryDrop has a simple cache. If requested page is not in the cache, DryDrop will try to fetch it from GitHub, store it in the cache and then serve it. Next time the same URL is requested, it will be served directly from DryDrop cache.

Let's say you did some changes to your files. In the moment you push file changes into GitHub, post-receive hook will ping DryDrop and that invalidates modified files in the cache. Next request will trigger downloading of fresh files from GitHub.

## Installation

- upload your static files as GitHub repository (easy step)
- generate DryDrop scaffold site and deploy it to GAE (easy step)
- setup post commit hook in GitHub repo pointing to your DryDrop site (easy step)

#### Since then, every change pushed to github project will automatically propagate to your static site hosted by Google.

### Step 1: prepare your GitHub repository

You already know how to work with GitHub, right? 

Let's say you are user `darwin` and created repository `web-app-theme`.
So, you repository's content lives at <a href="http://github.com/darwin/web-app-theme/tree/master">http://github.com/darwin/web-app-theme/tree/master</a>

### Step 2: create your App Engine project and upload DryDrop

I've created project called `drydropsample` like this:

<a href="/shared/img/drydrop-create-app.png"><img src="/shared/img/drydrop-create-app.png" width="300"></a>

Then I have to download latest DryDrop and upload it to my project:

    git clone git://github.com/darwin/drydrop.git
	cd drydrop
	rake upload project=drydropsample
	
Of course, don't forget to replace project name with name of your GAE project.





## FAQ

#### Do I need to understand Python to use this?
> Not at all. You just need to know how to use Git and how to create App Engine project on appspot.com.

#### How does DryDrop compare to <a href="http://pages.github.com">GitHub Pages</a>?
> GitHub Pages is solving same need of "live-hosting of GitHub repository as a static site on custom domain". I've started this project before GitHub Pages was announced and GitHub pages made it somewhat obsolete, especially because they support <a href="http://github.com/mojombo/jekyll/tree/master">jekyll</a>. But I still see two valid use cases: 1) you have public repo and you don't want to pay for CNAME support on GitHub 2) GitHub had some performance issues recently, App Engine works more reliably (this may be fixed in the future)

#### How can DryDrop serve files from GitHub?
> It is simple. DryDrop has a simple cache. If requested page is not in the cache, DryDrop will try to fetch it from GitHub, store it in the cache and then serve it. Next time the same URL is requested, it will be served directly from DryDrop cache. Let's say you did some changes to your files. In the moment you push file changes into GitHub, post-receive hook will call DryDrop and DryDrop will invalidate modified files in the cache. 

## History

  * **v0.2** (09.08.2009) 
	* initial public version

  * **v0.1** (internal alpha) 

[appengine]: http://code.google.com/appengine
[github]: http://github.com
[homepage]: http://github.com/darwin/drydrop
[contact]: mailto:antonin@hildebrand.cz
[workaround]: http://getsatisfaction.com/xrefresh/topics/unable_to_download_rainbow_for_firebug
[support]: http://drydrop.uservoice.com/
[gae-admin-hook]:http://code.google.com/p/googleappengine/issues/detail?id=893