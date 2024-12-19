function getGET() {
    var output = {};
    output['hash'] = location.hash;
    var _m = location.href.replace(output['hash'], '').split('?');
    _m.shift();
    var pa = _m.join('?');
    if (pa == "") return output;
    var map = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#039;': "'" };
    pa = pa.replace(/&amp;|&lt;|&gt;|&quot;|&#039;/g, function (m) { return map[m]; });
    var mpa = pa.split("&");
    for (var k = 0, max_k = mpa.length; k < max_k; k++) {
        //console.log(mpa[k]);
        var d = mpa[k].split("=");
        output[d[0]] = decodeURIComponent(d[1]);
    }
    return output;
}
function dialogMyBoxOn(message, isTouchOutSideClose, functionAction) {
    $.mybox({
        is_background_touch_close: isTouchOutSideClose,
        message: message,
        css: {
            border: '2px solid #fff',
            backgroundColor: '#000',
            color: '#fff',
            padding: '15px'
        },
        onBlock: function () {
            functionAction();
        }
    });
}
function dialogMyBoxOff() {
    $.unmybox();
}
function myAjax_async_json(url, postdata, func) {
    var method = "POST";
    if (postdata == "") {
        method = "GET";
    }
    $.ajax({
        url: url,
        type: method,
        data: postdata,
        async: true,
        dataType: 'json',
        success: function (html) {
            func(html);
            my_gc(html);
            html = null;
        }
    });
}