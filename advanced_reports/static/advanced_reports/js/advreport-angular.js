angular.module('BackOfficeApp')
.controller('AdvancedReportCtrl', ['$scope', '$http', '$location', 'boUtils', 'boApi', function ($scope, $http, $location, boUtils, boApi){
    $scope.report = null;
    $scope.page_count = null;
    $scope.filters = {};
    $scope.applied_filters = {};
    $scope.search = $location.search() || {};
    $scope.single_action = $scope.view.params.action || null;
    $scope.selected = {};

    $scope.$watch(function(){
        return $location.search();
    }, function(search){
        $scope.search = search;
        $scope.fetch_report();
    }, true);

    $scope.fetch_report = function() {
        if (!$scope.search.page)
            $scope.search.page = 1;
        else
            $scope.search.page = parseInt($scope.search.page);

        for (var j in $scope.search){
            if (typeof $scope.search[j] === 'undefined')
                delete $scope.search[j];
        }

        $scope.filters = {};
        for (var m in $scope.search){
            if ($scope.search.hasOwnProperty(m)){
                if (['page', 'order'].indexOf(m) === -1)
                {
                    $scope.filters[m] = $scope.search[m];
                }
            }
        }

        if ($scope.view.params.updateLocation)
            $location.search($scope.search);

        var qs_list = [];
        for (var k in $scope.search)
            qs_list.push(encodeURIComponent(k) + '=' + encodeURIComponent($scope.search[k]));
        var qs = '?' + qs_list.join('&');

        $scope.view.action('fetch', {}, false, qs).then(function(data){
            $scope.report = data;
            if (data.item_count == 1)
                $scope.toggle_expand($scope.report.items[0]);
            $scope.page_count = Math.floor(data.item_count / data.items_per_page) + 1;
            $scope.selected = {};
            $scope.multiple_action_dict = {};
            angular.forEach($scope.report.multiple_action_list, function(value){
                $scope.multiple_action_dict[value.method] = value;
            });
        }, function(error){
            $scope.error = error;
        });
    };

    $scope.show_header = function(){
        return $scope.report
                && $scope.report.report_header_visible
                && !$scope.single_action
                && ($scope.show_search() || $scope.show_action_select());
    };

    $scope.show_search = function(){
        return $scope.report && (
                $scope.report.filter_fields && $scope.report.filter_fields.length > 0 ||
                $scope.report.search_fields && $scope.report.search_fields.length > 0);
    };

    $scope.change_page = function(page){
        if (page < 1 || page > $scope.page_count || $scope.search.page == page)
            return;
        $scope.search.page = page;
        $scope.fetch_report();
    };

    $scope.has_expanded_content = function(item){
        return (item.extra_information.length > 0 || item.actions.length > 0);
    };

    $scope.toggle_expand = function(item) {
        if ($scope.select_mode()){
            return;
        }
        if (!item.expanded && $scope.has_expanded_content(item)) {
            item.expanded = true;
            $scope.$broadcast('item_expanded', item.item_id);
            $scope.fetch_lazy_divs(item);
        } else {
            item.expanded = false;
        }
    };

    $scope.show_action_select = function(){
        return $scope.report && $scope.report.multiple_actions && !boUtils.isEmpty($scope.selected);
    };

    $scope.update_selected = function(){
        if ($scope.report.all_selected){
            angular.forEach($scope.report.items, function(item){
                $scope.selected[item.item_id] = true;
            });
        }else{
            $scope.selected = {};
        }
    };

    $scope.update_all_selected = function(selected){
        if (!selected){
            $scope.report.all_selected = false;
        }
        angular.forEach($scope.selected, function(value, key){
            if (!value){
                delete $scope.selected[key];
            }
        });
    };

    $scope.selected_count = function(){
        return boUtils.keyCount($scope.selected);
    };

    $scope.change_order = function(order_by) {
        var ascending = $scope.report.extra.order_by != order_by || !$scope.report.extra.ascending;
        $scope.search.order = (ascending ? '' : '-') + order_by;
        $scope.search.page = 1;
        $scope.fetch_report();
    };

    $scope.has_applied_filters = function() {
        var count = 0;
        for (var key in $scope.search)
            if (key != 'order' && key != 'page')
                count += 1;
        return count > 0 && $scope.show_search();
    };

    $scope.apply_filters = function() {
        $scope.search = {order: $scope.search.order};
        for (var k in $scope.filters)
            $scope.search[k] = $scope.filters[k];
        $scope.search.page = 1;
        $scope.fetch_report();
    };

    $scope.remove_filters = function() {
        $scope.loader='search';
        $scope.filter = {};
        $scope.search = {order: $scope.search.order, page: 1};
        $scope.fetch_report();
    };

    $scope.update_item = function(item, data, expand_next) {
        if (!!data.item){
            // We successfully got an item back
            var new_item = data.item;
            for (var key in new_item) {
                if (new_item.hasOwnProperty(key))
                    item[key] = new_item[key];
            }
            if (expand_next)
            {
                var this_item_id = $scope.report.items.indexOf(item);
                if (this_item_id < $scope.report.items.length - 1)
                {
                    $scope.toggle_expand(item);
                    $scope.toggle_expand($scope.report.items[this_item_id+1]);
                }
            }

            $scope.fetch_lazy_divs(item);
        } else {
            var item_to_remove = $scope.report.items.indexOf(item);
            if (expand_next){
                if (item_to_remove < $scope.report.items.length - 1)
                {
                    $scope.toggle_expand($scope.report.items[item_to_remove+1]);
                }
            }
            $scope.report.items.splice(item_to_remove, 1);
        }
    };

    $scope.execute_multiple_action = function(){
        if (!$scope.multiple_action || $scope.multiple_action == ''){
            return;
        }
        var action = $scope.multiple_action_dict[$scope.multiple_action];
        $scope.multiple_action = '';
        var id_list = [];
        angular.forEach($scope.selected, function(value, key){
            if (value){
                id_list.push(key.toString());
            }
        });

        if ($scope.is_link_action(action)){
            var link_params = {
                report_method: action.method,
                items: id_list.join(','),
                global: $scope.report.all_selected_global
            };
            var url = $scope.view.action_link('multiple_action_view', link_params);
            window.location.href = url;
        }else{
            var execute = function(){
                if (action.confirm){
                    $scope.multiple_action_confirm_popup.modal('hide');
                }
                var action_params = {
                    report_method: action.method,
                    items: id_list.join(','),
                    global: $scope.report.all_selected_global
                };
                $scope.view.action('multiple_action', action_params, false).then(function(data){
                    $scope.multiple_succeeded = data.succeeded;
                    $scope.multiple_failed = data.failed;
                    $scope.fetch_report();
                });
            };

            if (action.confirm){
                $scope.multiple_action_confirm_popup.modal('show');
                action.execute = execute;
                $scope.multiple_action_to_confirm = action;
            }else{
                execute();
            }
        }
    };

    $scope.execute_action = function(item, action, force){
        if ($scope.is_link_action(action))
            return;

        if (action.form){
            $scope.form = action;
            $scope.form.item = item;
            $scope.action_form_popup.modal('show');
        } else {
            var execute = function(){
                $scope.view.action('action', {method: action.method, pk: item.item_id}, false).then(function(data){
                    $scope.action_confirm_popup.modal('hide');
                    if (data.item || data.removed_item_id){
                        $scope.update_item(item, data, action.next_on_success);
                        $scope.show_success(data.success);
                        $scope.trigger_success_attr(action);
                    } else {
                        $scope.detail_action = action;
                        $scope.detail_action_content = data;
                        $scope.detail_popup.modal('show');
                    }

                }, function(error){
                    $scope.action_confirm_popup.modal('hide');
                    $scope.show_error(error);
                });
            };

            if (action.confirm && !force){
                action.execute = execute;
                $scope.action_to_confirm = action;
                $scope.action_confirm_popup.modal('show');
            } else {
                execute();
            }
        }
    };

    $scope.trigger_success_attr = function(action){
        var success_attr = $scope.$eval($scope.view.params.success);
        if (success_attr){
            if (success_attr[action.method]){
                $scope.$eval(success_attr[action.method]);
            }
            if (success_attr['__all__']){
                $scope.$eval(success_attr['__all__'])
            }
        }
    };

    $scope.show_success = function(success){
        boApi.messages.push({message: success, level: 25});
    };

    $scope.show_error = function(error){
        $scope.error_message = error;
        $scope.error_popup.modal('show');
    };

    $scope.submit_form = function(form) {
        var data = $scope.action_form_form.serialize();
        var item = form.item;

        $scope.view.action('action', {method: form.method, pk: item.item_id, data: data}, false).then(function(result){
            if (result.success){
                $scope.update_item(item, result, form.next_on_success);
                $scope.show_success(result.success);
                $scope.trigger_success_attr(form);
                $scope.form = null;
                $scope.action_form_popup.modal('hide');
            }else{
                form.form = result.response_form;
                $scope.form = form;
            }
        }, function(error){
            $scope.action_form_popup.modal('hide');
            $scope.show_error(error);
        });
    };

    $scope.execute_inline_form_action = function(item, action, action_form_element){
        var data = action_form_element.serialize();
        $scope.view.action('action', {method: action.method, pk: item.item_id, data: data}, false).then(function(result){
            if (result.success){
                $scope.update_item(item, result, action.next_on_success);
                $scope.show_success(result.success);
                $scope.trigger_success_attr(action);
            }else{
                action.form = result.response_form;
            }
        }, function(error){
            alert(error);
        });
    };

    $scope.fetch_lazy_divs = function(item) {
        var binds = item.extra_information.split('ng-bind-html-unsafe="');
        binds.splice(0, 1);

        var fetchBindIndex = function(i) {
            var bind = binds[i].split('"')[0];
            binds[i] = bind;
            var parts = bind.split('__');
            if (parts[0] == 'lazydiv')
            {
                $http.get($scope.settings.base + 'action/' + parts[2] + '/' + parts[1] + '/').
                success(function(data, status) {
                    $scope[bind] = data;
                }).
                error(function(data, status) {
                    $scope[bind] = 'error';
                });
            }
        };

        for (var i = 0; i < binds.length; i++) {
            fetchBindIndex(i);
        }
    };

    $scope.is_button_action = function(action){
        return !action.form || action.form_via_ajax;
    };

    $scope.is_inline_form_action = function(action){
        return action.form && !action.form_via_ajax;
    };

    $scope.is_link_action = function(action){
        return boUtils.endsWith(action.method, '_view');
    };

    $scope.is_single_action = function(action){
        if (!$scope.single_action || (action.form && !action.form_via_ajax)){
            return false;
        }
        if ($scope.single_action == '*'){
            return true;
        }
        return $scope.single_action.split(',').indexOf(action.method) > -1;
    };

    $scope.get_action_link = function(item, action){
        if ($scope.is_link_action(action))
            return $scope.view.action_link('action_view', {report_method: action.method, pk: item.item_id});
        return '';
    };

    $scope.select_mode = function(){
        return $scope.view.params.selectMode == 'true';
    }
}]);
