function getParam(name) {
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)");
    var results = regex.exec(window.location.href);
    if (!results) return null;
    if (!results[2]) return "";
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

var state = getParam("state");
var guildId = getParam("guild_id");

if (state && guildId) {
    $.ajax({
        method: "POST",
        url: "https://api.modmail.xyz/invite/" + state,
        data: {
            guild: guildId
        }
    });
}

window.history.replaceState({}, document.title, window.location.href.split("?")[0]);
