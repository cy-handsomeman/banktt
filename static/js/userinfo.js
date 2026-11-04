let currentUserList = [];
let paginationInfo = {
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};

const API_BASE_URL = '/api/user/';

function renderUserTable(users) {
    const tbody = $('#userTableBody');
    if (!users || users.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="6">暂无客户数据，请新增或检查网络</td></tr>');
        return;
    }
    let htmlStr = '';
    users.forEach(user => {
        const pidDisplay = (user.pid !== null && user.pid !== undefined && user.pid !== '') ? user.pid : '—';
        htmlStr += `
            <tr data-id="${user.customer_id}">
                <td>${user.customer_id}</td>
                <td><strong>${escapeHtml(user.customer_name)}</strong></td>
                <td>${escapeHtml(pidDisplay)}</td>
                <td>${escapeHtml(user.telephone || '—')}</td>
                <td>${escapeHtml(user.address || '—')}</td>
                <td class="action-buttons">
                    <button class="edit-btn" data-id="${user.customer_id}" title="编辑"><i class="fas fa-edit"></i></button>
                    <button class="delete-btn" data-id="${user.customer_id}" title="删除"><i class="fas fa-trash-alt"></i></button>
                </td>
            </tr>
        `;
    });
    tbody.html(htmlStr);
    $('.edit-btn').off('click').on('click', function(e) {
        const userId = parseInt($(this).data('id'));
        openEditModal(userId);
    });
    $('.delete-btn').off('click').on('click', function(e) {
        const userId = parseInt($(this).data('id'));
        confirmDeleteUser(userId);
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

function fetchUserList(page = 1) {
    return $.ajax({
        url: `${API_BASE_URL}?page=${page}&page_size=${paginationInfo.pageSize}`,
        method: 'GET',
        timeout: 5000,
        contentType: 'application/json'
    }).then(response => {
        let users = [];
        let count = 0;
        
        if (Array.isArray(response)) {
            users = response;
            count = users.length;
        } else if (response && response.data && Array.isArray(response.data)) {
            users = response.data;
            count = response.count || users.length;
        } else if (response && response.results && Array.isArray(response.results)) {
            users = response.results;
            count = response.count || users.length;
        } else {
            users = [];
        }
        
        currentUserList = users;
        paginationInfo.currentPage = page;
        paginationInfo.totalCount = count;
        paginationInfo.totalPages = Math.ceil(count / paginationInfo.pageSize);
        
        renderUserTable(currentUserList);
        updatePaginationUI(count, paginationInfo.totalPages);
        return users;
    }).catch(err => {
        console.error("获取客户列表失败:", err);
        currentUserList = [];
        renderUserTable(currentUserList);
        updatePaginationUI(0, 1);
        showToast(parseApiError(err, '获取客户列表失败'), 2500);
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
            fetchUserList(i);
        });
        $container.append($btn);
    }
}

function goToFirstPage() {
    if (paginationInfo.currentPage > 1) {
        paginationInfo.currentPage = 1;
        fetchUserList(1);
    }
}

function goToPrevPage() {
    if (paginationInfo.currentPage > 1) {
        paginationInfo.currentPage--;
        fetchUserList(paginationInfo.currentPage);
    }
}

function goToNextPage() {
    if (paginationInfo.currentPage < paginationInfo.totalPages) {
        paginationInfo.currentPage++;
        fetchUserList(paginationInfo.currentPage);
    }
}

function goToLastPage() {
    if (paginationInfo.currentPage < paginationInfo.totalPages) {
        paginationInfo.currentPage = paginationInfo.totalPages;
        fetchUserList(paginationInfo.totalPages);
    }
}

function addUser(userData) {
    return $.ajax({
        url: API_BASE_URL,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(userData)
    }).then(response => {
        let newUser = response.data || response;
        fetchUserList();
        showToast("新增客户成功", 1500);
        return newUser;
    }).catch(err => {
        console.error("新增客户失败:", err);
        showToast(parseApiError(err, '新增客户失败'), 2500);
        return Promise.reject(err);
    });
}

function updateUser(userId, userData) {
    return $.ajax({
        url: `${API_BASE_URL}${userId}/`,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(userData)
    }).then(response => {
        fetchUserList();
        showToast("客户信息更新成功", 1500);
    }).catch(err => {
        console.error("更新客户失败:", err);
        showToast(parseApiError(err, '更新客户失败'), 2500);
        return Promise.reject(err);
    });
}

function deleteUser(userId) {
    return $.ajax({
        url: `${API_BASE_URL}${userId}/`,
        method: 'DELETE'
    }).then(() => {
        fetchUserList();
        showToast("删除成功", 1500);
    }).catch(err => {
        console.error("删除客户失败:", err);
        showToast(parseApiError(err, '删除客户失败'), 2500);
    });
}

let toastTimer = null;
function showToast(msg, duration = 2000) {
    let toastEl = $('#dynamicToast');
    if (toastEl.length === 0) {
        $('body').append(`<div id="dynamicToast" style="position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:#2c3e50; color:white; padding:10px 20px; border-radius:40px; z-index:1100; font-size:0.85rem; box-shadow:0 5px 12px rgba(0,0,0,0.2); opacity:0; transition:0.2s; pointer-events:none;"></div>`);
        toastEl = $('#dynamicToast');
    }
    toastEl.text(msg).css('opacity', '1');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toastEl.css('opacity', '0');
    }, duration);
}

