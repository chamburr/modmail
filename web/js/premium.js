function showAlert(message) {
    $("#alert-toast").text(message);
    $("#alert-toast").alert();
    $("#alert-toast").fadeTo(5000, 500).slideUp(500, function() {
        $("#alert-toast").slideUp(500);
    });
}

$("#payment-modal").on("show.bs.modal", function(e) {
    var plan = $(e.relatedTarget).data("plan");
    if (plan == "basic") {
        $("#payment-plan").text("Basic Plan (1 Server)");
        $(this).find("#payment-amount").val("30.00");
        $(this).find("#payment-item").val("ModMail Premium (Basic)");
    }
    else if (plan == "pro") {
        $("#payment-plan").text("Pro Plan (3 Servers)");
        $(this).find("#payment-amount").val("60.00");
        $(this).find("#payment-item").val("ModMail Premium (Pro)");
    } else {
        $("#payment-plan").text("Plus Plan (5 Servers)");
        $(this).find("#payment-amount").val("90.00");
        $(this).find("#payment-item").val("ModMail Premium (Plus)");
    }
});

function getParam(name) {
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)");
    var results = regex.exec(window.location.href);
    if (!results) return null;
    if (!results[2]) return "";
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

function updateUser(user) {
    Cookies.set("user_id", user.id, { expires: 14 });
    $("#payment-custom").val(user.id);
    $("#premium-user").text(user.username + "#" + user.discriminator);
}

var code = getParam("code");
var userId = Cookies.get("user_id");

if (code) {
    window.history.replaceState({}, document.title, window.location.href.split("?")[0]);
    $.ajax({
        url: "https://api.modmail.xyz/user?code=" + encodeURIComponent(code)
    }).done(function(data) {
        updateUser(data);
    }).fail(function(err) {
        showAlert("Oops! An unknown error occurred. Try refreshing?");
    });
}
else if (userId) {
    $.ajax({
        url: "https://api.modmail.xyz/user?id=" + encodeURIComponent(userId)
    }).done(function(data) {
        updateUser(data);
    }).fail(function(err) {
        Cookies.remove("user_id");
        showAlert("Oops! An unknown error occurred. Try refreshing?");
    });
} else {
    window.location.replace("https://discord.com/api/oauth2/authorize?client_id=575252669443211264&redirect_uri=https%3A%2F%2Fmodmail.xyz%2Fpremium&response_type=code&scope=identify");
}
