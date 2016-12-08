(function() {
  this.parsePlaintextChangelog = function(text) {
    var changelog, i, line, lines, m, parts, release;
    lines = text.split("\n");
    changelog = [];
    release = void 0;
    i = 0;
    while (i < lines.length) {
      line = $.trim(lines[i]);
      i++;
      m = line.match(/^(.*?)(\s\/\/.*)$/);
      if (m) {
        line = $.trim(m[1]);
      }
      if (line.length < 1 || line.match(/^\/\//)) {
        continue;
      }
      switch (line[0]) {
        case "<":
          release.changes.push({
            kind: "raw",
            text: line
          });
          break;
        case "$":
          release.changes.push({
            kind: "announce",
            text: $.trim(line.substring(1))
          });
          break;
        case "*":
          release.changes.push({
            kind: "improved",
            text: $.trim(line.substring(1))
          });
          break;
        case "+":
          release.changes.push({
            kind: "new",
            text: $.trim(line.substring(1))
          });
          break;
        case "!":
          release.changes.push({
            kind: "fixed",
            text: $.trim(line.substring(1))
          });
          break;
        case "-":
          release.changes.push({
            kind: "removed",
            text: $.trim(line.substring(1))
          });
          break;
        default:
          parts = line.split("-");
          release = {
            version: $.trim(parts[0]),
            date: $.trim(parts[1]),
            note: $.trim(parts[2]),
            changes: []
          };
          changelog.push(release);
      }
    }
    return changelog;
  };

  this.generateChangelogHTML = function(el, changelog, getDownloadLinkForVersion, getReleaseDateText) {
    var $a, $b, $changes, $date, $info, $infobox, $li, $release, $root, $separator, $sticker, $titlebox, $version, change, i, j, release, results;
    $root = $(el);
    i = changelog.length - 1;
    results = [];
    while (i >= 0) {
      release = changelog[i];
      if (i !== changelog.length - 1) {
        $separator = $("<div class=\"separator\"/>");
      }
      i--;
      $release = $("<div class=\"release\"/>").attr('id', "v" + release.version);
      $titlebox = $("<div class=\"titlebox\"/>");
      $version = $("<h4/>");
      $a = $("<a>" + release.version + "</a>").attr("href", getDownloadLinkForVersion(release.version));
      $date = $("<h5/>").html(getReleaseDateText(release.date));
      $version.append($a);
      $titlebox.append($version, $date);
      $release.append($titlebox);
      $infobox = $("<div class=\"infobox\"/>");
      $changes = $("<ul class=\"changes\"/>");
      j = 0;
      while (j < release.changes.length) {
        change = release.changes[j];
        j++;
        if (change.kind === "raw") {
          $changes.append(change.text);
          continue;
        }
        if (change.kind === "announce") {
          $li = $("<li/>");
          $info = $("<span class=\"info announce\"/>").html(change.text);
          $li.append("<span class=\"sticker\">&nbsp;</span>", $info);
          $changes.append($li);
          continue;
        }
        $li = $("<li/>");
        change.text = change.text.replace(/\(.*?\)/g, function(m) {
          return "<i>" + m + "</i>";
        });
        change.text = change.text.replace(/\[(.*?)\]/g, function(m, $1) {
          return "<em>" + $1 + "</em>";
        });
        $b = $("<b/>").text(change.kind);
        $sticker = $("<span class=\"sticker\"/>").addClass(change.kind);
        $sticker.append($b);
        $info = $("<span class=\"info\"/>").html(change.text);
        $li.append($sticker, $info);
        $changes.append($li);
      }
      $infobox.append($changes);
      $release.append($infobox);
      results.push($root.prepend($release, $separator));
    }
    return results;
  };

}).call(this);
