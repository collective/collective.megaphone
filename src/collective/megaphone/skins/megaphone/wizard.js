(function($) {
$.fn.megaphone_html5_sortable = function(options) {
    options = $.extend({
        onReorder: null
    }, options || {});
    
    this.attr('draggable', 'true')
        .css('-webkit-user-drag', 'element')
        .each(function (i) { $(this).attr('data-drag_id', i); })
        .bind('dragstart', function(e) {
            e.originalEvent.dataTransfer.setData('Text', $(this).attr('data-drag_id'));
            $('<div id="drop-marker" style="position: absolute; width: 100%;"></div>').insertBefore(this);
        })
        .bind('dragenter', function(e) { return false; })
        .bind('dragleave', function(e) { return false; })
        .bind('dragover', function(e) {
            var position = $(this).position();
            var height = $(this).height();
            var marker = $('#drop-marker');
            marker.css('border-bottom', '5px dotted red');
            if (e.pageY < ($(this).offset().top + height / 2)) {
                marker.css('top', position.top - 4 + 'px');
                $(this).attr('draghalf', 'top');
            } else {
                marker.css('top', position.top + height + 'px');
                $(this).attr('draghalf', 'bottom');
            }
            // window autoscroll
            if (!$('html,body').is(':animated')) {
                if ($(window).scrollTop() + $(window).height() - e.pageY < 30) { // bottom
                    $('html,body').animate({scrollTop: $(window).scrollTop() + 50}, 200);
                } else if (e.pageY - $(window).scrollTop() < 30) { // top
                    $('html,body').animate({scrollTop: $(window).scrollTop() - 50}, 200);
                }
            }
            return false;
        })
        .bind('drop', function(e) {
            e.preventDefault();
            var src = e.originalEvent.dataTransfer.getData('Text');
            var node = $('[data-drag_id=' + src + ']');
            if ($(this).attr('data-drag_id') == src) return;
            if ($(this).attr('draghalf') == 'top') {
                node.insertBefore(this);
            } else {
                node.insertAfter(this);
            }
            $('#drop-marker').remove();
            options.onReorder.apply(node, [node.parent().children('[data-drag_id]').index(node)]);
        })
        .bind('dragend', function(e) {
            $('#drop-marker').remove();
        });
}

$(function(){
    $('.fieldTitle').mouseup(function(){
        $(this).parents('dl').toggleClass('open');
        $(this).next('.fieldForm').slideToggle('fast');
    })
    $(".megaphone-orderable .megaphone-table td:last-child").mousedown(function(){
        var dl = $('dl', $(this).prev('td'));
        if (dl.hasClass('open')) {
            dl.toggleClass('open');
            $('.fieldForm', dl).slideToggle('fast');
        }
    });
    
    $(".megaphone-orderable").megaphone_html5_sortable({
        onReorder: function(i) {
            var sortable = this.parent('.megaphone-table-list');
            var items = sortable.children();
            items.each(function(){
                var pos = items.index(this);
                $('input[name$=order]', this).val(pos);
                if (pos % 2)
                    this.className = 'odd';
                else
                    this.className = 'even';
            });
        }
    });
    
    $('#wizard-step-formfields #form-buttons-continue, #wizard-step-formfields #form-buttons-back, #wizard-step-recipients #form-buttons-continue, #wizard-step-recipients #form-buttons-back').click(function(){
        // prevent messages about multiple submits if user cancels
        $(this).removeClass('submitting');
        // check the form for changes even if we're submitting
        message = window.onbeforeunload(null);
        if (message && !confirm("You have made changes that will be lost.  You probably want to press the 'Apply changes' or 'Add' button before you continue.  Continue?")) {
            return false;
        }
    });
    
    // show preview if no errors
    if ($('#letter-preview').length) {
      $('#letter-preview').addClass('overlay').hide();
      if (!$('.error').length) {
        $('#letter-preview').overlay({api: true}).load();
      }
    }
});
})(jQuery);