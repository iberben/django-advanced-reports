var app = angular.module('BackOfficeApp', ['ngCookies']);

app.run(function ($http, $cookies){
    $http.defaults.headers.common['X-CSRFToken'] = $cookies['csrftoken'];
});

app.config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider){
    $routeProvider.
        when('/', {controller: 'EmptyController', templateUrl: '/home.html'}).
        when('/tab/:tab/', {controller: 'EmptyController'}).

        when('/search/:query', {controller: 'EmptyController', templateUrl: '/search.html', reloadOnSearch: false}).
        when('/search/:query/:model/', {controller: 'EmptyController', templateUrl: '/search.html', reloadOnSearch: false}).
        when('/:model/:id/', {controller: 'EmptyController', templateUrl: '/model.html', reloadOnSearch: false}).
        when('/:model/:id/:tab/', {controller: 'EmptyController', templateUrl: '/model.html', reloadOnSearch: false}).
        when('/:model/:id/:tab/:detail/', {templateUrl: '/model.html', reloadOnSearch: false}).
        otherwise({redirectTo: '/'});
    //$locationProvider.html5Mode(true);
}]);

app.factory('boApi', ['$http', '$q', 'boUtils', function($http, $q, boUtils){
    return {
        requests: 0,
        configure: function(url){
            this.url = url;
        },
        get: function(method, params){
            var that = this;
            var defer = $q.defer();
            this.requests += 1;
            $http.get(this.url + method + '/?' + boUtils.toQueryString(params)).
            success(function (data, status){
                defer.resolve(data);
                that.requests -= 1;
            }).
            error(function (data, status){
                defer.reject(status);
                that.requests -= 1;
            });
            return defer.promise;
        },
        post: function(method, data, url_suffix){
            var that = this;
            var defer = $q.defer();
            this.requests += 1;
            $http.post(this.url + method + '/' + (url_suffix || ''), data).success(function (data, status){
                defer.resolve(data);
                that.requests -= 1;
            }).error(function (data, status){
                defer.reject(status);
                that.requests -= 1;
            });
            return defer.promise;
        },
        post_form: function(method, data){
            var that = this;
            var defer = $q.defer();
            this.requests += 1;
            $http({
                method: 'POST',
                url: this.url + method + '/',
                data: data,
                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
            }).success(function (data, status){
                defer.resolve(data);
                that.requests -= 1;
            }).error(function (data, status){
                defer.reject(status);
                that.requests -= 1;
            });
            return defer.promise;
        },
        put: function(method, data){
            var that = this;
            var defer = $q.defer();
            this.requests += 1;
            $http.put(this.url + method + '/', data).success(function (data, status){
                defer.resolve(data);
                that.requests -= 1;
            }).error(function (data, status){
                defer.reject(status);
                that.requests -= 1;
            });
            return defer.promise;
        },
        link: function(method, params){
            return this.url + method + '/?' + boUtils.toQueryString(params);
        },
        isLoading: function(){
            return this.requests > 0;
        }
    };
}]);

app.controller('MainController', ['$scope', '$http', '$location', 'boApi', '$route', 'boReverser', function($scope, $http, $location, boApi, $route, boReverser){
    $scope.params = {};

    $scope.path = function(){
        return $location.path();
    };

    $scope.useView = function(){
        var p = $scope.path();
        return !(p.substring(0, 5) == '/tab/' || p == '/');
    };

    $scope.setup = function(api_url, root_url){
        $scope.api_url = api_url;
        $scope.root_url = root_url;

        boApi.configure(api_url);
        boReverser.configure(['model', 'id', 'tab', 'detail']);
    };

    $scope.isLoading = function(){
        return boApi.isLoading();
    };

    $scope.search_results_preview_visible = false;
    $scope.search_reset_results_preview = function(){
        $scope.search_results_preview_visible = false;
        $scope.search_results_preview = null;
    };

    $scope.search_show_results_preview = function(){
        $scope.search_results_preview_visible = true;
    }

    $scope.is_search_results_preview_visible = function(){
        var visible = $scope.search_results_preview_visible && $scope.search_query.length > 0;
        if ($scope.search_results_preview_visible && !visible)
            $scope.search_reset_results_preview();
        return visible;
    };

    $scope.search_preview = function(query){
        if (!query || query.length == 0)
            return;
        boApi.get('search_preview', {q: query}).then(function(data){
            $scope.search_results_preview = data;
        }, function(error){
            $scope.search_results_preview = null;
        });
    };

    $scope.goto_search = function(){
        $scope.search_reset_results_preview();
        if ($scope.search_query.length > 0)
            $location.url('/search/' + encodeURIComponent($scope.search_query));
    };

    $scope.search = function(query, filter_model){
        var params = filter_model ? {q: query, filter_model: filter_model} : {q: query};
        boApi.get('search', params).then(function(data){
            $scope.search_results = data;

        }, function(error){
            $scope.search_results = null;
        });
    };

    $scope.get_params = function(){
        if ($route && $route.current && $route.current.params)
            return $route.current.params;
        return {};
    };

    $scope.currentModel = '';

    $scope.fetchModel = function(force){
        // Fetches the model if needed (if not already fetched)
        var params = $scope.get_params();

        if (params.model && params.id)
        {
            var newModel = params.model + '/' + params.id;
            if ($scope.currentModel != newModel || force){
                $scope.currentModel = newModel;
                boApi.get('model', {model_slug: params.model, pk: params.id}).then(function(data){
                    $scope.model = data;
                    if (!params.tab)
                        $route.current.params.tab = $scope.model.meta.tabs[0].slug;
                });
            }
        }
    };

    $scope.$on('$routeChangeSuccess', function (){
        $scope.params = $route.current.params;
        $scope.fetchModel(false);
    });

    $scope.get_url = function(url_params){
        return boReverser.reverse(url_params);
    };

    $scope.isVisibleTab = function(tab){
        return !tab.shadow;
    };
}]);

