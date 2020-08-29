var id = window.location.href.split("/").pop().split(".")[0];

if (id == "logs") {
    $("#logs-content").text("Invalid URL. Please try again.")
} else {
    $.ajax({
        url: "https://modmail.xyz/_functions/fetch-logs?id=" + id
    }).done(function(data) {
        $("#logs-content").text("");
        data.forEach(function(value) {
            var colour = value.role == "Staff" ? "FF4500" : value.role == "User" ? "00FF00" : "6C757D";
            var content = '<div class="card bg-dark my-2 border-0"> \
    <div class="card-title mb-1"> \
        <span style="color: #' + colour + '"> \
            ' + value.username + '#' + value.discriminator + '\
        </span> \
        <span class="text-muted">' + value.timestamp + '</span> \
    </div> \
    <div class="card-body px-0 pt-0 pb-2"> \
        ' + value.message;
            if (value.attachments.length != 0) {
                var supported = ['.bmp', '.gif', '.jpg', 'jpeg', '.png'];
                content += '\
        <div class="row mt-2">';
                for (let element of value.attachments) {
                    if (supported.includes(element.slice(-4).toLowerCase())) {
                        content += '\
            <div class="col flex-grow-0"> \
                <a href="' + element + '" target="_blank"> \
                    <img src="' + element + '" alt="' + element + '" style="max-width: 300px;"> \
                </a> \
            </div>'
                    } else {
                        content += '\
            <div class="col-12"> \
                <a href="' + element + '" target="_blank">' + element + '</a> \
            </div>';
                    }
                }
                content += '\
        </div>';
            }
            content += '\
    </div> \
</div>';
            $("#logs-content").append(content)
        });
    }).fail(function(data) {
        $("#logs-content").text("Error: " + data.responseJSON.error);
    });
}