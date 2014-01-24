/**
 * Notification, the $(window).load() is removed, is not needed here.
 * Neither $(document).ready isnt needed here since the JavaScript is loaded at the bottom of the page.
 * The DOM is already loaded then
 *
 * @author  Kristof Houben <kristof.houben@mobilevikings.com>
 */

/**
 * Example code
 *
 */

/*$(function(){

 var params = {
 message: 'Great job there! :)',
 type: 'success',
 isAutoHide: true
 }

 frontend.notification.show(params);

 var params = {
 isFadeOut: true
 }

 frontend.notification.hide(params);

 });
*/

frontend.notification = (function()
{
    var element = null;

    var methods = {

        /**
         * Show
         *
         * Config params:
         *  - param message string
         *  - param type (success, error, neutral, ladies)
         *  - param isAutoHide true/false
         *
         * @param arguments object with config params
         */
        show: function(arguments){

            if(element.length > 0){

                methods.hide({
                    isFadeOut: false
                });

                element.removeClass().addClass('notification');
                element.html(arguments.message).addClass(arguments.type).show();

                if(arguments.isAutoHide){
                    setTimeout(function(){
                        element.fadeOut();
                    }, 8000);
                }

                return element.html();

            } else {
                console.error('An element with id "notification" does not exist, you basterd!');
                return null;
            }
        },


        /**
         * Hide
         *
         * @param arguments
         */
        hide: function(arguments){

            if(arguments.isFadeOut){
                element.fadeOut(400, function(){
                    element.html('');
                });
            }else{
                element.hide();
                element.html('');
            }

            return element.html();

        },

        /**
         * Initialize the lib.  We create a reference to the notification div
         */
        init: function() {
            element = $('#notification');

            element.on('click', function(){
                element.hide();
            });
        }
    };

    return methods;
})();

// frontend.stickyNotification = (function()
// {
//     var element = null;

//     var methods = {

//         hide: function(arguments){

//             if(arguments.isFadeOut){
//                 element.fadeOut(400, function(){
//                     element.html('');
//                 });
//             }else{
//                 element.hide();
//                 element.html('');
//             }

//             return element.html();

//         },

//         /**
//          * Initialize the lib.  We create a reference to the notification div
//          */
//         init: function() {
//             element = $('.sticky-notification');
            
//             if (!element.hasClass('no-close')) {
//                 if($.cookie("sticky-notification") === "hidden"){
//                     element.hide();
//                 }
                
//                 element.on('click', function(){
//                     element.hide();
//                     $.cookie("sticky-notification", "hidden", { path: '/', expires: 1 });
//                 });
//             }
//         }
//     };
    
//     methods.init();
    
//     return methods;
// })();
