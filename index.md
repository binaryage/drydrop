---
layout: product
title: DryDrop updates App Engine site after pushing to GitHub
product: drydrop
product_title: DryDrop
product_subtitle: update App Engine site by pushing to GitHub
download: http://github.com/binaryage/drydrop
repo: http://github.com/binaryage/drydrop
meta_title: DryDrop updates App Engine site after pushing to GitHub
meta_keywords: python,github,google,app engine,binaryage,productivity,software,web,development
meta_description: DryDrop is a tool that lets you host your static site on Google App Engine and update it by pushing to GitHub
meta_image: http://www.binaryage.com/base/img/icons/drydrop-256.png
downloadtitle: Install v0.3
downloadsubtitle: or better use Github pages instead :-)
facebook: 1
retweet: 1
buzz: 1
fbsdk: 1
ogmeta: {
    site_name: "BinaryAge website",
    description: "DryDrop updates App Engine site after pushing to GitHub",
    email: "support@binaryage.com",
    type: "product",
    title: "DryDrop",
    url: "http://drydrop.binaryage.com",
    image: "http://www.binaryage.com/base/img/icons/drydrop-256.png"
}
shots: [{
    title: "DryDrop welcome screen",
    thumb: "/base/img/drydrop-mainshot.png",
    full: "/base/img/drydrop-mainshot-full.png"
}]
---


## Features

#### Host your static site on Google App Engine and update it by pushing to GitHub.

DryDrop is a tool that lets you host your static site on Google App Engine and update it by pushing to GitHub. Thanks to GitHub post-receive hooks your App Engine site can be updated automatically when you push new content.

* DRY principle (set it and forget it)
* Zero cost (thanks to [Google App Engine][appengine])
* Zero maintenance (thanks to [GitHub][github])
* No Python knowledge needed, but you need to know the basics of Git

