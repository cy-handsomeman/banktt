let paginationInfo = {
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};

const API_BASE_URL = '/api/trade/';
const INFLOW_TYPES = ['存款', '还款', '转账转入'];

function escapeHtml(value) {
    return String(value === null || value === undefined ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function formatMoney(value) {
    const num = parseFloat(value);
    if (Number.isNaN(num)) return '—';
    return '¥ ' + num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(value) {
    return value ? String(value).replace('T', ' ').slice(0, 19) : '—';
}

function buildQuery(page) {
    const params = {
        page: page,
        page_size: paginationInfo.pageSize
    };
    const cardId = $('#filterCardId').val().trim();
    const transType = $('#filterTransType').val();
    const startDate = $('#filterStartDate').val();
    const endDate = $('#filterEndDate').val();

    if (cardId) params.card_id = cardId;
    if (transType) params.trans_type = transType;
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    return params;
}

function fetchRecords(page = 1) {
    $.ajax({
        url: API_BASE_URL,
        method: 'GET',
        data: buildQuery(page),
        timeout: 8000
    }).then(function(response) {
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
        updatePaginationUI(count, paginationInfo.totalPages);
    }).catch(function(err) {
        console.error('获取交易流水失败', err);
        const message = window.parseApiError ? parseApiError(err, '获取交易流水失败') : '获取交易流水失败';
        $('#recordsBody').html(`<tr class="empty-row"><td colspan="9">${escapeHtml(message)}</td></tr>`);
        updatePaginationUI(0, 1);
    });
}

function renderTable(data) {
    const tbody = $('#recordsBody');
    if (!data || data.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="9">没有符合条件的交易流水</td></tr>');
        return;
    }

    let html = '';
    data.forEach(function(item) {
        const inflow = INFLOW_TYPES.indexOf(item.trans_type) !== -1;
        const sign = inflow ? '+' : '-';
        const amount = item.trans_money !== null ? sign + ' ' + formatMoney(item.trans_money) : '—';
        const pillClass = inflow ? '' : 'pending';

        html += `
            <tr>
                <td>${escapeHtml(item.tid)}</td>
                <td><span class="pill ${pillClass}">${escapeHtml(item.trans_type)}</span></td>
                <td>${escapeHtml(item.card_id)}</td>
                <td>${escapeHtml(item.to_card_id || '—')}</td>
                <td>${escapeHtml(formatDate(item.trans_date))}</td>
                <td class="money-cell ${inflow ? 'money-in' : 'money-out'}">${amount}</td>
                <td class="money-cell">${formatMoney(item.balance_after)}</td>
                <td>${escapeHtml(item.remark || '—')}</td>
                <td class="action-buttons">
                    <button class="edit-btn detail-btn" data-id="${escapeHtml(item.tid)}" title="查看详情"><i class="fas fa-eye"></i></button>
                </td>
            </tr>
        `;
    });
    tbody.html(html);

    $('.detail-btn').off('click').on('click', function() {
        openDetail($(this).data('id'));
    });
}

function updatePaginationUI(totalCount, totalPages) {
    const $wrapper = $('#paginationWrapper');
    $('#totalCount').text(totalCount);
    $('#currentPage').text(paginationInfo.currentPage);
    $('#totalPages').text(totalPages);

    if (totalCount <= paginationInfo.pageSize) {
        $wrapper.hide();
        return;
    }
    $wrapper.show();

    $('#firstPageBtn').prop('disabled', paginationInfo.currentPage === 1);
    $('#prevPageBtn').prop('disabled', paginationInfo.currentPage === 1);
    $('#nextPageBtn').prop('disabled', paginationInfo.currentPage >= totalPages);
    $('#lastPageBtn').prop('disabled', paginationInfo.currentPage >= totalPages);

    renderPageNumbers(totalPages);
}

function renderPageNumbers(totalPages) {
    const $container = $('#pageNumbers');
    $container.empty();

    const maxVisible = 5;
    let start = Math.max(1, paginationInfo.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    if (end - start + 1 < maxVisible) {
        start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
        const active = i === paginationInfo.currentPage;
        const $btn = $(`<button class="pagination-btn" style="width:32px;${active ? 'background:#2c6d9d;color:#fff;border-color:#2c6d9d;' : ''}">${i}</button>`);
        $btn.on('click', function() {
            fetchRecords(i);
        });
        $container.append($btn);
    }
}

function goToFirstPage() {
    if (paginationInfo.currentPage > 1) fetchRecords(1);
}

function goToPrevPage() {
    if (paginationInfo.currentPage > 1) fetchRecords(paginationInfo.currentPage - 1);
}

function goToNextPage() {
    if (paginationInfo.currentPage < paginationInfo.totalPages) fetchRecords(paginationInfo.currentPage + 1);
}

function goToLastPage() {
    if (paginationInfo.currentPage < paginationInfo.totalPages) fetchRecords(paginationInfo.totalPages);
}

function openDetail(tid) {
    $.ajax({
        url: `${API_BASE_URL}${tid}/`,
        method: 'GET'
    }).then(function(item) {
        const inflow = INFLOW_TYPES.indexOf(item.trans_type) !== -1;
        const rows = [
            ['交易 ID', item.tid],
            ['交易类型', item.trans_type],
            ['银行卡号', item.card_id],
            ['对方卡号', item.to_card_id || '—'],
            ['交易日期', formatDate(item.trans_date)],
            ['交易金额', (inflow ? '+' : '-') + ' ' + formatMoney(item.trans_money)],
            ['交易后余额', formatMoney(item.balance_after)],
            ['关联流水', item.pair_tid || '—'],
            ['是否冲正', item.is_reversed ? '已冲正' : '否'],
            ['备注', item.remark || '—']
        ];
        let html = '';
        rows.forEach(function(row) {
            html += `<div class="label">${escapeHtml(row[0])}</div><div class="value">${escapeHtml(row[1])}</div>`;
        });
        $('#detailContent').html(html);
        $('#detailModal').addClass('active');
    }).catch(function(err) {
        const message = window.parseApiError ? parseApiError(err, '获取交易详情失败') : '获取交易详情失败';
        showToast(message, 2500);
    });
}

function closeDetail() {
    $('#detailModal').removeClass('active');
}

let toastTimer = null;
function showToast(msg, duration) {
    let $toast = $('#recordsToast');
    if (!$toast.length) {
        $toast = $('<div id="recordsToast" class="toast"></div>');
        $('body').append($toast);
    }
    $toast.text(msg).addClass('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function() { $toast.removeClass('show'); }, duration || 2000);
}

function resetFilters() {
    $('#filterCardId').val('');
    $('#filterTransType').val('');
    $('#filterStartDate').val('');
    $('#filterEndDate').val('');
    fetchRecords(1);
}

$(document).ready(function() {
    fetchRecords(1);

    $('#searchBtn').on('click', function() { fetchRecords(1); });
    $('#resetBtn').on('click', resetFilters);
    $('#refreshBtn').on('click', function() { fetchRecords(paginationInfo.currentPage); });

    $('#filterCardId, #filterTransType, #filterStartDate, #filterEndDate').on('keydown', function(e) {
        if (e.key === 'Enter') fetchRecords(1);
    });

    $('#closeDetailBtn, #closeDetailBtn2').on('click', closeDetail);
    $('#detailModal').on('click', function(e) {
        if ($(e.target).hasClass('modal-overlay')) closeDetail();
    });

    $('#firstPageBtn').on('click', goToFirstPage);
    $('#prevPageBtn').on('click', goToPrevPage);
    $('#nextPageBtn').on('click', goToNextPage);
    $('#lastPageBtn').on('click', goToLastPage);
});