app.factory('boReverser', ['$route', 'boUtils', function($route, boUtils){
    return {
        configure: function(hierarchy, prefix){
            this.hierarchy = hierarchy;
            this.prefix = prefix || '#/';},

        reverse: function(url_params){
            var search = {};
            var hasSearch = false;
            var highestLevel = this.hierarchy.length;
            var params = angular.copy($route.current.params);
            for (var k in url_params){
                if (url_params.hasOwnProperty(k)){
                    if (this.hierarchy.indexOf(k) >= 0){
                        params[k] = url_params[k];
                        var level = this.hierarchy.indexOf(k);
                        if (level < highestLevel)
                            highestLevel = level;}
                    else{
                        search[k] = url_params[k];
                        hasSearch = true;}}}

            for (var l in params){
                if (params.hasOwnProperty(l)){
                    var level2 = this.hierarchy.indexOf(l);
                    if (!url_params[l] && level2 > highestLevel || level2 == -1){
                        delete params[l];}}}

            var pathSegments = [];
            for (var i = 0; i < this.hierarchy.length; i++){
                var segmentName = this.hierarchy[i];
                if (params[segmentName])
                    pathSegments.push(params[segmentName]);}

            var url = this.prefix + pathSegments.join('/') + '/';
            if (hasSearch){
                url += '?' + boUtils.toQueryString(search);}

            return url;
        }
    };
}]);

app.controller('EmptyController', ['$scope', function($scope){}]);

// http://stackoverflow.com/questions/17417607/angular-ng-bind-html-unsafe-and-directive-within-it
app.directive('compile', ['$compile', function ($compile){
    return {
        link: function(scope, element, attrs) {
            scope.$watch(function(scope){
                // watch the 'compile' expression for changes
                return scope.$eval(attrs.compile);
            }, function(value){
                // when the 'compile' expression changes
                // assign it into the current DOM
                element.html(value);

                // compile the new DOM and link it to the current
                // scope.
                // NOTE: we only compile .childNodes so that
                // we don't get into infinite loop compiling ourselves
                $compile(element.contents())(scope);
            });
        },
        scope: true
    };
}]);

app.directive('view', ['$compile', '$q', 'boApi', 'boUtils', '$timeout', function($compile, $q, boApi, boUtils, $timeout){
    return {
        link: function(scope, element, attrs){
            var slug = attrs.view;
            var params = attrs.params && scope.$eval(attrs.params) || {};
            params.view_slug = slug;
            var viewInstance = attrs.instance || slug;
            var internalScope = scope.$new();
            var viewToUpdateOnPost = attrs.viewToUpdateOnPost;

            var compile = function(data){
                attachView(data, params);
                element.html(data.content);
                $compile(element.contents())(internalScope);
            };

            var showError = function(error){
                attachView({}, params);
                element.html(error);
            };

            var attachView = function(data, params){
                data.params = params;
                data.fetch = function(){
                    loadView(data.params);
                };
                data.post = function(post_data, closeModalFirst){
                    var actual_post = function(){
                        boApi.post_form('view', post_data + '&' + boUtils.toQueryString(params)).then(function(data){
                            compile(data);
                            if (viewToUpdateOnPost){
                                scope.$eval(viewToUpdateOnPost).fetch();}
                            if (!data.success){
                                $timeout(function(){
                                    scope.$parent.$broadcast('boValidationError');
                                }, 100);
                            }
                        }, showError);
                    };
                    if (closeModalFirst){
                        scope.$parent.$broadcast('boRequestCloseModal', actual_post);}
                    else {
                        actual_post();}
                };
                data.action = function(method, actionParams, reloadViewOnSuccess, url_suffix){
                    return boApi.post('view_action', {method: method, params: actionParams || {}, view_params: params
                    }, url_suffix).then(function(result){
                        if (angular.isUndefined(reloadViewOnSuccess) || reloadViewOnSuccess)
                            data.fetch();
                        return result;
                    }, function(error){
                        if (angular.isUndefined(reloadViewOnSuccess) || reloadViewOnSuccess)
                            showError(error);
                        return error;
                    });
                };
                data.action_link = function(method, actionParams){
                    var combinedParams = angular.extend({method: method}, params, actionParams);
                    return boApi.link('view_view', combinedParams);
                };
                scope[viewInstance] = data;
                internalScope.view = data;
            };

            var loadView = function(params){
                boApi.get('view', params).then(compile, showError);
            };

            loadView(params);
        },
        scope: false
    };
}]);

