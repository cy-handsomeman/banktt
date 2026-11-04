// ---------- 全局变量 ----------
let currentUserList = [];       // 存储当前显示的用户列表
let paginationInfo = {          // 分页信息
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};

// ---------- API 基础配置 ----------
const API_BASE_URL = '/api/sys_user/';   // 正确的API地址，支持 GET, POST, PUT, DELETE

// ---------- 工具函数：渲染表格 ----------
function renderUserTable(users) {
    const tbody = $('#userTableBody');
    if (!users || users.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="9">暂无用户数据，请新增或检查网络</td></tr>');
        return;
    }
    let htmlStr = '';
    users.forEach(user => {
        const pidDisplay = (user.pid !== null && user.pid !== undefined && user.pid !== '') ? user.pid : '—';
        const createTimeShow = user.create_time || user.created_at || '—';
        const updateTimeShow = user.update_time || user.updated_at || '—';
        htmlStr += `
            <tr data-id="${user.user_id}">
                <td>${user.user_id}</td>
                <td><strong>${escapeHtml(user.user_name)}</strong></td>
                <td>${pidDisplay}</td>
                <td>${escapeHtml(user.email || '—')}</td>
                <td>${escapeHtml(user.mobile || '—')}</td>
                <td>${escapeHtml(user.address || '—')}</td>
                <td>${createTimeShow}</td>
                <td>${updateTimeShow}</td>
                <td class="action-buttons">
                    <button class="edit-btn" data-id="${user.user_id}" title="编辑"><i class="fas fa-edit"></i></button>
                    <button class="role-btn" data-id="${user.user_id}" title="配置角色"><i class="fas fa-user-shield"></i></button>
                    <button class="delete-btn" data-id="${user.user_id}" title="删除"><i class="fas fa-trash-alt"></i></button>
                </td>
            </tr>
        `;
    });
    tbody.html(htmlStr);
    // 绑定编辑删除事件 (事件委托)
    $('.edit-btn').off('click').on('click', function(e) {
        const userId = parseInt($(this).data('id'));
        openEditModal(userId);
    });
    $('.role-btn').off('click').on('click', function(e) {
        const userId = parseInt($(this).data('id'));
        openRoleConfigModal(userId);
    });
    $('.delete-btn').off('click').on('click', function(e) {
        const userId = parseInt($(this).data('id'));
        confirmDeleteUser(userId);
    });
}

// 简单的防XSS
function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    }).replace(/[\uD800-\uDBFF][\uDC00-\uDFFF]/g, function(c) {
        return c;
    });
}

// ---------- API 请求封装 ----------
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
        originalUserList = [...users];
        paginationInfo.currentPage = page;
        paginationInfo.totalCount = count;
        paginationInfo.totalPages = Math.ceil(count / paginationInfo.pageSize);
        renderUserTable(currentUserList);
        updatePaginationUI(count, paginationInfo.totalPages);
        return users;
    }).catch(err => {
        console.error("获取系统用户列表失败:", err);
        currentUserList = [];
        renderUserTable(currentUserList);
        updatePaginationUI(0, 1);
        showToast(parseApiError(err, '获取系统用户列表失败'), 2500);
        return null;
    });
}

// ---------- 分页功能 ----------
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

// 新增用户 (POST)
function addUser(userData) {
    return $.ajax({
        url: API_BASE_URL,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(userData)
    }).then(response => {
        let newUser = response.data || response;
        fetchUserList();
        showToast("新增用户成功", 1500);
        return newUser;
    }).catch(err => {
        console.error("新增系统用户失败:", err);
        showToast(parseApiError(err, '新增系统用户失败'), 2500);
        return Promise.reject(err);
    });
}

// 修改用户 (PUT)
function updateUser(userId, userData) {
    return $.ajax({
        url: `${API_BASE_URL}${userId}/`,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(userData)
    }).then(response => {
        fetchUserList();
        showToast("用户信息更新成功", 1500);
    }).catch(err => {
        console.error("更新系统用户失败:", err);
        showToast(parseApiError(err, '更新系统用户失败'), 2500);
        return Promise.reject(err);
    });
}

// 删除用户 (DELETE)
function deleteUser(userId) {
    return $.ajax({
        url: `${API_BASE_URL}${userId}/`,
        method: 'DELETE'
    }).then(() => {
        fetchUserList();
        showToast("删除成功", 1500);
    }).catch(err => {
        console.error("删除系统用户失败:", err);
        showToast(parseApiError(err, '删除系统用户失败'), 2500);
    });
}

// 简易toast
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

// 模态框逻辑
let currentModalMode = 'add';
function openAddModal() {
    currentModalMode = 'add';
    $('#modalTitle').text('新增用户');
    $('#userForm')[0].reset();
    $('#editUserId').val('');
    $('#password').prop('required', false).attr('placeholder', '至少6位');
    $('#userModal').addClass('active');
}

