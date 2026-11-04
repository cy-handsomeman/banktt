let currentList = [];
let paginationInfo = {
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};
const API_BASE_URL = '/api/card/';

function renderTable(data) {
    const tbody = $('#dataTableBody');
    if (!data || data.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="8">暂无银行卡数据</td></tr>');
        return;
    }
    let html = '';
    data.forEach(item => {
        const openDate = item.open_date ? item.open_date.replace('T', ' ').slice(0, 19) : '—';
        const openMoney = item.open_money !== null ? '¥' + parseFloat(item.open_money).toFixed(2) : '—';
        const balance = item.balance !== null ? '¥' + parseFloat(item.balance).toFixed(2) : '—';
        const status = item.card_status || '正常';
        const statusColor = status === '正常' ? '#047857' : (status === '挂失' ? '#b45309' : '#6b7280');
        let statusActions = '';
        if (status === '正常') {
            statusActions += `<button class="status-btn" data-id="${escapeHtml(item.card_id)}" data-action="report-loss" title="挂失" style="padding:4px 8px;margin-right:4px;border:1px solid #f59e0b;border-radius:6px;background:#fffbeb;color:#b45309;cursor:pointer;font-size:0.78rem;">挂失</button>`;
        }
        if (status === '挂失') {
            statusActions += `<button class="status-btn" data-id="${escapeHtml(item.card_id)}" data-action="unlock" title="解挂" style="padding:4px 8px;margin-right:4px;border:1px solid #10b981;border-radius:6px;background:#ecfdf5;color:#047857;cursor:pointer;font-size:0.78rem;">解挂</button>`;
        }
        if (status !== '销户') {
            statusActions += `<button class="status-btn" data-id="${escapeHtml(item.card_id)}" data-action="close" title="销卡" style="padding:4px 8px;margin-right:4px;border:1px solid #dc2626;border-radius:6px;background:#fef2f2;color:#dc2626;cursor:pointer;font-size:0.78rem;">销卡</button>`;
        }
        html += `<tr data-id="${item.card_id}">
            <td class="card-id-cell">${escapeHtml(item.card_id)}</td>
            <td><strong>${escapeHtml(item.cur_type)}</strong></td>
            <td><span style="color:${statusColor};font-weight:600;">${escapeHtml(status)}</span></td>
            <td>${openDate}</td>
            <td class="money-cell">${openMoney}</td>
            <td class="money-cell">${balance}</td>
            <td>${item.customer_id}</td>
            <td class="action-buttons">
                <button class="edit-btn" data-id="${escapeHtml(item.card_id)}"><i class="fas fa-edit"></i></button>
                <button class="delete-btn" data-id="${escapeHtml(item.card_id)}"><i class="fas fa-trash-alt"></i></button>
                ${statusActions}
            </td>
        </tr>`;
    });
    tbody.html(html);
    $('.edit-btn').off('click').on('click', function() { openEditModal($(this).data('id')); });
    $('.delete-btn').off('click').on('click', function() { confirmDelete($(this).data('id')); });
    $('.status-btn').off('click').on('click', function() {
        handleStatusAction($(this).data('id'), $(this).data('action'));
    });
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
        } else {
            data = [];
        }
        
        currentList = data;
        paginationInfo.currentPage = page;
        paginationInfo.totalCount = count;
        paginationInfo.totalPages = Math.ceil(count / paginationInfo.pageSize);
        
        renderTable(currentList);
        updatePaginationUI(count, paginationInfo.totalPages);
        return data;
    }).catch(err => {
        console.error("获取银行卡列表失败:", err);
        currentList = [];
        renderTable([]);
        updatePaginationUI(0, 1);
        showToast(parseApiError(err, '获取银行卡列表失败'), 2500);
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

function addItem(payload) {
    return $.ajax({
        url: API_BASE_URL,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(payload)
    }).then(() => {
        fetchList();
        showToast("新增成功", 1500);
    }).catch(err => {
        console.error("新增银行卡失败:", err);
        showToast(parseApiError(err, '新增银行卡失败'), 2500);
        return Promise.reject(err);
    });
}

function updateItem(cardId, payload) {
    return $.ajax({
        url: `${API_BASE_URL}${cardId}/`,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(payload)
    }).then(() => {
        fetchList();
        showToast("更新成功", 1500);
    }).catch(err => {
        console.error("更新银行卡失败:", err);
        showToast(parseApiError(err, '更新银行卡失败'), 2500);
        return Promise.reject(err);
    });
}

function deleteItem(cardId) {
    return $.ajax({
        url: `${API_BASE_URL}${cardId}/`,
        method: 'DELETE'
    }).then(() => {
        fetchList();
        showToast("删除成功", 1500);
    }).catch(err => {
        console.error("删除银行卡失败:", err);
        showToast(parseApiError(err, '删除银行卡失败'), 2500);
    });
}

function handleStatusAction(cardId, action) {
    const configs = {
        'report-loss': { tip: '确定要挂失该银行卡吗？挂失后将无法进行交易。', ok: '挂失成功' },
        'unlock': { tip: '确定要解挂该银行卡吗？', ok: '解挂成功' },
        'close': { tip: '确定要销卡吗？销卡后状态变为销户且不可恢复，且要求卡内余额为 0。', ok: '销卡成功' }
    };
    const config = configs[action];
    if (!config || !confirm(config.tip)) { return; }

    $.ajax({
        url: `${API_BASE_URL}${cardId}/${action}/`,
        method: 'POST',
        contentType: 'application/json'
    }).then(() => {
        fetchList();
        showToast(config.ok, 1500);
    }).catch(err => {
        console.error('银行卡状态变更失败:', err);
        showToast(parseApiError(err, '银行卡状态变更失败'), 2500);
    });
}

let toastTimer = null;
function showToast(msg, duration = 2000) {
    let toastEl = $('#dynamicToast');
    if (toastEl.length === 0) {
        $('body').append('<div id="dynamicToast" style="position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:#2c3e50; color:white; padding:10px 20px; border-radius:40px; z-index:1100; font-size:0.85rem; opacity:0; transition:0.2s; pointer-events:none;"></div>');
        toastEl = $('#dynamicToast');
    }
    toastEl.text(msg).css('opacity', '1');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastEl.css('opacity', '0'); }, duration);
}

