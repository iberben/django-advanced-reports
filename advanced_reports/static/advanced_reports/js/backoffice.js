var app = angular.module('BackOfficeApp', ['ngCookies']);

app.run(function ($http, $cookies){
    $http.defaults.headers.common['X-CSRFToken'] = $cookies['csrftoken'];
});

app.config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider){
	$routeProvider.
		when('/', {controller: 'MainController', templateUrl: '/home.html'}).
		when('/:model/:id/', {controller: 'BOModelController', templateUrl: '/model.html'}).
		otherwise({redirectTo: '/'});
    //$locationProvider.html5Mode(true);
}]);

app.factory('boApi', ['$http', '$q', function($http, $q){
    return {
        requests: 0,
        configure: function(url){
            this.url = url;
        },
        get: function(method, params){
            var that = this;
            var defer = $q.defer();
            this.requests += 1;
            $http.get(this.url + method + '/?' + params).success(function (data, status){
                defer.resolve(data);
                that.requests -= 1;
            }).error(function (data, status){
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


app.controller('MainController', ['$scope', '$http', '$location', 'boApi', function($scope, $http, $location, boApi){
    $scope.path = function(){
        return $location.path();
    }

    $scope.setup = function(api_url, root_url){
        $scope.api_url = api_url;
        $scope.root_url = root_url;

        boApi.configure(api_url);

        boApi.get('search', 'q=oemfoe').then(function(data){
            $scope.results = data;
        });
    };

    $scope.isLoading = function(){
        return boApi.isLoading();
    };
}]);


app.controller('BOModelController', ['$scope', '$route', '$location', '$http', function($scope, $route, $location, $http){
    $scope.params = $route.current.params;
}]);
