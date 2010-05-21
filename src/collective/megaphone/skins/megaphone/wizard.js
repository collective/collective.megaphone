jq(function(){
    jq('.fieldTitle').mouseup(function(){
        jq(this).parents('dl').toggleClass('open');
        jq(this).next('.fieldForm').slideToggle('fast');
    })
    jq(".orderable-crud-sortable td:last-child").mousedown(function(){
        var dl = jq('dl', jq(this).prev('td'));
        if (dl.hasClass('open')) {
            dl.toggleClass('open');
            jq('.fieldForm', dl).slideToggle('fast');
        }
    });
    
    jq(".orderable-crud-sortable").sortable({
        axis: 'y',
        handle: 'td:eq(2)',
        update: function(event, ui){
            var sortable = jq(ui.item).parent('.orderable-crud-sortable');
            var items = sortable.children(':not(.ui-sortable-placeholder)');
            items.each(function(){
                var pos = items.index(this);
                jq('input[name$=order]', this).val(pos);
                if (pos % 2)
                    this.className = 'odd';
                else
                    this.className = 'even';
            });
        }
    });
    
    jq('#wizard-step-formfields #form-buttons-continue, #wizard-step-formfields #form-buttons-back, #wizard-step-recipients #form-buttons-continue, #wizard-step-recipients #form-buttons-back').click(function(){
        // prevent messages about multiple submits if user cancels
        jq(this).removeClass('submitting');
        // check the form for changes even if we're submitting
        message = window.onbeforeunload(null);
        if (message && !confirm("You have made changes that will be lost.  You probably want to press the 'Apply changes' or 'Add' button before you continue.  Continue?")) {
            return false;
        }
    });
    
    // show preview if no errors
    if (jq('#letter-preview').length) {
      jq('#letter-preview').addClass('overlay pb-ajax').hide();
      if (!jq('.error').length) {
        jq('#letter-preview').overlay({api: true, expose: { color: '#666'} }).load();
      }
    }
});