For additional info read [blog post by Harper Reed](http://www.nata2.org/2011/01/26/how-to-use-app-engine-to-host-static-sites-for-free).

### How it works

It's simple. Let's say you have a GitHub repository containing a static web site and you want to host it on App Engine. DryDrop is an application that's ready to be uploaded as your App Engine project. After you upload it for the first time, you should set up a post-receive hook in your GitHub repo to point to your App Engine project. This means that every change you push to GitHub will be reflected on your App Engine site immediately.

Let's say someone visits your App Engine site. DryDrop has a simple cache. If a requested page is not in the cache, DryDrop will try to fetch it from GitHub, store it in the cache and then serve it. Next time the same URL is requested, it will be served directly from the DryDrop cache.

Let's say you made some changes to your files. In the moment you push file changes into GitHub, the post-receive hook will ping DryDrop, which will invalidate modified files in the cache. The next request will trigger a download of fresh files from GitHub.

## Installation

- upload your static files as a GitHub repository
- create a GAE project and upload DryDrop
- point your DryDrop site to your GitHub repo
- (optional) set up a post-receive hook in GitHub repo pointing to your DryDrop site

#### After that, every change pushed to github project will automatically propagate to your static site hosted by Google.

### Step 1: prepare your GitHub repository

You already know how to work with GitHub, right? 

Let's say you are user `darwin` and created repository `web-app-theme`.
So your repository's content lives at <a href="http://github.com/darwin/web-app-theme/tree/master">http://github.com/darwin/web-app-theme/tree/master</a>

### Step 2: create your App Engine project and upload DryDrop

Now you've created project called `drydropsample` like this:

<a href="/base/img/drydrop-create-app.png"><img src="/base/img/drydrop-create-app.png" width="300"></a>

Then make sure you have latest <a href="http://code.google.com/appengine/downloads.html">Google App Engine SDK</a> available on your machine.

Then you have to download the latest DryDrop and upload it to your drydropsample project:

    git clone git://github.com/binaryage/drydrop.git
    cd drydrop
    rake upload project=drydropsample
    
Note: You will be prompted for user name and password for your Google account by appcfg.py script.

My session looked like this:

<a href="/base/img/drydrop-upload.png"><img src="/base/img/drydrop-upload.png" width="300"></a>

Now you can visit your App Engine site at <a href="http://drydropsample.appspot.com">http://drydropsample.appspot.com</a> and you should see the welcome page:

<a href="/base/img/drydrop-welcome.png"><img src="/base/img/drydrop-welcome.png" width="300"></a>

### Step 3: point DryDrop site to your GitHub repo

Go to the admin section of your DryDrop site and switch to the settings page:

<a href="/base/img/drydrop-settings.png"><img src="/base/img/drydrop-settings.png" width="300"></a>

Set "Pull from" to `http://github.com/darwin/web-app-theme/raw/master`. That "raw" in the URL is important!!!

When you go back to <a href="http://drydropsample.appspot.com">http://drydropsample.appspot.com</a>, you should see your repo's content (assuming you have an index.html there)

<a href="/base/img/drydrop-site.png"><img src="/base/img/drydrop-site.png" width="300"></a>

### Step 4 (optional): set up post-receive hook in GitHub repo pointing to your DryDrop site

Go to the Admin section of your GitHub repo:

<a href="/base/img/drydrop-hook.png"><img src="/base/img/drydrop-hook.png" width="300"></a>

Set `http://drydropsample.appspot.com/hook/github` as post-receive hook.

### Step 5 (optional): test the hook

Now, let's try to push a change and check if it gets auto-published on <a href="http://drydropsample.appspot.com">http://drydropsample.appspot.com</a>.

<a href="/base/img/drydrop-edit.png"><img src="/base/img/drydrop-edit.png" width="300"></a>

Push it to GitHub ...

<a href="/base/img/drydrop-push.png"><img src="/base/img/drydrop-push.png" width="300"></a>

When you revisit <a href="http://drydropsample.appspot.com">http://drydropsample.appspot.com</a>, you should see an updated version:

<a href="/base/img/drydrop-updated.png"><img src="/base/img/drydrop-updated.png" width="300"></a>

You can double-check the situation in the admin section under Dashboard events:

<a href="/base/img/drydrop-events.png"><img src="/base/img/drydrop-events.png" width="300"></a>

The post-receive hook was triggered as you can see in the events list.

#### And that's it... Happy pushing! :-)

## FAQ

#### Do I need to understand Python to use this?
> Not at all. You just need to know how to use Git and how to create your App Engine project on appspot.com.

#### How does DryDrop compare to <a href="http://pages.github.com">GitHub Pages</a>?
> GitHub Pages solves the same need of "live-hosting of GitHub repository as a static site on custom domain". I started this project before GitHub Pages was announced and GitHub pages made it somewhat obsolete, especially because they support <a href="http://github.com/mojombo/jekyll/tree/master">jekyll</a>, which is cool.

#### How can DryDrop serve files from GitHub?
> It is simple. DryDrop has a simple cache. If a requested page is not in the cache, DryDrop will try to fetch it from GitHub, store it in the cache and then serve it. Next time the same URL is requested, it will be served directly from the DryDrop cache. Let's say you made some changes to your files. The moment you push file changes into GitHub, the post-receive hook will call DryDrop and DryDrop will invalidate modified files in the cache.

#### What if I want pretty URLs or some kind of routing?
> You can create a `site.yaml` config file which defines mapping between your repository files and App Engine URLs. This config uses a subset of App Engine's <a href="http://code.google.com/appengine/docs/python/config/appconfig.html">app.yaml syntax</a> and is kept in your GitHub repo, so you don't need to re-upload DryDrop after changing it. See admin/settings section of your DryDrop site for more info.

#### What about markdown/textile or some kind of static site generator like jekyll?
> You can use anything you want locally and pusht the generated output into your github repo. You can point your DryDrop site to a subfolder of your GitHub repo, even to different branch, so you have quite flexible options for how to keep your original source with generated output in one repo. I prefer to keep DryDrop simple, but you are welcome to add support for your favorite stack.

#### Are you going to support bitbucket or some other code repository services?
> Maybe, if there is a demand for it.


## Changelog

  * **v0.3** (18.02.2010) 
    * [[curiousdannii][]] added Last-Modified/If-Modified-Since support
    * [[darwin][]] serve simple not-found page for missing pages (can be overriden by /404.html file in your repo)
    * [[darwin][]] main routing routine is wrapped into try-catch block, better error page explaining possible steps to fix broken drydrop ([closes #1](http://github.com/binaryage/drydrop/issues#issue/1))
    * [[darwin][]] detect bogus status404 pages from github and treat them as real 404 pages ([fixes #2](http://github.com/binaryage/drydrop/issues#issue/2))
    * [[mannkind][]] added "Content-Type: text/html" header for files without an extension (for clean-like URLs without .html)

  * **v0.2** (09.08.2009) 
    * [[darwin][]] introducing support for GitHub and GitHub hooks
    * [[darwin][]] initial public version

  * **v0.1** (13.12.2008) 
    * [[darwin][]] initial experimental implementation
    
## Links

### Articles

  * [OMG FREE HOSTING: How to use GAE to host static sites for free](http://www.nata2.org/2011/01/26/how-to-use-app-engine-to-host-static-sites-for-free) (by Harper Reed)
  * [DryDrop announced](http://googleappengine.blogspot.com/2009/08/recent-happenings-ticktock-parallel.html) (via [Google App Engine Blog](http://googleappengine.blogspot.com))
  * [Using Google AppEngine as a “cache” for personal websites (wordpress blogs, wikis)](http://stackoverflow.com/questions/1675715/using-google-appengine-as-a-cache-for-personal-websites-wordpress-blogs-wikis) (via [Stack Overflow](http://stackoverflow.com))
  * [DryDrop – Manage static web site with GAE and Github](http://www.openalexandria.com/2009/09/drydrop) (via [openalexandria.com](http://www.openalexandria.com))

### Related Sites
  * [GitHub][github] - social code hosting

[appengine]: http://code.google.com/appengine
[github]: http://github.com
[darwin]: http://github.com/darwin
[mannkind]: http://github.com/mannkind
[curiousdannii]: http://github.com/curiousdannii