app.directive('postToView', function(){
    return function(scope, element, attrs){
        var closeModalFirst = scope.$eval(attrs.closeModalFirst);
        element.on('submit', function(e){
            scope.$apply(function(){
                scope.view.post(element.serialize(), closeModalFirst);
            });
        });
    };
});

app.directive('keyupDelay', ['$parse', '$timeout', function($parse, $timeout){
    return function(scope, element, attrs){
        var to = null;
        var fn = $parse(attrs.keyupDelay);
        var delay = scope.$eval(attrs['delay'] || "'500'");
        element.on('keyup', function(event){
            scope.$apply(function(){
                if (to)
                    $timeout.cancel(to);
                to = $timeout(function(){
                    fn(scope, {$event: event});
                }, delay);
            });
        });
    };
}]);

app.factory('boUtils', function(){
   return {
       toQueryString: function(obj){
           var str = [];
           for(var p in obj)
               str.push(encodeURIComponent(p) + '=' + encodeURIComponent(obj[p]));
           return str.join('&');
       },
       startsWith: function(str, prefix){
           // http://stackoverflow.com/questions/646628/javascript-startswith
           return str.indexOf(prefix) === 0;
       },
       endsWith: function(str, suffix){
           // http://stackoverflow.com/questions/280634/endswith-in-javascript
           return str.indexOf(suffix, str.length - suffix.length) !== -1;
       }
   };
});

app.filter('capitalize', function(){
    return function(input){
        if (input.length > 0)
            return input.charAt(0).toUpperCase() + input.slice(1);
        return '';
   };
});

app.filter('uriencode', function(){
    return encodeURIComponent;
});

app.directive('boElement', ['$parse', function($parse){
    return function(scope, element, attrs){
        var obj = $parse(attrs.boElement);
        obj.assign(scope, element);
    };
}]);

app.directive('focusOn', function() {
    return function(scope, elem, attr) {
        scope.$on(attr.focusOn, function(e, event_attr) {
            if (!event_attr || attr.focusAttr == '' + event_attr)
            {
                // http://stackoverflow.com/questions/17384464/jquery-focus-not-working-in-chrome
                setTimeout(function(){
                    elem[0].focus();
                }, 100);
            }
        });
    };
});

/*
<ul class="always-visible dropdown-menu" ng-show="is_search_results_preview_visible()">
    {% verbatim %}
    <li ng-repeat="result in search_results_preview.results">
        <a href="{{ root_url }}#{{ result.path }}">
            <small>{{ result.verbose_name }}</small> {{ result.title }}
        </a>
    </li>
    {% endverbatim %}
    <li ng-show="!search_results_preview" class="disabled">
        <a><img src="{{ STATIC_URL }}advanced_reports/img/modybox/loading.gif"></a>
    </li>
    <li ng-show="search_results_preview.results.length == 0" class="disabled">
        <a>{% trans "No results found" %}</a>
    </li>
</ul>
 */

app.directive('onFocus', ['$parse', function($parse){
    return function(scope, element, attrs){
        var fn = $parse(attrs.onFocus);
        element.on('focus', function(event){
            scope.$apply(function(){
                fn(scope, {$event: event});
            });
        });
    };
}]);

app.factory('idGenerator', function(){
    return {
        nextId: 0,
        generate: function(){
            this.nextId += 1;
            return this.nextId;
        }
    };
});

