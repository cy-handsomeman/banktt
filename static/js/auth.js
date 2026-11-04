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

// 统一从后台错误响应中提取可读提示，避免前端把失败当成功
window.parseApiError = function (xhr, fallback) {
    if (xhr && xhr.status === 0) {
        return '无法连接服务器，请检查网络';
    }
    var data = xhr && xhr.responseJSON;
    if (data) {
        if (typeof data === 'string') return data;
        if (data.detail) return String(data.detail);
        if (data.message) return String(data.message);
        if (data.non_field_errors) return data.non_field_errors.join('；');
        var key = Object.keys(data)[0];
        if (key) {
            var value = data[key];
            return (Array.isArray(value) ? value.join('；') : String(value));
        }
    }
    if (xhr && xhr.status === 403) return fallback || '没有权限执行该操作';
    if (xhr && xhr.status >= 500) return '服务器内部错误，请稍后重试';
    return fallback || '操作失败';
};
