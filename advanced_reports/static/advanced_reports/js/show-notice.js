/* NOTICES */
var queue_notices = [];
var notices = $("#notices");
var total_height = 0;
function show_notice(text, type) {
    var notice = $("<div/>").addClass("notice remove").text(text);
    queue_notices.push(notice); // add to queue
    notices.show().append(notice); // add to notices
    var notice_height = notice.outerHeight();
    
    // add correct class
    if (type == 'error')        {notice.addClass("error");}
    else if (type == 'warning') {notice.addClass("warning");}
    else                        {notice.addClass("success");}

    notice.css("margin-left", ((notice.width()/2)*(-1))+"px");
    notice.css("top", total_height+"px");

    var remove_callback = function(){
        $(this).remove();
        queue_notices = $.grep(queue_notices, function(val){return val != notice;});
        total_height -= notice_height;
        
        $('.notice').animate({top: "-=" + notice_height});
    };

    notice.fadeIn(100);
    setTimeout(function(){
        notice.fadeOut(100, remove_callback);
    }, 5100);

    //notice.fadeIn(100).delay(5000).fadeOut(100, remove_callback);
    
    // add height
    total_height += notice_height;
}
/* END NOTICES */
