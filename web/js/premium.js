function showAlert(message) {
    $("#alert-toast").text(message);
    $("#alert-toast").alert();
    $("#alert-toast").fadeTo(5000, 500).slideUp(500, function() {
        $("#alert-toast").slideUp(500);
    });
}

var role = "";

$("#payment-modal").on("show.bs.modal", function(e) {
    var plan = $(e.relatedTarget).data("plan");
    if (plan == "basic") {
        $("#payment-plan").text("Basic Plan (1 Server)");
        $(this).find("#payment-amount").val("30.00");
        role = "576756461267451934";
    }
    else if (plan == "pro") {
        $("#payment-plan").text("Pro Plan (3 Servers)");
        $(this).find("#payment-amount").val("60.00");
        role = "576754574346551306";
    } else {
        $("#payment-plan").text("Plus Plan (5 Servers)");
        $(this).find("#payment-amount").val("90.00");
        role = "576754671620980740";
    }
});

$("#payment-form").on("submit", function(e) {
    if (this.checkValidity() == false) {
        return;
    }
    var text = $("#paypal-button").text();
    $("#paypal-button").html("<span class=\"spinner-border spinner-border-sm\" role=\"status\" aria-hidden=\"true\"></span> " + text);
    var query = $("#payment-user").val();
    e.preventDefault();
    e.stopPropagation();
    $.ajax({
        url: "https://discordtemplates.me/modmail-search?q=" + encodeURIComponent(query)
    }).done(function(data) {
        var user = null;
        data.forEach(function(value) {
            if (query == $("<textarea/>").html(value.text).text()) {
                user = value.id;
            }
        });
        if (user == null) {
            showAlert("Oops! The user was not found. Perhaps you're not in our support server?");
            $("#paypal-button").text(text);
        } else {
            $("#payment-custom").val(user + "," + role);
            $("#payment-form").unbind("submit").submit();
        }
    }).fail(function(data) {
        showAlert("Oops! An unknown error occurred.")
    });
});

$("#payment-user").typeahead({
    classNames: {
        menu: "form-control p-0 h-auto w-100",
        suggestion: "tt-suggestion form-control border-left-0 border-right-0 border-top-0 rounded-0",
        dataset: "tt-dataset px-2 py-2"
    }
}, {
    source: function(query, syncResults, asyncResults) {
        $.ajax({
            url: "https://discordtemplates.me/modmail-search?q=" + encodeURIComponent(query)
        }).done(function(data) {
            data.forEach(function(value, index) {
                data[index].text = $("<div/>").html(value.text).text();
            });
            asyncResults(data);
        }).fail(function(data) {
            showAlert("Oops! An error occurred while searching.")
        });
    },
    display: function(data) {
        return data.text;
    },
    templates: {
        notFound: function() {
            return "<span class=\"px-2\">No Results Found</span>";
        },
        pending: function() {
            return "<span class=\"px-2\">Searching...</span>";
        },
        suggestion: function(data) {
            return "<div data-id=\"" + data.id + "\">" + data.text + "</div>"
        }
    }
});

window.addEventListener("load", function () {
    var forms = document.getElementsByClassName("needs-validation");
    Array.prototype.filter.call(forms, function(form) {
        form.addEventListener("submit", function(event) {
            if (form.checkValidity() == false) {
                event.preventDefault();
                event.stopPropagation();
                form.classList.add("was-validated");
            }
        }, false);
    });
}, false);
