let currentList = [];
let paginationInfo = {
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};

const API_BASE_URL = '/api/trade/';

function renderTable(data) {
    const tbody = $('#dataTableBody');
    if (!data || data.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="10">暂无交易数据</td></tr>');
        return;
    }
    let html = '';
    data.forEach(item => {
        const transMoney = item.trans_money !== null ? '¥' + parseFloat(item.trans_money).toFixed(2) : '—';
        const transDate = item.trans_date ? item.trans_date.replace('T', ' ').slice(0, 19) : '—';
        const toCardId = item.to_card_id ? escapeHtml(item.to_card_id) : '—';
        const balanceAfter = item.balance_after !== null && item.balance_after !== undefined
            ? '¥' + parseFloat(item.balance_after).toFixed(2) : '—';
        // 转账的两条流水是成对的，不允许单独修改或删除
        const isTransferLeg = item.trans_type === '转账转出' || item.trans_type === '转账转入';
        const isReversal = item.trans_type === '冲正';
        const statusHtml = item.is_reversed
            ? '<span style="color:#b45309;font-weight:600;">已冲正</span>'
            : (isReversal ? '<span style="color:#6b7280;">冲正流水</span>' : '正常');

        let actionHtml = '<span class="transfer-locked" title="该流水不支持修改/删除">—</span>';
        if (!item.is_reversed && !isReversal) {
            const editBtn = isTransferLeg ? '' :
                `<button class="edit-btn" data-id="${item.tid}" title="编辑"><i class="fas fa-edit"></i></button>
                 <button class="delete-btn" data-id="${item.tid}" title="删除"><i class="fas fa-trash-alt"></i></button>`;
            actionHtml = editBtn +
                `<button class="reverse-btn" data-id="${item.tid}" title="冲正"><i class="fas fa-undo-alt"></i></button>`;
        }

        html += `<tr data-id="${item.tid}">
            <td>${item.tid}</td>
            <td><strong>${escapeHtml(item.trans_type)}</strong></td>
            <td>${escapeHtml(item.card_id)}</td>
            <td>${toCardId}</td>
            <td>${transDate}</td>
            <td class="money-cell">${transMoney}</td>
            <td class="money-cell">${balanceAfter}</td>
            <td>${statusHtml}</td>
            <td>${escapeHtml(item.remark || '—')}</td>
            <td class="action-buttons">${actionHtml}</td>
        </tr>`;
    });
    tbody.html(html);
    $('.edit-btn').off('click').on('click', function() { openEditModal(parseInt($(this).data('id'))); });
    $('.delete-btn').off('click').on('click', function() { confirmDelete(parseInt($(this).data('id'))); });
    $('.reverse-btn').off('click').on('click', function() { confirmReverse(parseInt($(this).data('id'))); });
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
    const $firstBtn = $('#firstPageBtn');
    const $prevBtn = $('#prevPageBtn');
    const $nextBtn = $('#nextPageBtn');
    const $lastBtn = $('#lastPageBtn');
    
    $('#totalCount').text(totalCount);
    $('#currentPage').text(paginationInfo.currentPage);
    $('#totalPages').text(totalPages);
    
    if (totalCount <= paginationInfo.pageSize) {
        $wrapper.hide();
        return;
    }
    
    $wrapper.show();
    
    $firstBtn.prop('disabled', paginationInfo.currentPage === 1);
    $prevBtn.prop('disabled', paginationInfo.currentPage === 1);
    $nextBtn.prop('disabled', paginationInfo.currentPage >= totalPages);
    $lastBtn.prop('disabled', paginationInfo.currentPage >= totalPages);
    
    $firstBtn.css('opacity', paginationInfo.currentPage === 1 ? '0.5' : '1');
    $prevBtn.css('opacity', paginationInfo.currentPage === 1 ? '0.5' : '1');
    $nextBtn.css('opacity', paginationInfo.currentPage >= totalPages ? '0.5' : '1');
    $lastBtn.css('opacity', paginationInfo.currentPage >= totalPages ? '0.5' : '1');
    
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
        const $btn = $(`<button style="width: 32px; height: 32px; border: 1px solid #e5e7eb; border-radius: 6px; background: ${i === paginationInfo.currentPage ? '#2c6e9e' : 'white'}; color: ${i === paginationInfo.currentPage ? 'white' : '#374151'}; cursor: pointer; font-size: 0.85rem; transition: 0.15s;">${i}</button>`);
        if (i === paginationInfo.currentPage) {
            $btn.css('font-weight', '600');
        }
        $btn.on('click', () => {
            paginationInfo.currentPage = i;
            fetchList(i);
        });
        $container.append($btn);
    }
}

function goToFirstPage() {
    if (paginationInfo.currentPage > 1) {
        paginationInfo.currentPage = 1;
        fetchList(1);
    }
}

function goToPrevPage() {
    if (paginationInfo.currentPage > 1) {
        paginationInfo.currentPage--;
        fetchList(paginationInfo.currentPage);
    }
}

