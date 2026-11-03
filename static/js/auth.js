// 统一为所有 ajax 请求附加 JWT；未登录或 token 失效时跳回登录页
(function () {
    var token = sessionStorage.getItem('access_token');
    if (token) {
        $.ajaxSetup({
            headers: { 'Authorization': 'Bearer ' + token }
        });
    }
    $(document).ajaxError(function (event, jqXHR) {
        if (jqXHR.status === 401) {
            sessionStorage.clear();
            window.location.href = '/login/';
        }
    });
})();
