$(function(){
    // gettext wrapper
    var _ = (typeof gettext == 'undefined' ? function(x) { return x; } : gettext);

    var advreport = function($elem) {
        this.adv_report      = $elem;
        this.adv_slug        = this.adv_report.data('slug');
        this.adv_url         = this.adv_report.data('link');
        this.adv_animation   = this.adv_report.data('animation');

        this.init();
    }

    $.extend(advreport.prototype, {

            init: function() {
                var instance = this;
                var adv_report = this.adv_report;
                adv_report.find('.date_range').each(function() {
                    var date_picker_options = {showOn: 'button',
                                               buttonImage: JS_STATIC_URL + 'advanced_reports/img/calendar.png',
                                               buttonImageOnly: true,
                                               dateFormat: 'yy-mm-dd',
                                               maxDate:'+0D',
                                               firstDay: 1,
                                               dayNamesMin: [_("Su"),
                                                             _("Mo"),
                                                             _("Tu"),
                                                             _("We"),
                                                             _("Th"),
                                                             _("Fr"),
                                                             _("Sa")],
                                               monthNames: [_("January"),
                                                            _("February"),
                                                            _("March"),
                                                            _("April"),
                                                            _("May"),
                                                            _("June"),
                                                            _("July"),
                                                            _("August"),
                                                            _("September"),
                                                            _("October"),
                                                            _("November"),
                                                            _("December")]};

                    $(this).datepicker(date_picker_options);
                });

                adv_report.find('.select-all').click(function(){
                    adv_report.find('.information-checkbox').attr('checked', true);
                    adv_report.find('#selector').attr('checked', true);
                    instance.update_checkboxes();
                    return false;
                });

                adv_report.find('.select-none').click(function(){
                    adv_report.find('.information-checkbox').attr('checked', false);
                    adv_report.find('#selector').attr('checked', false);
                    instance.update_checkboxes();
                    return false;
                });

                adv_report.find('.select-toggle').click(function(){
                    adv_report.find('.information-checkbox').click();
                    adv_report.find('#selector').attr('checked', false);
                    instance.update_checkboxes();
                    return false;
                });

                $('#selector').live('click', function(){
                    if ($(this).is(":checked")) {
                        $(".information-checkbox").attr("checked", "checked");
                    } else {
                        $(".information-checkbox").removeAttr("checked");
                    }
                    instance.update_checkboxes();
                });

                adv_report.find('.multiple-action-form input[type="submit"]').click(function(){
                    var method = $('#select-method').val();
                    if (method == '')
                        return false;

                    var execute = function(){
                        adv_report.find('.multiple-action-form').submit();
                    };

                    if ($('.confirm_' + method).data('confirm'))
                        $.mbox((_("Confirm")), $('.confirm_' + method).data('confirm'), { type: DIALOG_YES_NO, callback_closed_yes: execute});
                    else
                        execute();
                    return false;
                });
            },

            update_checkboxes: function() {
                this.adv_report.find('.information-checkbox').each(function(){
                    var checkbox = $(this);
                    var hidden = $('#' + checkbox.attr('id').replace('checkbox_', 'hidden_checkbox_'));
                    hidden.attr('value', checkbox.is(':checked') ? 'true' : 'false');
                });
            },

            handle_lazy: function(container) {
                var adv_url = this.adv_url;
                var advreport = this;
                container.find('.lazy').each(function(){
                    var lazy_div = $(this);
                    lazy_div.html('<img class="loader" src="' + JS_STATIC_URL + 'advanced_reports/img/modybox/loading.gif" alt=""/>');
                    lazy_div.find('.loader').show();
                    var object_id = '0';
                    if (container.attr('id'))
                        object_id = container.attr('id').split('_')[1];
                    
                    var url = adv_url + 'action/' + lazy_div.data('method') + '/' + object_id + '/';
                    $.ajax({
                        'type': 'GET',
                        'url': url,
                        'dataType': 'text',
                        'success': function(x) {
                            lazy_div.find('.loader').hide();
                            //lazy_div.removeClass('lazy');
                            lazy_div.html(x);
                            advreport.connect_row(container, false, true);
                        },
                        'error': function(x) {
                            lazy_div.find('.loader').hide();
                            lazy_div.text('error');
                        }
                    });
                });
            },

            connect_row: function(action_row, initialHide, noLazy) {
                var data_row        = action_row.prev();
                var show_options    = data_row.find('.show-options');
                var hide_options    = data_row.find('.hide-options');
                var checkbox        = data_row.find('.information-checkbox');
                var instance        = this;

                if (checkbox && checkbox.attr('id')) {
                    var id = checkbox.attr('id').replace('checkbox_', '');
                    var hidden = $('#hidden_checkbox_' + id);
                    if (hidden.length <= 0) {
                        $('#advreport_' + instance.adv_slug + ' form.multiple-action-form select').before(
                            $('<input type="hidden" />').attr('name', 'checkbox_0000_' + id)
                                        .attr('id', 'hidden_checkbox_' + id)
                                        .attr('value', false)
                        );
                    }
                }

                if (initialHide && $('.action-row').length > 1)
                    collapse_row();
                else
                    expand_row();

                function expand_row()
                {
                    if (instance.adv_animation == 'True')
                        action_row.slideDown('fast');
                    else
                        action_row.show();
                    show_options.hide();
                    hide_options.show();
                    action_row.find('input:text').eq(0).focus();
                    if (!noLazy)
                        instance.handle_lazy(action_row);
                }

                function collapse_row()
                {
                    if (instance.adv_animation == 'True')
                        action_row.slideUp('fast');
                    else
                        action_row.hide();
                    show_options.show();
                    hide_options.hide();
                }

                function handle_checkbox_click()
                {
                    var hidden = $('#' + checkbox.attr('id').replace('checkbox_', 'hidden_checkbox_'));
                    hidden.attr('value', checkbox.is(':checked') ? 'true' : 'false');
                    if (!checkbox.is(':checked'))
                        $('#selector').attr('checked', false);
                }

                data_row.unbind().click(function(e){
                    if (action_row.is(':visible')) collapse_row(); else expand_row();
                    if (action_row.hasClass('empty-row'))
                    {
                        checkbox.attr('checked', !checkbox.attr('checked'));
                        handle_checkbox_click();
                    }
                    e.stopPropagation();
                });

                data_row.find('a').each(function(){
                    var link = $(this);
                    link.unbind().click(function(e){ e.stopPropagation(); });
                });

                show_options.unbind().click(function(){ expand_row(); return false; });
                hide_options.unbind().click(function(){ collapse_row(); return false; });

                action_row.find('.action-form').each(function(){
                    var form = $(this);
                    instance.connect_form(form, action_row, data_row);
                });

                action_row.find('.collapse-form').each(function(){
                    $(this).addClass('inline').removeClass('limit-width');
                });

                action_row.find('.action-link').each(function(){
                    var link = $(this);
                    if (!link.hasClass('form-via-ajax')) {
                        instance.connect_link(link, action_row, data_row);
                    }
                });

                checkbox.click(function(e){
                    handle_checkbox_click();
                    e.stopPropagation();
                });
                if (checkbox && checkbox.attr('id')){
                    handle_checkbox_click();
                }
                
                action_row.find('.form-via-ajax').each(function(){
                    var link = $(this);
                    
                    link.unbind().click(function(){
                        var action_name = link.text();
                        var title = link.data('confirm');
                        if (!title || title == "") {
                            title = action_name;
                        }
                        var submit_caption = link.data('submit');
                        if (!submit_caption || submit_caption == "") {
                            submit_caption = action_name;
                        }
                    
                        $.mbox_ajax_form(
                            title,
                            link.attr("href"),
                            submit_caption,
                            {
                                'width': '600px',
                                'response_type': RESPONSE_JSON,
                                'callback_ajax_posted_success': function(mbox_element, data){
                                    instance.replace_rows(data, action_row, data_row, link.data('next') == true);
                                    return true;
                                }
                            }
                        );
                        
                        return false;
                    });
                });
            },

            recycle: function() {
                var counter = 0;
                this.adv_report.find('.table-row').each(function(){
                    $(this).removeClass('alternate');
                    if ((counter % 4) >= 2) {
                        $(this).addClass('alternate');
                    }

                    counter++;
                });
            },

            replace_rows: function(data, action_row, data_row, next_on_success) {
                var instance = this;
                var probe = $(data);
                var new_rows;
                if (probe.get(0).tagName == 'TR')
                    new_rows = $('<table>' + data + '</table>');
                else
                    new_rows = $('<div>' + data + '</div>');

                var new_action_row = new_rows.find('.action-row');
                var new_data_row = new_action_row.prev();
                new_data_row.insertBefore(data_row);
                new_action_row.insertBefore(data_row);
                data_row.remove();
                action_row.remove();
                instance.connect_row(new_action_row, false);

                var next_data_row = new_action_row.next();
                var next_action_row = new_action_row.next().next();

                this.recycle();

                $(document).trigger('newElements', new_action_row);

                if (new_action_row.find('.success').length > 0)
                {
                    show_notice(new_action_row.find('.success').text());
                    if (next_on_success)
                    {
                        next_action_row.show();
                        next_data_row.find('.show-options').hide();
                        next_data_row.find('.hide-options').show();
                        next_action_row.find('input:text').eq(0).focus();
                        instance.handle_lazy(next_action_row);
                        new_action_row.hide();
                        new_data_row.find('.show-options').show();
                        new_data_row.find('.hide-options').hide();
                    }
                    else
                    {
                        new_action_row.show();
                        new_data_row.find('.show-options').hide();
                        new_data_row.find('.hide-options').show();
                    }
                }
            },

            connect_form: function(form, action_row, data_row) {
                var instance = this;
                function submit_form()
                {
                    var execute = function(){
                        $.ajax({
                            'type': 'POST',
                            'url': form.attr('action').replace('/action/', '/ajax/'),
                            'dataType': 'text',
                            'data': form.serialize(),
                            'success': function(x) {
                                instance.replace_rows(x, action_row, data_row, form.data('next') == true);
                            },
                            'error': function(x) { $.mbox_error(_("Alert"), x.responseText); }
                        });
                    };

                    if (form.data('confirm'))
                        $.mbox((_("Confirm")), form.data('confirm'), { type: DIALOG_YES_NO, callback_closed_yes: execute});
                    else
                        execute();

                    return false;
                }

                // var submit_button = form.find('.action-submit');
                form.off('submit');
                form.on('submit', submit_form);
                //form.find('input[type=text]').last().keypress(function(e) { if (e.which == 13) { submit_form(); return false; } } );
            },

            connect_link: function(link, action_row, data_row) {
                var instance = this;

                if (link.attr('href').indexOf('_view') != -1) {
                    if (!link.data('ajax'))
                        return;
                    
                    link.unbind().click(function(){
                        var execute = function()
                        {
                            link.find('.loader').show();
                            $.ajax({
                                'type': 'GET',
                                'url': link.attr('href'),
                                'dataType': 'text',
                                'success': function(x) {
                                    link.find('.loader').hide();
                                    $.mbox(link.text(), x, {
                                        'width': '700px'
                                    });
                                },
                                'error': function(x) {
                                    link.find('.loader').hide();
                                    $.mbox_error(_("Alert"), x.responseText);
                                }
                            });
                        };

                        if (link.data('confirm'))
                            $.mbox((_("Confirm")), link.data('confirm'), { type: DIALOG_YES_NO, callback_closed_yes: execute});
                        else
                            execute();
                        return false;
                    });
                }
                else {
                    link.unbind().click(function(){
                        var execute = function()
                        {
                            link.find('.loader').show();
                            $.ajax({
                                'type': 'POST',
                                'url': link.attr('href').replace('/action/', '/ajax/'),
                                'data': $('#csrf_form').serialize(),
                                'dataType': 'text',
                                'success': function(x) {
                                    link.find('.loader').hide();
                                    instance.replace_rows(x, action_row, data_row, link.data('next') == true);
                                },
                                'error': function(x) {
                                    link.find('.loader').hide();
                                    $.mbox_error(_("Alert"), x.responseText);
                                }
                            });
                        };

                        if (link.data('confirm'))
                            $.mbox((_("Confirm")), link.data('confirm'), { type: DIALOG_YES_NO, callback_closed_yes: execute});
                        else
                            execute();
                        return false;
                    });
                }
            },

            connect_page: function() {
                var instance = this;
                this.adv_report.find('.action-row').each(function(){
                    instance.connect_row($(this), true);
                });

                instance.handle_lazy($('.help-text'));
                instance.recycle();
            }
        });

    var reports = {};
    function register_advreports() {
        reports = {};
        $('.advreport').each(function(){
            var slug = $(this).data('slug');
            $(this).find('form.multiple-action-form input[name^="checkbox_"]:hidden').remove();
            if (! (slug in reports)) {
                var advr = new advreport($(this));
                reports[slug] = advr;
            }
        });
    }

    function connect_advreports() {
        register_advreports();
        for (var slug in reports) {
            reports[slug].connect_page();
        }
    }

    $(document).unbind('paginatorPageReplaced', connect_advreports);
    $(document).bind('paginatorPageReplaced', connect_advreports);
    $(document).unbind('tabLoaded', connect_advreports);
    $(document).bind('tabLoaded', connect_advreports);
    connect_advreports();
});
