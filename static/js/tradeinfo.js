let currentList = [];
let isApiAvailable = true;
let paginationInfo = {
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};

const API_BASE_URL = '/api/trade/';

const generateMockData = () => { return []; };

function renderTable(data) {
    const tbody = $('#dataTableBody');
    if (!data || data.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="7">暂无交易数据，请新增或检查网络</td></tr>');
        return;
    }
    let html = '';
    data.forEach(item => {
        const transMoney = item.trans_money !== null ? '¥' + parseFloat(item.trans_money).toFixed(2) : '—';
        const transDate = item.trans_date ? item.trans_date.replace('T', ' ').slice(0, 19) : '—';
        html += `<tr data-id="${item.tid}">
            <td>${item.tid}</td>
            <td><strong>${escapeHtml(item.trans_type)}</strong></td>
            <td>${escapeHtml(item.card_id)}</td>
            <td>${transDate}</td>
            <td class="money-cell">${transMoney}</td>
            <td>${escapeHtml(item.remark || '—')}</td>
            <td class="action-buttons">
                <button class="edit-btn" data-id="${item.tid}" title="编辑"><i class="fas fa-edit"></i></button>
                <button class="delete-btn" data-id="${item.tid}" title="删除"><i class="fas fa-trash-alt"></i></button>
            </td>
        </tr>`;
    });
    tbody.html(html);
    $('.edit-btn').off('click').on('click', function() { openEditModal(parseInt($(this).data('id'))); });
    $('.delete-btn').off('click').on('click', function() { confirmDelete(parseInt($(this).data('id'))); });
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
        console.error("获取数据失败:", error);
        isApiAvailable = false;
        currentList = generateMockData();
        renderTable(currentList);
        updatePaginationUI(currentList.length, 1);
        showToast("⚠️ 接口调用失败", 3000);
        return currentList;
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
        console.error("新增失败:", err);
        isApiAvailable = false;
        const newId = generateNewId();
        currentList.push({ tid: newId, ...itemData });
        renderTable(currentList);
        showToast("⚠️ 已本地新增", 2000);
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
        console.error("更新失败:", err);
        isApiAvailable = false;
        const idx = currentList.findIndex(u => u.tid === id);
        if (idx !== -1) { currentList[idx] = { ...currentList[idx], ...itemData, tid: id }; renderTable(currentList); }
        showToast("⚠️ 已本地更新", 2000);
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
        console.error("删除失败:", err);
        const idx = currentList.findIndex(u => u.tid === id);
        if (idx !== -1) { currentList.splice(idx, 1); renderTable(currentList); }
        showToast("⚠️ 已本地删除", 2000);
    });
}

function generateNewId() {
    if (!currentList.length) return 1;
    return Math.max(...currentList.map(u => u.tid)) + 1;
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
    $('#dataModal').addClass('active');
}

function openEditModal(id) {
    const item = currentList.find(u => u.tid === id);
    if (!item) { showToast("未找到数据", 1000); return; }
    currentMode = 'edit';
    $('#modalTitle').text('编辑交易');
    $('#editId').val(item.tid);
    $('#trans_type').val(item.trans_type);
    $('#card_id').val(item.card_id);
    if (item.trans_date) {
        const dt = item.trans_date.replace(' ', 'T').slice(0, 16);
        $('#trans_date').val(dt);
    }
    $('#trans_money').val(item.trans_money);
    $('#remark').val(item.remark || '');
    $('#dataModal').addClass('active');
}

function closeModal() { $('#dataModal').removeClass('active'); }

function onSave() {
    const transType = $('#trans_type').val();
    const cardId = $('#card_id').val().trim();
    const transDate = $('#trans_date').val();
    const transMoney = $('#trans_money').val();
    
    if (!transType) { showToast("请选择交易类型", 1500); return; }
    if (!cardId) { showToast("银行卡号不能为空", 1500); return; }
    if (!transDate) { showToast("请选择交易日期", 1500); return; }
    if (!transMoney) { showToast("交易金额不能为空", 1500); return; }
    
    const payload = {
        trans_type: transType,
        card_id: cardId,
        trans_date: transDate.replace('T', ' ') + ':00',
        trans_money: parseFloat(transMoney),
        remark: $('#remark').val().trim()
    };
    
    if (currentMode === 'add') {
        addItem(payload).then(() => closeModal());
    } else {
        updateItem(parseInt($('#editId').val()), payload).then(() => closeModal());
    }
}

function confirmDelete(id) {
    if (confirm('确定要删除这条交易记录吗？')) { deleteItem(id); }
}

let refreshInterval = null;
function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(fetchList, 30000);
}

function handleRefresh() {
    const $btn = $('#refreshBtn');
    $btn.addClass('refreshing');
    fetchList().then(() => { $btn.removeClass('refreshing'); showToast("数据已刷新", 1500); });
}

$(document).ready(function() {
    fetchList();
    startAutoRefresh();
    $('#refreshBtn').on('click', handleRefresh);
    $('#openAddModalBtn').on('click', openAddModal);
    $('#closeModalBtn, #cancelModalBtn').on('click', closeModal);
    $('#submitBtn').on('click', onSave);
    $('#dataModal').on('click', function(e) { if ($(e.target).hasClass('modal-overlay')) closeModal(); });
    $('#dataForm').on('submit', function(e) { e.preventDefault(); return false; });
    
    $('#firstPageBtn').on('click', goToFirstPage);
    $('#prevPageBtn').on('click', goToPrevPage);
    $('#nextPageBtn').on('click', goToNextPage);
    $('#lastPageBtn').on('click', goToLastPage);
});