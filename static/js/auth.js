// 统一为所有 ajax 请求附加 JWT；access 过期时自动用 refresh 换新并重放请求
(function () {
    var TOKEN_KEY = 'access_token';
    var REFRESH_KEY = 'refresh_token';

    function applyToken(token) {
        if (token) {
            $.ajaxSetup({ headers: { 'Authorization': 'Bearer ' + token } });
        }
    }

    applyToken(sessionStorage.getItem(TOKEN_KEY));

    function clearAndRedirect() {
        sessionStorage.clear();
        window.location.href = '/login/';
    }

    var refreshInFlight = false;
    var pendingRequests = [];

    function runRefresh() {
        var refresh = sessionStorage.getItem(REFRESH_KEY);
        if (!refresh) {
            clearAndRedirect();
            return;
        }
        refreshInFlight = true;
        $.ajax({
            url: '/api/token/refresh/',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ refresh: refresh }),
            dataType: 'json'
        }).done(function (res) {
            refreshInFlight = false;
            var access = res && res.access;
            if (!access) {
                clearAndRedirect();
                return;
            }
            sessionStorage.setItem(TOKEN_KEY, access);
            applyToken(access);
            // 用新 token 重放等待中的请求
            var retryList = pendingRequests.splice(0);
            retryList.forEach(function (settings) { $.ajax(settings); });
        }).fail(function () {
            refreshInFlight = false;
            pendingRequests = [];
            clearAndRedirect();
        });
    }

    $(document).ajaxError(function (event, jqXHR, settings) {
        if (jqXHR.status !== 401) {
            return;
        }
        // 刷新接口本身失败时不再重试，直接回登录页
        if (settings && /\/api\/token\/refresh\//.test(settings.url || '')) {
            clearAndRedirect();
            return;
        }
        // 每个请求最多重放一次，避免死循环
        if (settings && settings._authRetried) {
            clearAndRedirect();
            return;
        }
        if (settings) {
            settings._authRetried = true;
            pendingRequests.push(settings);
        }
        if (!refreshInFlight) {
            runRefresh();
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
        if (data.error) return String(data.error);
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
