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
            g.push('<tr>');
            g.push('<td class="date">'+e.date+'</td>');
            g.push('<td class="author">'+e.author+'</td>');
            g.push('</tr>');
            g.push('<tr class="second">');
            g.push('<td colspan="2" class="action">'+e.action+'</td>');
            g.push('</tr>');
        };
        g.push('</table>');
        c.attr('innerHTML', g.join(''));
    },
    
    onNextEvents: function() {
        this.eventsOffset += this.eventsLimit;
        this.askForEvents();
    },

    onPrevEvents: function() {
        if (this.eventsOffset<=0) return;
        this.eventsOffset -= this.eventsLimit;
        this.askForEvents();
    },
    
    askForEvents: function() {
        $.get("/admin/events", { limit: this.eventsLimit, offset: this.eventsOffset }, function(data) {
            if (data.status==0) {
                dashboard.renderEvents(data.data);
            } else {
                // TODO: handle this
            }
        }, "json");
        
    }
};