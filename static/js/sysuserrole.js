let currentList = [];
let paginationInfo = {
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};
const API_BASE_URL = '/api/sys_user_role/';
let originalList = [];

function renderTable(data) {
    const tbody = $('#dataTableBody');
    if (!data || data.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="4">暂无数据</td></tr>');
        return;
    }
    let html = '';
    data.forEach(item => {
        html += `<tr data-id="${item.id}">
            <td>${item.id}</td>
            <td><strong>${item.user_id}</strong></td>
            <td>${item.role_id}</td>
            <td class="action-buttons">
                <button class="delete-btn" data-id="${item.id}" title="删除"><i class="fas fa-trash"></i></button>
            </td>
        </tr>`;
    });
    tbody.html(html);
    $('.delete-btn').off('click').on('click', function() { confirmDelete(parseInt($(this).data('id'))); });
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
        originalList = [...data];
        paginationInfo.currentPage = page;
        paginationInfo.totalCount = count;
        paginationInfo.totalPages = Math.ceil(count / paginationInfo.pageSize);

        renderTable(currentList);
        updatePaginationUI(count, paginationInfo.totalPages);
        return data;
    }).catch(err => {
        console.error("获取用户角色关联失败:", err);
        currentList = [];
        renderTable([]);
        updatePaginationUI(0, 1);
        showToast(parseApiError(err, '获取用户角色关联失败'), 2500);
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
        console.error("新增用户角色关联失败:", err);
        showToast(parseApiError(err, '新增用户角色关联失败，请检查用户ID和角色ID'), 2500);
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
        console.error("删除用户角色关联失败:", err);
        showToast(parseApiError(err, '删除用户角色关联失败'), 2500);
    });
}

function batchRemoveRoles(userIds, roleId) {
    return $.ajax({
        url: `${API_BASE_URL}batch_remove/`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ user_ids: userIds, role_id: roleId })
    }).then(response => {
        fetchList();
        showToast(response.message || "批量移除成功", 1500);
    }).catch(err => {
        console.error("批量移除用户角色失败:", err);
        showToast(parseApiError(err, '批量移除用户角色失败'), 2500);
        return Promise.reject(err);
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

function openAddModal() {
    $('#modalTitle').text('新增关联');
    $('#dataForm')[0].reset();
    $('#editId').val('');
    $('#dataModal').addClass('active');
}

function openBatchRemoveModal() {
    $('#batchRemoveForm')[0].reset();
    $('#batchRemoveModal').addClass('active');
}

function closeBatchRemoveModal() {
    $('#batchRemoveModal').removeClass('active');
}

function closeModal() { $('#dataModal').removeClass('active'); }

function onSave() {
    const userId = parseInt($('#user_id').val());
    const roleId = parseInt($('#role_id').val());
    if (!userId) { showToast("用户ID不能为空", 1500); return; }
    if (!roleId) { showToast("角色ID不能为空", 1500); return; }

    const payload = { user_id: userId, role_id: roleId };
    addItem(payload).then(() => closeModal()).catch(() => {});
}

function onBatchRemove() {
    const userIdsStr = $('#batchRemoveUserIds').val().trim();
    const roleId = parseInt($('#batchRemoveRoleId').val());
    if (!userIdsStr) { showToast("用户ID不能为空", 1500); return; }
    if (!roleId) { showToast("角色ID不能为空", 1500); return; }

    const userIds = userIdsStr.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
    if (userIds.length === 0) { showToast("请输入有效的用户ID", 1500); return; }

    batchRemoveRoles(userIds, roleId).then(() => closeBatchRemoveModal());
}

function confirmDelete(id) {
    if (confirm('确定要删除这条关联记录吗？')) { deleteItem(id); }
}

function handleSearch() {
    const keyword = $('#searchInput').val().trim().toLowerCase();

    if (!keyword) {
        currentList = [...originalList];
        renderTable(currentList);
        updatePaginationUI(currentList.length, Math.ceil(currentList.length / paginationInfo.pageSize));
        return;
    }

    const filteredList = originalList.filter(item => {
        const userIdStr = String(item.user_id).toLowerCase();
        const roleIdStr = String(item.role_id).toLowerCase();
        return userIdStr.includes(keyword) || roleIdStr.includes(keyword);
    });

    currentList = filteredList;
    renderTable(currentList);
    updatePaginationUI(filteredList.length, 1);
    paginationInfo.currentPage = 1;
    paginationInfo.totalPages = 1;
}

$(document).ready(function() {
    fetchList();
    $('#refreshBtn').on('click', function() { 
        paginationInfo.currentPage = 1; 
        $('#searchInput').val('');
        fetchList(1); 
        showToast("已刷新", 1500); 
    });
    $('#openAddModalBtn').on('click', openAddModal);
    $('#closeModalBtn, #cancelModalBtn').on('click', closeModal);
    $('#submitBtn').on('click', onSave);
    $('#closeBatchRemoveModalBtn, #cancelBatchRemoveBtn').on('click', closeBatchRemoveModal);
    $('#submitBatchRemoveBtn').on('click', onBatchRemove);
    $('#dataModal').on('click', function(e) { if ($(e.target).hasClass('modal-overlay')) closeModal(); });
    $('#batchRemoveModal').on('click', function(e) { if ($(e.target).hasClass('modal-overlay')) closeBatchRemoveModal(); });

    $('#firstPageBtn').on('click', goToFirstPage);
    $('#prevPageBtn').on('click', goToPrevPage);
    $('#nextPageBtn').on('click', goToNextPage);
    $('#lastPageBtn').on('click', goToLastPage);

    $('#searchInput').on('input', handleSearch);

    setInterval(function() { fetchList(paginationInfo.currentPage); }, 30000);
});