app.directive('autoComplete', ['$timeout', '$compile', 'idGenerator', function($timeout, $compile, idGenerator){
    return {
        link: function(scope, element, attrs){
            // Generate a unique ID to connect the datalist to the field.
            var elementId = 'autoComplete-' + idGenerator.generate();

            // The datalist template that we will put after the field.
            var datalistTemplate = '' +
                '<datalist id="' + elementId + '">' +
                '<option ng-repeat="option in options" value="{{ option }}"></option>' +
                '</datalist>';

            // Put the template after the field and connect it to newScope.
            element.after(datalistTemplate);
            var newScope = scope.$new();
            $compile(element.next().contents())(newScope);
            element.attr('list', elementId);

            // Update the datalist on each keystroke with a throttling of 200 ms.
            var to = null;
            element.on('input', function(event){
                if (to)
                    $timeout.cancel(to);
                to = $timeout(function(){
                    var params = angular.extend({partial: element.val()}, scope.$eval(attrs.params || '{}'));
                    scope.view.action(attrs.autoComplete, params, false).then(function(results){
                        newScope.options = results;
                        // If we have one or more results, prefill the first one in the field and select it
                        // in a way that you can continue typing.
                        if (results.length > 0){
                            var idx = results[0].indexOf(element.val());
                            if (idx > -1){
                                var start = element.selectionStart;
                                element.val(results[0].substring(0, idx + element.val().length));
                                element.selectionStart = start;
                                element.selectionEnd = element.val().length;
                            }
                        }
                    });
                }, 200);
                scope.$apply();
            });
        },
        scope: false
    };
}]);

app.directive('autoCompleteOld', ['$timeout', 'boUtils', function($timeout, boUtils){
    return {
        template: '' +
            '<span ng-transclude></span>' +
            '<ul class="always-visible dropdown-menu" ng-show="showCompletions">' +
            '    <li ng-repeat="result in results">' +
            '        <a href on-focus="fillOutCompletion(result)" ng-mouseenter="fillOutCompletion(result)" ng-click="fillOutCompletion(result); show(false)">{{ result }}</a>' +
            '    </li>' +
            '    <li ng-hide="results" class="disabled"><a>{{ txt_no_results }}</a></li>' +
            '</ul>' +
            '',
        link: function(scope, element, attrs){
            element.css('position', 'relative');
            var to = null;
            var input = element.find('input,textarea');
            var transcludedScope = scope.$$nextSibling;

            scope.showCompletions = false;
            scope.model = transcludedScope[scope.modelName];
            scope.results = [];

            scope.$watch(function(scope){
                return input.val();
            }, function(value){
                scope.model = value;
            });

            scope.$watch('model', function(value){
                var start = input[0].selectionStart;
                var oldValue = input.val();
                input.val(value);
                input[0].selectionStart = start;
                input[0].selectionEnd = value.length;
            });

            scope.fillOutCompletion = function(value){
                scope.model = value;
            };

            scope.show = function(show){
                scope.showCompletions = show;
            };

            input.on('keyup', function(event){
                if (to)
                    $timeout.cancel(to);
                if (event.keyCode == 8 || event.keyCode == 46 || event.keyCode == 9)
                {
                    scope.showCompletions = false;
                    scope.$apply();
                    return;
                }
                scope.showCompletions = true;
                to = $timeout(function(){
                    var params = angular.extend({partial: input.val()}, scope.$eval(attrs.params || '{}'));
                    scope.view.action(attrs.autoCompleteOld, params, false).then(function(results){
                        scope.results = results;
                        if (results.length > 0 && boUtils.startsWith(results[0], scope.model))
                            scope.model = results[0];
                    });
                }, 150);
                scope.$apply();
            });

            input.on('blur', function(event){
                scope.showCompletions = false;
                scope.$apply();
            });
        },
        scope: {
            txt_no_results: '@noResultsText',
            view: '=viewObject',
            model: '='
        },
        replace: false,
        transclude: true
    };
}]);


app.directive('linkTo', function(){
   return function(scope, element, attrs){
       var url = scope.$eval(attrs.linkTo);
       element.attr('href', url);
   };
});


app.directive('boModal', function(){
    return {
        templateUrl: '/modal.html',
        scope: {
            boModal: '=',
            modalTitle: '@',
            onYes: '&'
        },
        transclude: true,
        link: function(scope, element, attrs){
            scope.boModal.on('hidden.bs.modal', function(event){
                scope.$apply(function(){
                    if (scope.fnToExecute){
                        scope.fnToExecute();
                        scope.fnToExecute = null;
                    }
                });
            });


            scope.$parent.$on('boRequestCloseModal', function(e, fnToExecute){

                scope.fnToExecute = fnToExecute;
                scope.boModal.modal('hide');
            });
            scope.$parent.$on('boValidationError', function(){
                scope.boModal.modal('show');
            });
        }
    };
});