function openEditModal(userId) {
    const user = currentUserList.find(u => u.user_id === userId);
    if (!user) {
        showToast("未找到该用户数据", 1000);
        return;
    }
    currentModalMode = 'edit';
    $('#modalTitle').text('编辑用户');
    $('#editUserId').val(user.user_id);
    $('#user_name').val(user.user_name);
    $('#pid').val(user.pid !== null && user.pid !== undefined ? user.pid : '');
    $('#email').val(user.email || '');
    $('#mobile').val(user.mobile || '');
    $('#address').val(user.address || '');
    $('#password').val('');
    $('#remarks').val(user.remarks || '');
    $('#userModal').addClass('active');
}

function closeModal() {
    $('#userModal').removeClass('active');
}

// 配置角色模态框
let roleList = [];

function fetchRoleList() {
    return $.ajax({
        url: '/api/role/',
        method: 'GET',
        timeout: 5000,
        contentType: 'application/json'
    }).then(response => {
        if (Array.isArray(response)) {
            roleList = response;
        } else if (response && response.data && Array.isArray(response.data)) {
            roleList = response.data;
        } else if (response && response.results && Array.isArray(response.results)) {
            roleList = response.results;
        } else {
            roleList = [];
        }
        return roleList;
    }).catch(err => {
        console.error("获取角色列表失败:", err);
        roleList = [];
        showToast(parseApiError(err, '获取角色列表失败'), 2500);
        return roleList;
    });
}

function renderRoleOptions(userId = null) {
    const container = $('#roleOptionsContainer');
    if (!roleList || roleList.length === 0) {
        container.html('<div style="text-align: center; color: #9ca3af; padding: 20px;">暂无角色数据</div>');
        return;
    }
    
    if (userId) {
        $.ajax({
            url: `/api/sys_user_role/user/${userId}/`,
            method: 'GET'
        }).then(response => {
            const userRoles = response.roles || [];
            const userRoleIds = userRoles.map(r => r.role_id.toString());
            
            let htmlStr = '';
            roleList.forEach(role => {
                const roleId = (role.role_id || role.id || role.id_field).toString();
                const roleName = role.role_name || role.name || '未知角色';
                const isChecked = userRoleIds.includes(roleId) ? 'checked' : '';
                htmlStr += `
                    <label class="role-option">
                        <input type="checkbox" name="role" value="${roleId}" ${isChecked}>
                        <span>${roleName}</span>
                    </label>
                `;
            });
            container.html(htmlStr);
        }).catch(err => {
            console.error("获取用户角色失败:", err);
            showToast(parseApiError(err, '获取用户角色失败'), 2500);
            container.html('<div style="text-align: center; color: #e03a3a; padding: 20px;">加载失败，请稍后重试</div>');
        });
    } else {
        let htmlStr = '';
        roleList.forEach(role => {
            const roleId = role.role_id || role.id || role.id_field;
            const roleName = role.role_name || role.name || '未知角色';
            htmlStr += `
                <label class="role-option">
                    <input type="checkbox" name="role" value="${roleId}">
                    <span>${roleName}</span>
                </label>
            `;
        });
        container.html(htmlStr);
    }
}

function openRoleConfigModal(userId) {
    $('#roleUserId').val(userId);
    
    if (roleList.length === 0) {
        fetchRoleList().then(() => {
            renderRoleOptions(userId);
            $('#roleModal').addClass('active');
        });
    } else {
        renderRoleOptions(userId);
        $('#roleModal').addClass('active');
    }
}

function closeRoleConfigModal() {
    $('#roleModal').removeClass('active');
}

function submitRoleConfig() {
    const userId = $('#roleUserId').val();
    const selectedRoleIds = $('input[name="role"]:checked').map(function() {
        return parseInt($(this).val());
    }).get();
    
    if (!userId) {
        showToast("用户ID不能为空", 1500);
        return;
    }
    
    $.ajax({
        url: `/api/sys_user_role/user/${userId}/`,
        method: 'GET'
    }).then(response => {
        const currentRoles = response.roles || [];
        const currentRoleIds = currentRoles.map(r => r.role_id);
        
        const rolesToAdd = selectedRoleIds.filter(rId => !currentRoleIds.includes(rId));
        const rolesToRemove = currentRoleIds.filter(rId => !selectedRoleIds.includes(rId));
        
        let doneCount = 0;
        let failCount = 0;
        let firstError = null;
        let totalOperations = rolesToAdd.length + rolesToRemove.length;
        
        if (totalOperations === 0) {
            closeRoleConfigModal();
            showToast("角色配置未变化", 1500);
            return;
        }
        
        function checkComplete() {
            if (doneCount + failCount !== totalOperations) { return; }
            if (failCount === 0) {
                closeRoleConfigModal();
                showToast("角色配置成功", 1500);
            } else {
                showToast(parseApiError(firstError, `${failCount} 项角色配置失败`), 2500);
            }
            fetchUserList();
        }
        
        function onSuccess() { doneCount++; checkComplete(); }
        function onFail(err) { failCount++; if (!firstError) firstError = err; checkComplete(); }
        
        rolesToRemove.forEach(roleId => {
            $.ajax({
                url: `/api/sys_user_role/batch_remove/`,
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    user_ids: [parseInt(userId)],
                    role_id: roleId
                })
            }).then(onSuccess).catch(onFail);
        });
        
        rolesToAdd.forEach(roleId => {
            $.ajax({
                url: `/api/sys_user_role/`,
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    user_id: parseInt(userId),
                    role_id: roleId
                })
            }).then(onSuccess).catch(onFail);
        });
    }).catch(err => {
        console.error("获取用户角色失败:", err);
        showToast("配置角色失败", 2000);
    });
}