let currentMode = 'add';
function openAddModal() {
    currentMode = 'add';
    $('#modalTitle').text('新增银行卡');
    $('#dataForm')[0].reset();
    $('#editCardId').val('');
    $('#dataModal').addClass('active');
}

function openEditModal(cardId) {
    const item = currentList.find(u => u.card_id === cardId);
    if (!item) { showToast("未找到数据", 1000); return; }
    currentMode = 'edit';
    $('#modalTitle').text('编辑银行卡');
    $('#editCardId').val(item.card_id);
    $('#card_id').val(item.card_id).prop('readonly', true);
    $('#cur_type').val(item.cur_type);
    if (item.open_date) {
        const dt = item.open_date.replace(' ', 'T').slice(0, 16);
        $('#open_date').val(dt);
    }
    $('#customer_id').val(item.customer_id);
    $('#open_money').val(item.open_money);
    $('#balance').val(item.balance);
    $('#password').val('').prop('placeholder', '不修改请留空');
    $('#dataModal').addClass('active');
}

function closeModal() { 
    $('#dataModal').removeClass('active');
    $('#card_id').prop('readonly', false);
    $('#password').prop('placeholder', '请输入密码');
}

function onSave() {
    const cardId = $('#card_id').val().trim();
    const curType = $('#cur_type').val();
    const openDate = $('#open_date').val();
    const customerId = parseInt($('#customer_id').val());
    const openMoney = parseFloat($('#open_money').val());
    const balance = parseFloat($('#balance').val());
    const password = $('#password').val();
    
    if (!cardId) { showToast("卡号不能为空", 1500); return; }
    if (!curType) { showToast("请选择货币类型", 1500); return; }
    if (!openDate) { showToast("请选择开户日期", 1500); return; }
    if (!customerId) { showToast("用户ID不能为空", 1500); return; }
    if (!openMoney && openMoney !== 0) { showToast("开户金额不能为空", 1500); return; }
    if (!balance && balance !== 0) { showToast("余额不能为空", 1500); return; }
    
    const payload = {
        card_id: cardId,
        cur_type: curType,
        open_date: openDate.replace('T', ' ') + ':00',
        customer_id: customerId,
        open_money: openMoney,
        balance: balance
    };
    
    if (currentMode === 'add') {
        if (!password) { showToast("密码不能为空", 1500); return; }
        payload.password = password;
        addItem(payload).then(() => closeModal()).catch(() => {});
    } else {
        if (password) {
            payload.password = password;
        }
        updateItem($('#editCardId').val(), payload).then(() => closeModal()).catch(() => {});
    }
}

function confirmDelete(cardId) {
    if (confirm('确定要删除这张银行卡吗？')) { deleteItem(cardId); }
}

$(document).ready(function() {
    fetchList();
    $('#refreshBtn').on('click', function() { paginationInfo.currentPage = 1; fetchList(1); showToast("已刷新", 1500); });
    $('#openAddModalBtn').on('click', openAddModal);
    $('#closeModalBtn, #cancelModalBtn').on('click', closeModal);
    $('#submitBtn').on('click', onSave);
    $('#dataModal').on('click', function(e) { if ($(e.target).hasClass('modal-overlay')) closeModal(); });
    
    $('#firstPageBtn').on('click', goToFirstPage);
    $('#prevPageBtn').on('click', goToPrevPage);
    $('#nextPageBtn').on('click', goToNextPage);
    $('#lastPageBtn').on('click', goToLastPage);
    
    setInterval(function() { fetchList(paginationInfo.currentPage); }, 30000);
});