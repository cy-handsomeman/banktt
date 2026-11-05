let currentList = [];
let canWriteBusiness = typeof window.__serverCanWrite === 'boolean' ? window.__serverCanWrite : true;
let paginationInfo = {
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};

const API_BASE_URL = '/api/trade/';
const INFLOW_TYPES = ['存款', '还款', '转账转入'];

function renderTable(data) {
    const tbody = $('#dataTableBody');
    if (!data || data.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="8">暂无交易数据</td></tr>');
        return;
    }
    let html = '';
    data.forEach(item => {
        const inflow = INFLOW_TYPES.indexOf(item.trans_type) !== -1;
        const sign = inflow ? '+' : '-';
        const transMoney = item.trans_money !== null
            ? sign + ' ¥' + parseFloat(item.trans_money).toFixed(2) : '—';
        const transDate = item.trans_date ? item.trans_date.replace('T', ' ').slice(0, 19) : '—';
        const toCardId = item.to_card_id ? escapeHtml(item.to_card_id) : '—';
        const balanceAfter = item.balance_after !== null && item.balance_after !== undefined
            ? '¥' + parseFloat(item.balance_after).toFixed(2) : '—';
        const pillClass = inflow ? '' : 'pending';

        html += `<tr data-id="${item.tid}">
            <td>${item.tid}</td>
            <td><span class="pill ${pillClass}">${escapeHtml(item.trans_type)}</span></td>
            <td>${escapeHtml(item.card_id)}</td>
            <td>${toCardId}</td>
            <td>${transDate}</td>
            <td class="money-cell ${inflow ? 'money-in' : 'money-out'}">${transMoney}</td>
            <td class="money-cell">${balanceAfter}</td>
            <td>${escapeHtml(item.remark || '—')}</td>
        </tr>`;
    });
    tbody.html(html);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>]/g, m => m === '&' ? '&amp;' : m === '<' ? '&lt;' : m === '>' ? '&gt;' : m);
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

        currentList = data;
        paginationInfo.currentPage = page;
        paginationInfo.totalCount = count;
        paginationInfo.totalPages = Math.ceil(count / paginationInfo.pageSize);

        renderTable(currentList);
        updatePaginationUI(count, paginationInfo.totalPages);
        return data;
    }).catch(error => {
        console.error("获取交易列表失败:", error);
        currentList = [];
        renderTable(currentList);
        updatePaginationUI(0, 1);
        showToast(parseApiError(error, '获取交易列表失败'), 2500);
        return null;
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
        $btn.on('click', () => {
            paginationInfo.currentPage = i;
            fetchList(i);
        });
        $container.append($btn);
    }
}

function goToFirstPage() {
    if (paginationInfo.currentPage > 1) { fetchList(1); }
}

function goToPrevPage() {
    if (paginationInfo.currentPage > 1) { fetchList(paginationInfo.currentPage - 1); }
}

function goToNextPage() {
    if (paginationInfo.currentPage < paginationInfo.totalPages) { fetchList(paginationInfo.currentPage + 1); }
}

function goToLastPage() {
    if (paginationInfo.currentPage < paginationInfo.totalPages) { fetchList(paginationInfo.totalPages); }
}

function addItem(itemData) {
    return $.ajax({
        url: API_BASE_URL,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(itemData)
    }).then(() => {
        fetchList(1);
        showToast("交易办理成功", 1500);
    }).catch(err => {
        console.error("新增交易失败:", err);
        showToast(parseApiError(err, '新增交易失败'), 2500);
        return Promise.reject(err);
    });
}

let toastTimer = null;
function showToast(msg, duration = 2000) {
    let toastEl = $('#dynamicToast');
    if (toastEl.length === 0) {
        $('body').append('<div id="dynamicToast" style="position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:#243e55; color:white; padding:10px 20px; border-radius:6px; z-index:1100; font-size:0.85rem; opacity:0; transition:0.2s; pointer-events:none;"></div>');
        toastEl = $('#dynamicToast');
    }
    toastEl.text(msg).css('opacity', '1');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastEl.css('opacity', '0'); }, duration);
}

function openAddModal() {
    $('#dataForm')[0].reset();
    $('#modalTitle').text('新增交易');
    toggleToCardField();
    $('#dataModal').addClass('active');
}

function closeModal() { $('#dataModal').removeClass('active'); }

function onSave() {
    const transType = $('#trans_type').val();
    const cardId = $('#card_id').val().trim();
    const toCardId = $('#to_card_id').val().trim();
    const transMoney = $('#trans_money').val();

    if (!transType) { showToast("请选择交易类型", 1500); return; }
    if (!cardId) { showToast("银行卡号不能为空", 1500); return; }
    if (transType === '转账' && !toCardId) { showToast("转账必须填写收款卡号", 1500); return; }
    if (transType === '转账' && toCardId === cardId) { showToast("收款卡号不能与付款卡号相同", 1500); return; }
    if (!transMoney) { showToast("交易金额不能为空", 1500); return; }

    const payload = {
        trans_type: transType,
        card_id: cardId,
        trans_money: parseFloat(transMoney),
        remark: $('#remark').val().trim()
    };
    if (transType === '转账') {
        payload.to_card_id = toCardId;
    }

    addItem(payload).then(() => closeModal()).catch(() => {});
}

// 转账时才显示收款卡号
function toggleToCardField() {
    const isTransfer = $('#trans_type').val() === '转账';
    $('#toCardGroup').toggle(isTransfer);
    if (!isTransfer) { $('#to_card_id').val(''); }
}

let refreshInterval = null;
function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(() => fetchList(paginationInfo.currentPage), 30000);
}

function handleRefresh() {
    const $btn = $('#refreshBtn');
    $btn.addClass('refreshing');
    fetchList(paginationInfo.currentPage).then(data => {
        $btn.removeClass('refreshing');
        if (data) { showToast("数据已刷新", 1500); }
    });
}

$(document).ready(function() {
    if (typeof window.__serverCanWrite === 'boolean') {
        // 服务端已注入角色，直接按结果控制只读状态，避免异步请求失败导致误判
        if (!canWriteBusiness) {
            $('#openAddModalBtn').addClass('hidden');
            $('#readonlyBadge').removeClass('hidden');
        }
    } else if (window.getUserRoles) {
        getUserRoles().then(roles => {
            canWriteBusiness = window.isWriteRole(roles);
            if (!canWriteBusiness) {
                $('#openAddModalBtn').addClass('hidden');
                $('#readonlyBadge').removeClass('hidden');
            }
        });
    }

    fetchList();
    startAutoRefresh();
    $('#refreshBtn').on('click', handleRefresh);
    $('#openAddModalBtn').on('click', openAddModal);
    $('#closeModalBtn, #cancelModalBtn').on('click', closeModal);
    $('#submitBtn').on('click', onSave);
    $('#trans_type').on('change', toggleToCardField);
    $('#dataModal').on('click', function(e) { if ($(e.target).hasClass('modal-overlay')) closeModal(); });
    $('#dataForm').on('submit', function(e) { e.preventDefault(); return false; });

    $('#firstPageBtn').on('click', goToFirstPage);
    $('#prevPageBtn').on('click', goToPrevPage);
    $('#nextPageBtn').on('click', goToNextPage);
    $('#lastPageBtn').on('click', goToLastPage);
});