let currentModalMode = 'add';
function openAddModal() {
    currentModalMode = 'add';
    $('#modalTitle').text('新增客户');
    $('#userForm')[0].reset();
    $('#editUserId').val('');
    $('#userModal').addClass('active');
}

function openEditModal(userId) {
    const user = currentUserList.find(u => u.customer_id === userId);
    if (!user) {
        showToast("未找到该客户数据", 1000);
        return;
    }
    currentModalMode = 'edit';
    $('#modalTitle').text('编辑客户');
    $('#editUserId').val(user.customer_id);
    $('#customer_name').val(user.customer_name);
    $('#pid').val(user.pid !== null && user.pid !== undefined ? user.pid : '');
    $('#telephone').val(user.telephone || '');
    $('#address').val(user.address || '');
    $('#userModal').addClass('active');
}

function closeModal() {
    $('#userModal').removeClass('active');
}

function onSaveUser() {
    const customerName = $('#customer_name').val().trim();
    if (!customerName) {
        showToast("开户名不能为空", 1500);
        return;
    }
    const pid = $('#pid').val().trim();
    if (!pid) {
        showToast("身份证号不能为空", 1500);
        return;
    }
    const telephone = $('#telephone').val().trim();
    if (!telephone) {
        showToast("联系电话不能为空", 1500);
        return;
    }
    const payload = {
        customer_name: customerName,
        pid: pid,
        telephone: telephone,
        address: $('#address').val().trim()
    };
    if (currentModalMode === 'add') {
        addUser(payload).then(() => {
            closeModal();
        }).catch(() => {});
    } else {
        const editId = parseInt($('#editUserId').val());
        updateUser(editId, payload).then(() => {
            closeModal();
        }).catch(() => {});
    }
}

function confirmDeleteUser(userId) {
    const userName = currentUserList.find(u => u.customer_id === userId)?.customer_name || userId;
    if (confirm(`确定要删除客户 "${userName}" 吗？\n删除后不可恢复。`)) {
        deleteUser(userId);
    }
}

let refreshInterval = null;

function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(function() {
        fetchUserList();
    }, 30000);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

function handleRefresh() {
    const $btn = $('#refreshBtn');
    $btn.addClass('refreshing');
    fetchUserList().then(data => {
        $btn.removeClass('refreshing');
        if (data) { showToast("数据已刷新", 1500); }
    });
}

$(document).ready(function() {
    fetchUserList();
    startAutoRefresh();
    $('#refreshBtn').on('click', handleRefresh);
    $('#openAddModalBtn').on('click', openAddModal);
    $('#closeModalBtn, #cancelModalBtn').on('click', closeModal);
    $('#submitUserBtn').on('click', onSaveUser);
    $('#userModal').on('click', function(e) {
        if ($(e.target).hasClass('modal-overlay')) closeModal();
    });
    $('#userForm').on('submit', function(e) { e.preventDefault(); return false; });
    
    $('#firstPageBtn').on('click', goToFirstPage);
    $('#prevPageBtn').on('click', goToPrevPage);
    $('#nextPageBtn').on('click', goToNextPage);
    $('#lastPageBtn').on('click', goToLastPage);
});