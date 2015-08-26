var myApp = angular.module('myApp', ['ngRoute']);
myApp.config(['$routeProvider',
    function($routeProvider) {
        $routeProvider
            .when('/', {
                templateUrl: '{{ site.baseurl }}/partials/force.html',
                controller: 'ForceController',
            })
            .when('/item/:itemId', {
                templateUrl: '{{ site.baseurl }}/partials/item-detail.html',
                controller: 'ItemController',
            })
            .otherwise({
                redirectTo: '/'
            });
    }
]);