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
});

var dashboard = {
    reindex: function() {
        if (!confirm("Do you really want rebuild index from\n"+state.source+" ?\
        \n\nReindexing is a process where we obtain file list from github by traversing project's directory structure.\n\n\
        This may take a while ...")) return;

        var rconsole = $('#reindexing-console')
        rconsole.html('');
        
        var append = function(msg) { 
            rconsole.append('<div class="reindex-msg">'+msg+'</div>');
        };

        var finisher = function(result) {
            append(result.message);
        };
        
        var presenter = function(result) {
            append(result.message);
        };
        var fetcher = function(data) {
            $.post("/admin/reindex", data, function(response) {
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