function goToNextPage() {
    if (paginationInfo.currentPage < paginationInfo.totalPages) {
        paginationInfo.currentPage++;
        fetchList(paginationInfo.currentPage);
    }
}

function goToLastPage() {
    if (paginationInfo.currentPage < paginationInfo.totalPages) {
        paginationInfo.currentPage = paginationInfo.totalPages;
        fetchList(paginationInfo.totalPages);
    }
}

function addItem(itemData) {
    return $.ajax({
        url: API_BASE_URL,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(itemData)
    }).then(response => {
        fetchList();
        showToast("新增成功", 1500);
    }).catch(err => {
        console.error("新增交易失败:", err);
        showToast(parseApiError(err, '新增交易失败'), 2500);
        return Promise.reject(err);
    });
}

function updateItem(id, itemData) {
    return $.ajax({
        url: `${API_BASE_URL}${id}/`,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(itemData)
    }).then(response => {
        fetchList();
        showToast("更新成功", 1500);
    }).catch(err => {
        console.error("更新交易失败:", err);
        showToast(parseApiError(err, '更新交易失败'), 2500);
        return Promise.reject(err);
    });
}

function deleteItem(id) {
    return $.ajax({
        url: `${API_BASE_URL}${id}/`,
        method: 'DELETE'
    }).then(() => {
        fetchList();
        showToast("删除成功", 1500);
    }).catch(err => {
        console.error("删除交易失败:", err);
        showToast(parseApiError(err, '删除交易失败'), 2500);
    });
}

let toastTimer = null;
function showToast(msg, duration = 2000) {
    let toastEl = $('#dynamicToast');
    if (toastEl.length === 0) {
        $('body').append('<div id="dynamicToast" style="position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:#2c3e50; color:white; padding:10px 20px; border-radius:40px; z-index:1100; font-size:0.85rem; box-shadow:0 5px 12px rgba(0,0,0,0.2); opacity:0; transition:0.2s; pointer-events:none;"></div>');
        toastEl = $('#dynamicToast');
    }
    toastEl.text(msg).css('opacity', '1');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastEl.css('opacity', '0'); }, duration);
}

let currentMode = 'add';
function openAddModal() {
    currentMode = 'add';
    $('#modalTitle').text('新增交易');
    $('#dataForm')[0].reset();
    $('#editId').val('');
    toggleToCardField();
    $('#dataModal').addClass('active');
}

function openEditModal(id) {
    const item = currentList.find(u => u.tid === id);
    if (!item) { showToast("未找到数据", 1000); return; }
    currentMode = 'edit';
    $('#modalTitle').text('编辑交易');
    $('#editId').val(item.tid);
    $('#trans_type').val(item.trans_type === '转账转出' ? '转账' : item.trans_type);
    $('#card_id').val(item.card_id);
    $('#to_card_id').val(item.to_card_id || '');
    $('#trans_date_display').val(
        item.trans_date ? item.trans_date.replace('T', ' ').slice(0, 19) + '（不可修改）' : '保存时由系统自动记录'
    );
    $('#trans_money').val(item.trans_money);
    $('#remark').val(item.remark || '');
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
    
    if (currentMode === 'add') {
        addItem(payload).then(() => closeModal()).catch(() => {});
    } else {
        updateItem(parseInt($('#editId').val()), payload).then(() => closeModal()).catch(() => {});
    }
}

// 转账时才显示收款卡号
function toggleToCardField() {
    const isTransfer = $('#trans_type').val() === '转账';
    $('#toCardGroup').toggle(isTransfer);
    if (!isTransfer) { $('#to_card_id').val(''); }
}

function confirmDelete(id) {
    if (confirm('确定要删除这条交易记录吗？')) { deleteItem(id); }
}

function reverseItem(id) {
    return $.ajax({
        url: `${API_BASE_URL}${id}/reverse/`,
        method: 'POST',
        contentType: 'application/json'
    }).then(() => {
        fetchList();
        showToast("冲正成功", 1500);
    }).catch(err => {
        console.error("冲正失败:", err);
        showToast(parseApiError(err, '冲正失败'), 2500);
    });
}

function confirmReverse(id) {
    const item = currentList.find(u => u.tid === id);
    const type = item ? item.trans_type : '';
    const isTransfer = type === '转账转出' || type === '转账转入';
    const tip = isTransfer
        ? '冲正该笔转账会同时冲销收付款双方的流水，确定继续吗？'
        : '确定要对这笔交易发起冲正吗？冲正后将生成反向流水且原交易不可再修改。';
    if (confirm(tip)) { reverseItem(id); }
}

let refreshInterval = null;
function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(fetchList, 30000);
}

function handleRefresh() {
    const $btn = $('#refreshBtn');
    $btn.addClass('refreshing');
    fetchList().then(data => {
        $btn.removeClass('refreshing');
        if (data) { showToast("数据已刷新", 1500); }
    });
}

$(document).ready(function() {
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