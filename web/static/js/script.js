$(function () {
    $.ui.autocomplete.prototype._renderItem = function (ul, item) {
        return $("<li></li>")
            .data("item.autocomplete", item)
            .append(
                $("<div></div>")
                    .html(item.label)
                    .append($("<div class='complete_category'></div>").html(item.category))
            )
            .appendTo(ul);
    };
    $("#keyword").autocomplete({
        source: function (request, response) {
            $.ajax({
                type: "GET",
                url: `/complete?mode=${mode}&query=` + request.term,
                contentType: "application/json",
                dataType: "json"
            }).done(function (res) {
                response(res)
            }).fail(function (res) {
                response([]);
            });
        },
        select: function (event, ui) {
            location.href = `/?mode=${mode}&query=${ui.item.raw}`;
            return false;
        }
    });
});