// 保存（新增或更新）
function onSaveUser() {
    const userName = $('#user_name').val().trim();
    if (!userName) {
        showToast("用户名不能为空", 1500);
        return;
    }
    const passwordVal = $('#password').val();
    if (currentModalMode === 'add' && !passwordVal) {
        showToast("新增用户必须填写密码", 1500);
        return;
    }
    const pidRaw = $('#pid').val();
    if (!pidRaw) {
        showToast("身份证号不能为空", 1500);
        return;
    }
    // 身份证号按字符串提交，避免 18 位数字被 JS 转成 Number 后丢失精度
    const pid = pidRaw.trim();
    const mobile = $('#mobile').val().trim();
    if (!mobile) {
        showToast("手机号不能为空", 1500);
        return;
    }
    const payload = {
        user_name: userName,
        pid: pid,
        email: $('#email').val().trim(),
        mobile: $('#mobile').val().trim(),
        address: $('#address').val().trim(),
        password: passwordVal || undefined,
    };
    if (currentModalMode === 'add') {
        addUser(payload).then(() => {
            closeModal();
        }).catch(() => {});
    } else {
        const editId = parseInt($('#editUserId').val());
        if (!payload.password) delete payload.password;
        updateUser(editId, payload).then(() => {
            closeModal();
        }).catch(() => {});
    }
}

function confirmDeleteUser(userId) {
    const userName = currentUserList.find(u => u.user_id === userId)?.user_name || userId;
    if (confirm(`确定要删除用户 “${userName}” 吗？\n删除后不可恢复。`)) {
        deleteUser(userId);
    }
}

// 定时刷新功能
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

// 搜索功能
let originalUserList = [];

function handleSearch() {
    const keyword = $('#searchInput').val().trim().toLowerCase();
    
    if (!keyword) {
        currentUserList = [...originalUserList];
        renderUserTable(currentUserList);
        updatePaginationUI(currentUserList.length, Math.ceil(currentUserList.length / paginationInfo.pageSize));
        return;
    }
    
    const filteredUsers = originalUserList.filter(user => {
        const userIdStr = String(user.user_id).toLowerCase();
        const userName = (user.user_name || '').toLowerCase();
        return userIdStr.includes(keyword) || userName.includes(keyword);
    });
    
    currentUserList = filteredUsers;
    renderUserTable(currentUserList);
    updatePaginationUI(filteredUsers.length, 1);
    paginationInfo.currentPage = 1;
    paginationInfo.totalPages = 1;
}

// 刷新按钮点击事件
function handleRefresh() {
    const $btn = $('#refreshBtn');
    $btn.addClass('refreshing');
    paginationInfo.currentPage = 1;
    $('#searchInput').val('');
    fetchUserList(1).then(data => {
        $btn.removeClass('refreshing');
        if (data) { showToast("数据已刷新", 1500); }
    });
}

// 事件绑定 & 初始化
$(document).ready(function() {
    fetchUserList();
    startAutoRefresh();
    
    $('#searchInput').on('input', handleSearch);
    $('#refreshBtn').on('click', handleRefresh);
    
    $('#openAddModalBtn').on('click', openAddModal);
    $('#closeModalBtn, #cancelModalBtn').on('click', closeModal);
    $('#submitUserBtn').on('click', onSaveUser);
    $('#userModal').on('click', function(e) {
        if ($(e.target).hasClass('modal-overlay')) closeModal();
    });
    
    $('#closeRoleModalBtn, #cancelRoleModalBtn').on('click', closeRoleConfigModal);
    $('#submitRoleBtn').on('click', submitRoleConfig);
    $('#roleModal').on('click', function(e) {
        if ($(e.target).hasClass('modal-overlay')) closeRoleConfigModal();
    });
    
    $('#firstPageBtn').on('click', goToFirstPage);
    $('#prevPageBtn').on('click', goToPrevPage);
    $('#nextPageBtn').on('click', goToNextPage);
    $('#lastPageBtn').on('click', goToLastPage);
    
    $('#userForm').on('submit', function(e) { e.preventDefault(); return false; });
});