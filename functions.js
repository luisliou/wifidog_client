/**
 * Created by Kay on 2016/3/8.
 */
function login() {
 
    var token = document.getElementById("token");
 
    if (token.value == "") {
 
        alert("请输入验证码");
 
    } else {
 
        window.location.assign("http://192.168.20.1:2060/wifidog/auth?token=" + token.value);
 
    }
 
}

