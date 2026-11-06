let paginationInfo = {
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};
const API_BASE_URL = '/api/login_log/';

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[m]));
}

function renderTable(data) {
    const tbody = $('#dataTableBody');
    if (!data || data.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="6">暂无登录日志</td></tr>');
        return;
    }
    let html = '';
    data.forEach(item => {
        const time = item.login_time ? item.login_time.replace('T', ' ').slice(0, 19) : '—';
        const ok = item.status === '成功';
        html += `<tr>
            <td>${time}</td>
            <td>${escapeHtml(item.user_name || '—')}</td>
            <td><span style="font-weight:600;color:${ok ? '#047857' : '#dc2626'};">${escapeHtml(item.status)}</span></td>
            <td>${escapeHtml(item.login_ip || '—')}</td>
            <td title="${escapeHtml(item.user_agent || '')}">${escapeHtml((item.user_agent || '—').slice(0, 60))}</td>
            <td>${escapeHtml(item.message || '—')}</td>
        </tr>`;
    });
    tbody.html(html);
}

function showToast(msg, duration = 2000) {
    let toastEl = $('#dynamicToast');
    if (toastEl.length === 0) {
        $('body').append('<div id="dynamicToast" style="position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:#2c3e50; color:white; padding:10px 20px; border-radius:40px; z-index:2000; font-size:0.85rem; box-shadow:0 5px 12px rgba(0,0,0,0.2); opacity:0; transition:0.2s; pointer-events:none;"></div>');
        toastEl = $('#dynamicToast');
    }
    toastEl.text(msg).css('opacity', '1');
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => { toastEl.css('opacity', '0'); }, duration);
}

function fetchList(page = 1) {
    return $.ajax({
        url: `${API_BASE_URL}?page=${page}&page_size=${paginationInfo.pageSize}`,
        method: 'GET',
        timeout: 5000,
        contentType: 'application/json'
    }).then(response => {
        let data = [];
        let count = 0;

        if (Array.isArray(response)) {
            data = response;
            count = data.length;
        } else if (response && response.data && Array.isArray(response.data)) {
            data = response.data;
            count = response.count || data.length;
        } else if (response && response.results && Array.isArray(response.results)) {
            data = response.results;
            count = response.count || data.length;
        }

        paginationInfo.currentPage = page;
        paginationInfo.totalCount = count;
        paginationInfo.totalPages = Math.max(1, Math.ceil(count / paginationInfo.pageSize));

        renderTable(data);
        $('#totalCount').text(count);
        $('#currentPage').text(paginationInfo.currentPage);
        $('#totalPages').text(paginationInfo.totalPages);

        const $wrapper = $('#paginationWrapper');
        if (count <= paginationInfo.pageSize) {
            $wrapper.hide();
        } else {
            $wrapper.show();
            $('#firstPageBtn, #prevPageBtn').prop('disabled', paginationInfo.currentPage === 1);
            $('#nextPageBtn, #lastPageBtn').prop('disabled', paginationInfo.currentPage >= paginationInfo.totalPages);
        }
        return data;
    }).catch(err => {
        console.error('获取登录日志失败:', err);
        renderTable([]);
        showToast(parseApiError(err, '获取登录日志失败'), 2500);
        return null;
    });
}

$(document).ready(function() {
    fetchList();
    $('#refreshBtn').on('click', function() { paginationInfo.currentPage = 1; fetchList(1); showToast('已刷新', 1500); });
    $('#firstPageBtn').on('click', function() { paginationInfo.currentPage = 1; fetchList(1); });
    $('#prevPageBtn').on('click', function() { if (paginationInfo.currentPage > 1) fetchList(paginationInfo.currentPage - 1); });
    $('#nextPageBtn').on('click', function() { if (paginationInfo.currentPage < paginationInfo.totalPages) fetchList(paginationInfo.currentPage + 1); });
    $('#lastPageBtn').on('click', function() { fetchList(paginationInfo.totalPages); });
});
