(function($) {
$.fn.megaphone_html5_sortable = function(options) {
    options = $.extend({
        onReorder: null,
        handleSelector: '.drag-handle'
    }, options || {});
    
    this.each(function (i) { $(this).attr('data-drag_id', i); })
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
            if ($(this).attr('data-drag_id') === src) {
                return;
            }
            if ($(this).attr('draghalf') === 'top') {
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
        
    var drag_elements = this;
    this.find(options.handleSelector).mouseover(function(e) {
        drag_elements.attr('draggable', true)
            .css('-webkit-user-drag', 'element');
    })
    .mouseout(function(e) {
        drag_elements.attr('draggable', false)
            .css('-webkit-user-drag', 'none');
    });
};

$(function(){
    $('.fieldTitle').mouseup(function(){
        $(this).parents('dl').toggleClass('open');
        $(this).next('.fieldForm').slideToggle('fast');
    });
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
                if (pos % 2) {
                    this.className = 'odd';
                } else {
                    this.className = 'even';
                }
            });
            $.post($('form[action$=editMegaphoneAction]').attr('action'), $('form[action$=editMegaphoneAction]').serialize() + '&crud-edit.formfields.buttons.edit=Save+order');
        }
    });
    
    // popups
    $('a.megaphone-popup-button').each(function() {
        var $this = $(this);
        $this.replaceWith($('<button class="megaphone-popup allowMultiSubmit" href="' + $this.attr('href') + '">' + $this.text() + '</button>'));
    });
    $('.megaphone-popup').prepOverlay({
        subtype: 'ajax',
        formselector: 'form',
        noform: 'reload'
    });
    
    // show preview if no errors
    if ($('#megaphone-preview').length) {
      $('#megaphone-preview').addClass('overlay').hide();
      if (!$('.error').length) {
        $('#megaphone-preview').overlay({api: true}).load();
      }
    }
});
})(jQuery);