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


app.config(['$routeSegmentProvider', '$locationProvider', function($routeSegmentProvider, $locationProvider){
    $routeSegmentProvider.options.autoLoadTemplates = true;
	$routeSegmentProvider.
		when('/', 'home').
        when('/search/:query', 'search').
        when('/:model/:id/', 'model').
        when('/:model/:id/:tab/', 'model.tab').

        segment('home', {controller: 'HomeController', templateUrl: '/home.html'}).
        segment('search', {controller: 'BOSearch', templateUrl: '/search.html'}).
        segment('model', {
            controller: 'BOModelController',
            templateUrl: '/model.html',
            dependencies: ['model', 'id']
//            resolve: {
//                data: function(boApi, $routeSegment) {
//                    //return $timeout(function() { return 'SLOW DATA CONTENT'; }, 2000);
//                    console.log($routeSegment.$routeParams);
//                    return boApi.get('model', 'model_slug=' + encodeURIComponent('user') + '&pk=' + encodeURIComponent('2'));
//                }
//            }
        }).
        within().
            segment('tab', {templateUrl: '/tab.html'}).
        up();

    //$locationProvider.html5Mode(true);
}]);




app.controller('MainController', ['$scope', '$http', '$location', 'boApi', '$routeSegment', function($scope, $http, $location, boApi, $routeSegment){
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

    $scope.search = function(){
        $location.url('/search/' + encodeURIComponent($scope.search_query));
    };



}]);


app.controller('HomeController', ['$scope', function($scope){

}]);


app.controller('BOModelController', ['$scope', '$routeSegment', '$location', '$http', 'boApi', function($scope, $routeSegment, $location, $http, boApi){
    $scope.params = $routeSegment.$routeParams;

    $scope.$on('$routeChangeSuccess', function (){


        boApi.get('model', 'model_slug=' + encodeURIComponent($scope.params.model) + '&pk=' + encodeURIComponent($scope.params.id)).then(function(data){
            $scope.model = data;
        });

    });
}]);

app.controller('BOSearch', ['$scope', '$routeSegment', function($scope, $routeSegment){
    $scope.params = $routeSegment.$routeParams;
}]);
