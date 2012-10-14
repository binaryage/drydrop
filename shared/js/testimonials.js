(function() {
  var prepareTweetLoader;

  prepareTweetLoader = function(msg) {
    return ["<li class=\"hentry status\" id=\"tweet-loader\">", "<span class=\"thumb vcard author\"><img width=\"31\" height=\"31\" src=\"/shared/img/twitter-loader.gif\"></span>", "<span class=\"status-body\"><span class=\"tweet-msg\">" + msg + "</span><a class=\"more-praise\" target=\"_blank\" href=\"http://twitter.com/binaryage/favorites\">show all recent</a></span>", "</li>"].join("");
  };

  $.fn.tweet = function(options) {
    var generator, index, prevCard, ready;
    index = 0;
    ready = false;
    prevCard = void 0;
    generator = function(root, params) {
      var itemTemplate, worker;
      itemTemplate = "            <li id=\"status_--id--\" class=\"hentry status\">                <span class=\"thumb vcard author\">                    <a class=\"tweet-url profile-pic url\" href=\"http://twitter.com/--userscreenname--\">                        <img width=\"48\" height=\"48\" src=\"--avatar--\" class=\"photo fn\" alt=\"--username--\">                    </a>                </span>                <span class=\"status-body\">                    <strong><a title=\"--username--\" class=\"tweet-url screen-name\" href=\"http://twitter.com/--userscreenname--\">--userscreenname--</a></strong>                     <span class=\"entry-content\">--text--</span><span class=\"meta entry-meta\">                        <a rel=\"bookmark\" class=\"entry-date\" href=\"http://twitter.com/--userscreenname--/status/--id--\"><span class=\"published timestamp\">--createdat--</span></a>                         <span>from --source--</span>                    </span>                    <a class=\"more-praise\" target=\"_blank\" href=\"http://twitter.com/binaryage/favorites\">show all recent</a>                </span>            </li>";
      worker = function(data) {
        var availHeight, availWidth, children, container, cur, gen, step;
        if (!ready) {
          setTimeout((function() {
            return worker(data);
          }), 100);
          return;
        }
        container = $("#main .container");
        availWidth = 950 - 300;
        availHeight = container.height() - 80;
        if (availHeight < 200) {
          availHeight = 200;
        }
        if (availHeight > 600) {
          availHeight = 600;
        }
        gen = function(item) {
          var el, li, rot;
          index++;
          if (prevCard) {
            prevCard.addClass("card-fade-out");
          }
          li = itemTemplate;
          li = li.replace(/--id--/g, item.id);
          li = li.replace(/--text--/g, item.text);
          li = li.replace(/--avatar--/g, item.user.profile_image_url);
          li = li.replace(/--username--/g, item.user.name);
          li = li.replace(/--userscreenname--/g, item.user.screen_name);
          li = li.replace(/--source--/g, item.source);
          li = li.replace(/--createdat--/g, item.created_at);
          el = $(li);
          rot = Math.round(Math.random() * 3) + 3;
          if (index % 2 === 0) {
            rot = -rot;
          }
          el.css({
            left: Math.random() * availWidth,
            top: Math.random() * availHeight,
            "-webkit-transform": "rotate(" + rot + "deg)",
            "-moz-transform": "rotate(" + rot + "deg)"
          });
          root.append(el);
          prevCard = el;
          el.find(".published").relatizeDate();
          return el.find(".entry-content").autolink().autohash();
        };
        if (!data.length) {

        } else {
          children = root.children();
          if (children.length > 60) {
            children.slice(0, data.length).fadeOut(3000, function() {
              return $(this).remove();
            });
          }
          cur = -1;
          step = function() {
            var c, futureItem, im, item;
            cur++;
            if (cur >= data.length) {
              params.page++;
              generator(root, params);
              return;
            }
            item = data[cur];
            gen(item);
            c = 1;
            while (c <= 5) {
              futureItem = data[cur + c];
              if (futureItem) {
                im = new Image();
                im.src = futureItem.user.profile_image_url;
              }
              c++;
            }
            return setTimeout(step, 3000);
          };
          return step();
        }
      };
      return $.getJSON("http://api.twitter.com/1/favorites.json?page=" + params.page + "&id=" + encodeURIComponent(params.user) + "&callback=?", worker);
    };
    return this.each(function() {
      var defaults, params, root;
      root = $(this);
      defaults = {
        user: "binaryage",
        count: 5
      };
      params = $.extend(defaults, options);
      params.page = 1;
      root.data("sparams", params);
      $("#main").addClass("main-dim").append("<div class=\"main-overlay\"></div>");
      setTimeout((function() {
        return ready = true;
      }), 500);
      return generator(root, params);
    });
  };

}).call(this);
