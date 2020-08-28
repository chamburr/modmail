$(window).scroll(function() {
    if ($(window).scrollTop() > 300) $("#scroll-button").addClass("show");
    else $("#scroll-button").removeClass("show");
});

$(document).ready(function() {
    $("#scroll-button").click(function(e) {
        e.preventDefault();
        $("html, body").animate({scrollTop: 0}, "300");
    });
});
