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
            $("#loading").css("display", "inline");
            location.href = `/?mode=${mode}&query=${ui.item.raw}`;
            return false;
        }
    });
    $('.click').on("click", function () {
        $("#loading").css("display", "inline");
    });
    $('#change_r').on("click", function () {
        location.href = `/?mode=kobun_list&random&range=` + $('#range').val();
    });
    $('#change_s').on("click", function () {
        location.href = `/?mode=kobun_list&range=` + $('#range').val();
    });
    if (mode === "kobun_list") {
        for (let i = 1; i < 352; i++) {
            $(".h" + i).on("click", function () {
                if ($(".m" + i).css("display") === "none") {
                    $(".m" + i).css("display", "block")
                } else {
                    $(".m" + i).css("display", "none")
                }
            });
            $(".m" + i).on("click", function () {
                $(".m" + i).css("display", "none")
            });
        }
    }
});