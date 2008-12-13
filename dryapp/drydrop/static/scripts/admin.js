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
            $('.sitename').html('<a href="'+value+'">'+value+'</a>')
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
        placeholder: placeholder('enter GitHub login to access private repo'),
        style: 'inherit'
    });
    $("#github_token.edit").editable('/admin/update_option', {
        submit: 'OK',
        height: '16px',
        width: '590px',
        indicator: '<img src="/drydrop-static/images/indicator.gif">',
        tooltip: 'for private repo you need to enter GitHub token',
        placeholder: placeholder('enter GitHub token to access private repo'),
        style: 'inherit'
    });
});

var dashboard = {
    flushResourceCache: function() {
        if (!confirm("Do you really want flush resource cache?")) return;

        var rconsole = $('#flushing-console')
        rconsole.html('');
        
        var append = function(msg) { 
            rconsole.append('<div class="flushing-msg">'+msg+'</div>');
        };

        var finisher = function(result) {
            append(result.message);
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
    }
};