/*!
 * Javascript Humane Dates
 * Copyright (c) 2008 Dean Landolt (deanlandolt.com)
 * Re-write by Zach Leatherman (zachleat.com)
 * 
 * Adopted from the John Resig's pretty.js
 * at http://ejohn.org/blog/javascript-pretty-date
 * and henrah's proposed modification 
 * at http://ejohn.org/blog/javascript-pretty-date/#comment-297458
 * 
 * Licensed under the MIT license.
 */

function humane_date(date_str){
    var time_formats = [
        [60, 'Just Now'],
        [90, '1 Minute'], // 60*1.5
        [3600, 'Minutes', 60], // 60*60, 60
        [5400, '1 Hour'], // 60*60*1.5
        [86400, 'Hours', 3600], // 60*60*24, 60*60
        [129600, '1 Day'], // 60*60*24*1.5
        [604800, 'Days', 86400], // 60*60*24*7, 60*60*24
        [907200, '1 Week'], // 60*60*24*7*1.5
        [2628000, 'Weeks', 604800], // 60*60*24*(365/12), 60*60*24*7
        [3942000, '1 Month'], // 60*60*24*(365/12)*1.5
        [31536000, 'Months', 2628000], // 60*60*24*365, 60*60*24*(365/12)
        [47304000, '1 Year'], // 60*60*24*365*1.5
        [3153600000, 'Years', 31536000], // 60*60*24*365*100, 60*60*24*365
        [4730400000, '1 Century'], // 60*60*24*365*100*1.5
    ];

    var time = ('' + date_str).replace(/-/g,"/").replace(/[TZ]/g," "),
        dt = new Date,
        seconds = ((dt - new Date(time) + (dt.getTimezoneOffset() * 60000)) / 1000),
        token = ' Ago',
        i = 0,
        format;

    if (seconds < 0) {
        seconds = Math.abs(seconds);
        token = '';
    }

    while (format = time_formats[i++]) {
        if (seconds < format[0]) {
            if (format.length == 2) {
                return format[1] + (i > 1 ? token : ''); // Conditional so we don't return Just Now Ago
            } else {
                return Math.round(seconds / format[2]) + ' ' + format[1] + (i > 1 ? token : '');
            }
        }
    }

    // overflow for centuries
    if(seconds > 4730400000)
        return Math.round(seconds / 4730400000) + ' Centuries' + token;

    return date_str;
};

if(typeof jQuery != 'undefined') {
    jQuery.fn.humane_dates = function(){
        return this.each(function(){
            var date = humane_date(this.title);
            if(date && jQuery(this).text() != date) // don't modify the dom if we don't have to
                jQuery(this).text(date);
        });
    };
}

$(document).ready(function() {
    var placeholder = function(s) {
        return '<span class="placeholder">'+s+'</span>';
    };
    
    $("#source.edit").editable('/admin/update_option', {
        submit: 'OK',
        indicator: '<img src="/drydrop-static/images/indicator.gif">',
        tooltip: 'Click to edit source URL',
        placeholder: placeholder('enter source URL for mirroring'),
        style: 'inherit',
        height: '16px',
        width: '590px',
        callback: function(value, settings) {
            state.source = value;
            $('.sitename').html('<a href="'+value+'">'+value+'</a>');
        }
    });
    $("#config.edit").editable('/admin/update_option', {
        submit: 'OK',
        height: '16px',
        width: '590px',
        indicator: '<img src="/drydrop-static/images/indicator.gif">',
        tooltip: 'Click to edit config relative path',
        placeholder: placeholder('enter relative path to config file'),
        style: 'inherit'
    });
    $("#github_login.edit").editable('/admin/update_option', {
        submit: 'OK',
        height: '16px',
        width: '590px',
        indicator: '<img src="/drydrop-static/images/indicator.gif">',
        tooltip: 'for private repo you need to enter GitHub login',
        placeholder: placeholder('enter GitHub username'),
        style: 'inherit'
    });
    $("#github_token.edit").editable('/admin/update_option', {
        submit: 'OK',
        height: '16px',
        width: '590px',
        indicator: '<img src="/drydrop-static/images/indicator.gif">',
        tooltip: 'for private repo you need to enter GitHub token',
        placeholder: placeholder('enter GitHub token'),
        style: 'inherit'
    });

	$('.help-button').bind('click', function() {
		$(this).parent().find('.help-text').toggle();
	});
    
    dashboard.askForEvents();
});

