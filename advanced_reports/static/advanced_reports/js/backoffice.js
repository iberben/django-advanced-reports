var app = angular.module('BackOfficeApp', ['ngCookies']);

app.run(function ($http, $cookies){
    $http.defaults.headers.common['X-CSRFToken'] = $cookies['csrftoken'];
});

app.config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider){
    $routeProvider.
        when('/', {controller: 'HomeController', templateUrl: '/home.html'}).
        when('/search/:query', {controller: 'BOSearchController', templateUrl: '/search.html'}).
        when('/search/:query/:model/', {controller: 'BOSearchController', templateUrl: '/search.html'}).
        when('/:model/:id/', {controller: 'BOModelController', templateUrl: '/model.html'}).
        when('/:model/:id/:tab/', {controller: 'BOModelController', templateUrl: '/model.html'}).
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
        post: function(method, data){
            var that = this;
            var defer = $q.defer();
            this.requests += 1;
            $http.post(this.url + method + '/', data).success(function (data, status){
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
        isLoading: function(){
            return this.requests > 0;
        }
    };
}]);


app.controller('MainController', ['$scope', '$http', '$location', 'boApi', '$route', function($scope, $http, $location, boApi, $route){
    $scope.path = function(){
        return $location.path();
    };

    $scope.hasRoute = function(){
        return $scope.path() != '/';
    };

    $scope.setup = function(api_url, root_url){
        $scope.api_url = api_url;
        $scope.root_url = root_url;

        boApi.configure(api_url);
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
        if (query.length == 0)
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
        $scope.fetchModel(false);
    });


}]);


app.controller('HomeController', ['$scope', function($scope){

}]);


app.controller('BOModelController', ['$scope', '$route', '$location', '$http', 'boApi', function($scope, $route, $location, $http, boApi){
    $scope.params = $route.current.params;

//    $scope.$on('$routeChangeSuccess', function (){
//        boApi.get('model', 'model_slug=' + encodeURIComponent($scope.params.model) + '&pk=' + encodeURIComponent($scope.params.id)).then(function(data){
//            $scope.$parent.model = data;
//        });
//    });
}]);

app.controller('BOSearchController', ['$scope', '$route', function($scope, $route){
    $scope.params = $route.current.params;
}]);

//
// http://stackoverflow.com/questions/17417607/angular-ng-bind-html-unsafe-and-directive-within-it
//
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


app.directive('view', ['$compile', 'boApi', 'boUtils', function($compile, boApi, boUtils){
    return {
        link: function(scope, element, attrs){
            var slug = attrs.view;
            var params = attrs.params && scope.$eval(attrs.params) || {};
            params.slug = slug;
            var view_instance = attrs.instance || params.slug;

            var attachView = function(data, params){
                data.params = params;
                data.fetch = function(){
                    loadView(data.params);
                };
                data.post = function(post_data){
                    boApi.post_form('view', post_data + '&' + boUtils.toQueryString(params)).then(function(data){
                        attachView(data, params);
                        element.html(data.content);
                        $compile(element.contents())(scope);
                    }, function(error){
                        attachView({}, params);
                        element.html(error);
                    });
                };
                data.action = function(method, action_params){
                    boApi.post('view_action', {
                        method: method,
                        params: action_params || {},
                        view_params: params
                    }).then(function(d){
                        data.fetch();
                    }, function(error){
                        element.html(error);
                    });
                };
                scope.$parent[view_instance] = data;
                scope.view = data;
            };

            var loadView = function(params){
                boApi.get('view', params).then(function(data){
                    attachView(data, params);
                    element.html(data.content);
                    $compile(element.contents())(scope);
                }, function(error){
                    attachView({}, params);
                    element.html(error);
                });
            };
            loadView(params);
        },
        scope: true
    };
}]);

app.directive('postToView', function(){
    return function(scope, element, attrs){
        element.on('submit', function(e){
            scope.$apply(function(){
                scope.view.post(element.serialize());
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
