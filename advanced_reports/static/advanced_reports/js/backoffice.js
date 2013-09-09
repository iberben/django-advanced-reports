var app = angular.module('BackOfficeApp', ['ngCookies']);

app.run(function ($http, $cookies){
    $http.defaults.headers.common['X-CSRFToken'] = $cookies['csrftoken'];
});

app.controller('MainController', ['$scope', '$http', function($scope, $http){

    $scope.setup = function(api_url){
        $scope.api_url = api_url;

        $http.get($scope.api_url + 'search/?q=oemfoe').
        success(function(data, status){
             $scope.results = data;
        });
    };

    $scope.isLoading = function(){
        return $scope.loading;
    };

}]);