var dashboard = {
    eventsLimit: 50,
    eventsOffset: 0,
    
    flushResourceCache: function() {
        if (!confirm("Do you really want flush resource cache?")) return;

        var rconsole = $('#flushing-console')
        rconsole.html('');
        
        var append = function(msg) { 
            rconsole.append('<div class="flushing-msg">'+msg+'</div>');
        };

        var finisher = function(result) {
            append(result.message);
			$('.cache-box').empty();
        };
        
        var presenter = function(result) {
            append(result.message);
        };
        
        var fetcher = function(data) {
            $.post("/admin/flusher", data, function(response) {
                if (response.finished) {
                    finisher(response);
                } else {
                    setTimeout(function() {
                        fetcher(response);
                        presenter(response);
                    }, 100);
                }
            }, "json");
        };
        
        fetcher({ command: 'go' });
    },

    clearEventsLog: function() {
        if (!confirm("Do you really want clear events log?")) return;

        var rconsole = $('#flushing-console')
        rconsole.html('');
        
        var append = function(msg) { 
            rconsole.append('<div class="flushing-msg">'+msg+'</div>');
        };

        var finisher = function(result) {
            append(result.message);
            dashboard.eventsOffset = 0;
            dashboard.askForEvents();
        };
        
        var presenter = function(result) {
            append(result.message);
        };
        
        var fetcher = function(data) {
            $.post("/admin/events_flusher", data, function(response) {
                if (response.finished) {
                    finisher(response);
                } else {
                    setTimeout(function() {
                        fetcher(response);
                        presenter(response);
                    }, 100);
                }
            }, "json");
        };
        
        fetcher({ command: 'go' });
    },
    
    renderEvents: function(events) {
        var c = $('#events-list');
        var g = ['<table>'];
        for (var i=0; i < events.length; i++) {
            var e = events[i];
			var hasInfo = e.info!='None';
			if (!hasInfo) {
				var more = "";
				var infoBox = "";
			} else {
				var more = '<span onclick="$(this).next(\'.info-box\').toggle()" class="more-button">more ...</span>';
				var infoBox = '<div class="info-box">'+e.info+'</div>';
			}
            g.push('<tr>');
            g.push('<td class="author">'+e.author+'</td>');
            g.push('<td class="date">'+humane_date(e.date).toLowerCase()+'</td>');
            g.push('</tr>');
            g.push('<tr class="second">');
            g.push('<td colspan="2" class="action">'+e.action+more+infoBox+'</td>');
            g.push('</tr>');
        };
        g.push('</table>');
        c.attr('innerHTML', g.join(''));
    },
    
    onNextEvents: function() {
		if ($('#events-paginator .next-button').hasClass('disabled')) return;
        this.eventsOffset += this.eventsLimit;
        this.askForEvents();
    },

    onPrevEvents: function() {
		if ($('#events-paginator .prev-button').hasClass('disabled')) return;
        if (this.eventsOffset<=0) return;
        this.eventsOffset -= this.eventsLimit;
		if (this.eventsOffset<0) this.eventsOffset = 0;
        this.askForEvents();
    },
    
    askForEvents: function() {
		var that = this;
        $.get("/admin/events", { limit: this.eventsLimit+1, offset: this.eventsOffset }, function(data) {
            if (data.status==0) {
                dashboard.renderEvents(data.data);
				if (data.data.length<that.eventsLimit+1) {
					$('#events-paginator .next-button').addClass('disabled');
				} else {
					$('#events-paginator .next-button').removeClass('disabled');
				}
				if (that.eventsOffset<=0) {
					$('#events-paginator .prev-button').addClass('disabled');
				} else {
					$('#events-paginator .prev-button').removeClass('disabled');
				}
            } else {
                // TODO: handle this
            }
        }, "json");
        
    }
};