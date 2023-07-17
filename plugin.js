// ==UserScript==
// @name         EX-M
// @namespace    exm
// @version      0.0.1
// @description  自定义
// @author       erinilis
// @grant        GM_addStyle
// @grant        GM_getResourceText
// @include      *://hotgirl.asia/*
// @require      https://cdn.staticfile.org/toastify-js/1.12.0/toastify.min.js
// @run-at       document-end
// @resource     toastify-css https://cdn.staticfile.org/toastify-js/1.12.0/toastify.min.css
// ==/UserScript==


(function () {
    "use strict";

    GM_addStyle(GM_getResourceText('toastify-css'));

    let url = window.location.href;
    let SERVER_URL = "http://127.0.0.1:7769/"

    let message = (msg) => Toastify({ text: msg, duration: 3000, }).showToast();
    

    // hotgirl.asia
    let hotgirl = /hotgirl\.asia/gm;
    let hotgirl_match = hotgirl.exec(url);
    if (hotgirl_match) {
        console.log("hotgirl.asia match");
        message("插件加载成功");
        let pid = $("[name=id]").val();
        if (pid) {
            let btn = $('<button style="margin-left: 10px;" class="btn btn-info">下载</button>');
            btn.click(function () {
                btn.attr("disabled", true);
                let url_path = "hotgirl/download/" + pid;
                $.getJSON(SERVER_URL + url_path).then((result)=>{
                    if(result.retcode == 0) {
                        message("下载成功 任务ID:" + result.data.task_id);
                        btn.attr("disabled", false);
                    }
                });
            });
            $(".mx-auto").append(btn);
        }
        
    }


})();