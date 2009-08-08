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
overlaysx: 1606px
overlaysy: 738px
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

TODO

## Installation

- upload your static files as GitHub repository (easy step)
- generate DryDrop scaffold site and deploy it to GAE (easy step)
- setup post commit hook in GitHub repo pointing to your DryDrop site (easy step)

#### Since then, every change pushed to github project will automatically propagate to your static site hosted by Google.

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