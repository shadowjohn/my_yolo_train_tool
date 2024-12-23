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
/*
 * 注意事項，value請直接以純字串處理，不建議用什麼boolean，可能會失敗
 * 例如 setMemory("isDrag",true);
 * 那麼，判斷true or false 記得要這樣 if(getMemory("isDrag")=='true'))
 * 要以字串來判斷，最好 setMemory 也當純字串使用 'true'
 */
function setMemory(wtfkey, value) {
    localStorage.setItem(wtfkey, value);
}
function getMemory(wtfkey) {
    return localStorage.getItem(wtfkey);
}
function removeMemory(wtfkey) {
    return localStorage.removeItem(wtfkey);
}
function my_gc(obj) {
    if (typeof obj !== 'object' || obj === null) {
        return; // 傳入非物件或空值，直接返回
    }

    if (Array.isArray(obj)) {
        obj.length = 0; // 清空陣列元素
    } else {
        for (const prop in obj) {
            if (obj.hasOwnProperty(prop)) {
                if (typeof obj[prop] === 'object') {
                    my_gc(obj[prop]); // 遞迴處理子物件
                }
                obj[prop] = null; // 將屬性設置為 null
            }
        }
    }
}
/// <summary>
/// $ra:Array
/// $fields:欄位名稱
/// $headers:中文欄位名稱
/// $classname:使用的style css名稱
/// </summary>
function print_table($ra, $fields, $headers, $classname) {
    $classname = (typeof ($classname) == "undefined" || $classname == '') ? '' : " class='" + $classname + "' ";
    if (typeof ($fields) == "undefined" || $fields == '' || $fields == '*') {

        $tmp = "<table " + $classname + " border='1' cellspacing='0' cellpadding='0'>";
        $tmp += "<thead><tr>";
        for (var k in $ra[0]) {
            $tmp += "<th field=\"" + k + "\">" + k + "</th>";
        }
        $tmp += "</tr></thead>";
        $tmp += "<tbody>";
        for ($i = 0, $max_i = $ra.length; $i < $max_i; $i++) {
            $tmp += "<tr>";
            for (var k in $ra[$i]) {
                $tmp += "<td field=\"" + k + "\">" + $ra[$i][k] + "</td>";
            }
            $tmp += "</tr>";
        }
        $tmp += "</tbody>";
        $tmp += "</table>";
        return $tmp;
    }
    else {
        $tmp = "<table " + $classname + " border='1' cellspacing='0' cellpadding='0'>";
        $tmp += "<thead><tr>";
        $mheaders = $headers.split(',');
        $m_fields = $fields.split(',');
        for (var k = 0, max_k = $mheaders.length; k < max_k; k++) {
            $tmp += "<th field=\"" + $m_fields[k] + "\">" + $mheaders[k] + "</th>";
        }
        $tmp += "</tr></thead>";
        $tmp += "<tbody>";

        for ($i = 0, $max_i = $ra.length; $i < $max_i; $i++) {
            $tmp += "<tr>";
            for (var k = 0, max_k = $m_fields.length; k < max_k; k++) {
                $tmp += "<td field=\"" + $m_fields[k] + "\">" + $ra[$i][$m_fields[k]] + "</td>";
            }
            $tmp += "</tr>";
        }
        $tmp += "</tbody>";
        $tmp += "</table>";
        return $tmp;
    }
}
function print_table_v(ra, fields, show_fields, theclass) {
    var names = [];
    var show_names = [];
    if (count(ra) > 0) {
        for (var k in ra[0]) {
            names.push(k);
            show_names.push(k);
        }
    }
    if (typeof (fields) != "undefined") {
        names = [];
        show_names = [];
        fields = trim(fields);
        show_fields = trim(show_fields);
        var m = explode(",", fields);
        var sm = explode(",", show_fields);
        if (count(m) != count(sm)) {
            alert('Now same array...');
            return;
        }

        for (var i = 0, max_i = count(m); i < max_i; i++) {
            names.push(m[i]);
            show_names.push(sm[i]);
        }
    }
    var table_data = "";
    var class_append = "";
    if (typeof (theclass) != "undefined") {
        class_append += " class=\"" + theclass + "\" ";
    }
    table_data = "<table " + class_append + ">";
    table_data += "<thead>";
    table_data += "<tr>";
    table_data += "<th>項目</th>";
    table_data += "<th colspan=\"" + count(ra) + "\">內容</th>";
    table_data += "</tr>";
    table_data += "</thead>";
    table_data += "<tbody>";
    for (var k = 0, max_k = names.length; k < max_k; k++) {
        table_data += "<tr>";
        table_data += "<th>" + show_names[k] + "</th>";
        for (var i = 0; i < ra.length; i++) {
            for (var obj in ra[i]) {
                if (obj == names[k]) {
                    table_data += "<td fields=\"" + names[k] + "\">" + ra[i][obj] + "</td>";
                }
            }
        }
        table_data += "</tr>";
    }
    table_data += "</tbody>";
    table_data += "</table>";
    return table_data;
}
function smallComment(message, seconds, is_need_motion, cssOptions) {
    //畫面的1/15	
    if ($("#mysmallComment").length == 0) {
        $("body").append("<div id='mysmallComment'><span class='' id='mysmallCommentContent'></span></div>");
        $("#mysmallComment").css({
            'display': 'none',
            'position': 'fixed',
            'left': '0px',
            'right': '0px',
            'padding': '15px',
            'bottom': '3em',
            'z-index': new Date().getTime(),
            'text-align': 'center',
            'opacity': 0.8,
            'pointer-events': 'none'
        });
        $("#mysmallCommentContent").css({
            'color': '#fff',
            'background-color': '#000',
            'padding': '10px',
            'border': '3px solid #fff',
            'pointer-events': 'none'
        });
        /*
        $("#mysmallComment").css({
            'left': (wh['width']-$("#mysmallComment").width())/2+'px' 
        });
        */

        //$("#mysmallComment").corner();
    }

    var mlen = strlen(strip_tags(message));
    var font_size = "16px";
    if (mlen >= 10) {
        font_size = "12px";
    }
    $("#mysmallCommentContent").css({
        'font-size': font_size
    });

    if (typeof (cssOptions) != "undefined") {
        $("#mysmallCommentContent").css(cssOptions);
    }

    $("#mysmallCommentContent").html(message);
    if (is_need_motion == true) {
        $("#mysmallComment").stop();
        $("#mysmallComment").fadeIn("slow");
        clearTimeout(window['smallComment_TIMEOUT']);
        window['smallComment_TIMEOUT'] = setTimeout(function () {
            $("#mysmallComment").fadeOut('fast');
        }, seconds);
    }
    else {
        $("#mysmallComment").stop();
        $("#mysmallComment").show();
        clearTimeout(window['smallComment_TIMEOUT']);
        window['smallComment_TIMEOUT'] = setTimeout(function () {
            $("#mysmallComment").hide();
        }, seconds);
    }
}