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
            //my_gc(html);
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
function basename(filepath) {
    var m = explode("/", filepath);
    var mdata = explode("?", end(m));
    return mdata[0];
}
function mainname(filepath) {
    filepath = basename(filepath);
    var mdata = explode(".", filepath);
    return mdata[0];
}
function subname(filepath) {
    filepath = basename(filepath);
    var m = explode(".", filepath);
    return end(m);
}
function arduino_map(x, in_min, in_max, out_min, out_max) {
    //x = 輸入值
    //in 如 0~255
    //out 如 0~1024
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}
function myAjax(url, postdata) {
    var $method = "POST";
    if (postdata == null || postdata == "") {
        $method = "GET";
    }
    var tmp = $.ajax({
        url: url,
        type: $method,
        data: postdata,
        async: false
    }).responseText;
    return tmp;
}
function getWindowSize() {
    var myWidth = 0, myHeight = 0;
    if (typeof (window.innerWidth) == 'number') {
        //Non-IE
        myWidth = window.innerWidth;
        myHeight = window.innerHeight;
    } else if (document.documentElement && (document.documentElement.clientWidth || document.documentElement.clientHeight)) {
        //IE 6+ in 'standards compliant mode'
        myWidth = document.documentElement.clientWidth;
        myHeight = document.documentElement.clientHeight;
    } else if (document.body && (document.body.clientWidth || document.body.clientHeight)) {
        //IE 4 compatible
        myWidth = document.body.clientWidth;
        myHeight = document.body.clientHeight;
    }
    var a = new Object();
    a['width'] = myWidth;
    a['height'] = myHeight;
    return a;
}
function selectToCheckbox(select_jQDom, options) {
    //用途，把 select 變成 checkbox，當 checkbox 選擇後，等同 select 被切換，表單只需回傳 select 的資料即可，省得寫一堆 checkbox
    //注：my_fix_random 在 myphp.js 裡面，符合資安等級亂數
    //注：原 select 需先加入「multiple="multiple"」，才不會 init 後預選第一筆
    //Version: 0.02
    //Author: 羽山秋人 (https://3wa.tw)
    //
    //return object
    //{ jQDom: 新的 checkbox jquery doms ,html: checkbox_html 內容, reqk: 'selectToCheckbox_{timestame}' }
    //options:
    if (select_jQDom.attr('selectToCheckbox_reqk') != null) {
        //已註冊過 checkbox ，全都移除
        $("*[reqk='" + select_jQDom.attr('selectToCheckbox_reqk') + "']").remove();
        select_jQDom.unbind(select_jQDom.data()["selectToCheckbox_event"]);
    }
    var reqk = 'selectToCheckbox_' + new Date().getTime() + '_' + my_fix_random();
    //把 select 註冊 selectToCheckbox_reqk
    select_jQDom.attr({
        'selectToCheckbox_reqk': reqk,
        'multiple': 'multiple'
    });


    var default_options = {
        "separate": '&nbsp;', //分格符號，預設為空白
        "output_format": "dom", // 可為 dom 或 html，如果單純為 html ，就沒有 jQDom 輸出，但會有註冊屬性的 funnction 回傳，需自行執行 (execute_event)
        "checkboxhtml_to_dom": null, //如果這裡是空值，就會在原來的 select 後面接上
        "class": null //css class，可自定名稱
    };
    if (options != null && typeof (options) == "object") {
        for (var k in options) {
            k = k.toLowerCase();
            switch (k) {
                case 'output_format':
                    default_options[k] = options[k].toLowerCase();
                    break;
                default:
                    default_options[k] = options[k];
                    break;
            }
        }
    }
    var output = new Object();
    output['jQDom'] = null;
    output['html'] = null;
    output['reqk'] = null;
    output['execute_event'] = null;
    if (select_jQDom.length == 0) {
        console.log("Select 不存在...");
        return output;
    }
    // select to array
    var m = new Array();
    var select_option_doms = select_jQDom.find("option");
    for (var i = 0, max_i = select_option_doms.length; i < max_i; i++) {
        var d = {
            'value': select_option_doms.eq(i).val(),
            'value_label': select_option_doms.eq(i).text()
        };
        m.push(d);
    }
    //註冊事件
    output['execute_event'] = function () {
        //當 checkbox 被按到的時候，原來的 select 會變化
        $("input[type='checkbox'][reqk='" + reqk + "']").off().bind("click", {}, function (e) {
            //收集有哪些 checkbox 現在是 checked 是 true，組合成 array
            var checked_doms = $("input[type='checkbox'][reqk='" + reqk + "']:checked");
            var m_true_values = new Array();
            for (var i = 0, max_i = checked_doms.length; i < max_i; i++) {
                m_true_values.push(checked_doms.eq(i).val());
            }
            select_jQDom.val(m_true_values).trigger("change"); //賦值，且可觸發原來  select 的事件
        });
    }.bind(reqk, select_jQDom);
    //如果使用者仍對 select 作 value 操作，也可以改變 checkbox 的值
    select_jQDom.data()["selectToCheckbox_event"] = function (selfDom, reqk) {
        var val = selfDom.val();
        //console.log(val);
        //clean all
        if (val != null) {
            $("input[type='checkbox'][reqk='" + reqk + "']").prop('checked', false);
            for (var i = 0, max_i = val.length; i < max_i; i++) {
                $("input[type='checkbox'][reqk='" + reqk + "']").filter("[value='" + val[i] + "']").prop('checked', true);
            }
        }
    };
    select_jQDom.bind("change", {
        "selfDom": select_jQDom,
        "reqk": reqk
    }, function (e) {
        e.data.selfDom.data()["selectToCheckbox_event"](e.data.selfDom, e.data.reqk);
    });
    //產生 checkbox 內容
    var m_checkbox_html = new Array();
    var select_jQDom_nowValue = select_jQDom.val();
    m.map(function (item) {
        var strIsChecked = "";
        if (select_jQDom_nowValue.includes(item.value)) {
            strIsChecked = " checked ";
        }
        var d = `<label><input type="checkbox" reqk="${reqk}" value="${item.value}" name="${reqk}" ${strIsChecked}>${item.value_label}</label>`;
        m_checkbox_html.push(d);
    });
    output['html'] = "<span reqk='" + reqk + "' ";
    if (default_options['class'] != null) {
        output['html'] += ` class="${default_options['class']}"`;
    }
    output['html'] += ">";
    output['html'] += m_checkbox_html.join(default_options.separate) + "</span>";
    if (default_options.output_format == "dom") {
        if (default_options.checkboxhtml_to_dom != null) {
            //使用者有指定要放哪，直接蓋掉
            default_options.checkboxhtml_to_dom.html(output['html']);
        } else {
            //如果是 null，就 after 到原來的 select
            select_jQDom.after(output['html']);
        }
        output['jQDom'] = $("input[reqk='" + reqk + "']");
    }
    //隱藏原來的 select
    $(select_jQDom).hide();
    //執行事件
    output['execute_event']();
    //輸出結果
    /*
      output['jQDom'] checkbox 的 jquery 物件們(陣列)
      output['html'] checkbox 最後集合的 html 文字內容;
      output['reqk'] checkbox 裡 reqk 的臨時編號
      output['execute_event'] 如果使用 html 回傳，那就要自行執行此 function 才有 select 、checkbox 雙向事件綁定
    */
    return output;
}
function myW(html, func, cssOption) {
    if (typeof (window['myW_t']) == "undefined") {
        window['myW_t'] = 0;
    }
    $.fn.center = function () {
        this.css("position", "absolute");
        this.css("top", ($(window).height() - this.height()) / 2 + $(window).scrollTop() + "px");
        this.css("left", ($(window).width() - this.width()) / 2 + $(window).scrollLeft() + "px");
        return this;
    }
    var t = new Date().getTime() + "_" + window['myW_t']++;
    var id = "myW_" + t;
    $("body").append("<div id='" + id + "'></div>");
    $("#" + id).css({
        'position': 'absolute',
        'z-index': new Date().getTime(),
        'padding': '3px',
        'background-color': '#fff',
        'color': 'black',
        'border': '2px solid #00f'
    });
    if (typeof (cssOption) != "undefined" && typeof (cssOption) == "object") {
        for (var k in cssOption) {
            $("#" + id).css(k, cssOption[k]);
        }
    }
    html = html.replace("{myW_id}", id);
    $("#" + id).html(html);
    $(window).bind("scroll", { id: id }, function (event) {
        $("#" + event.data.id).center();
    });
    $("#" + id).center();
    func(id);
    return id;
}
