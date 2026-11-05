let roleList = [];
let menuList = [];
let userList = [];
let memberList = [];
let selectedRoleId = null;

const ROLE_API = '/api/role/';
const MENU_API = '/api/menu/';
const ROLE_MENU_API = '/api/role_menu/';
const USER_API = '/api/sys_user/';
const USER_ROLE_API = '/api/sys_user_role/';

function escapeHtml(value) {
    return String(value === null || value === undefined ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function normalizeList(resp) {
    if (Array.isArray(resp)) return resp;
    if (resp && Array.isArray(resp.results)) return resp.results;
    if (resp && Array.isArray(resp.data)) return resp.data;
    return [];
}

/* ---------------- 角色列表 ---------------- */
function fetchRoles(preferredId) {
    return $.ajax({
        url: `${ROLE_API}?page_size=100`,
        method: 'GET'
    }).then(function(resp) {
        roleList = normalizeList(resp);
        renderRoles();
        const targetId = preferredId || selectedRoleId || (roleList[0] && roleList[0].role_id);
        if (targetId) {
            selectRole(targetId);
        }
        return roleList;
    }).catch(function(err) {
        console.error('获取角色列表失败', err);
        showToast(parseApiError(err, '获取角色列表失败'), 2500);
        $('#roleTableBody').html('<tr class="empty-row"><td colspan="4">角色加载失败</td></tr>');
        return [];
    });
}

function renderRoles() {
    const tbody = $('#roleTableBody');
    if (!roleList.length) {
        tbody.html('<tr class="empty-row"><td colspan="4">暂无角色</td></tr>');
        return;
    }
    let html = '';
    roleList.forEach(function(role) {
        const selected = role.role_id === selectedRoleId ? 'selected' : '';
        html += `<tr class="role-row ${selected}" data-id="${role.role_id}">
            <td>${role.role_id}</td>
            <td><strong>${escapeHtml(role.role_name)}</strong></td>
            <td>${escapeHtml(role.description || '—')}</td>
            <td class="action-buttons">
                <button class="edit-btn" data-id="${role.role_id}" title="编辑"><i class="fas fa-edit"></i></button>
                <button class="delete-btn" data-id="${role.role_id}" title="删除"><i class="fas fa-trash-alt"></i></button>
            </td>
        </tr>`;
    });
    tbody.html(html);

    $('.role-row').off('click').on('click', function(e) {
        if ($(e.target).closest('.action-buttons').length) return;
        selectRole(parseInt($(this).data('id')));
    });
    $('.edit-btn').off('click').on('click', function(e) {
        e.stopPropagation();
        openEditModal(parseInt($(this).data('id')));
    });
    $('.delete-btn').off('click').on('click', function(e) {
        e.stopPropagation();
        confirmDeleteRole(parseInt($(this).data('id')));
    });
}

function selectRole(roleId) {
    selectedRoleId = roleId;
    const role = roleList.find(function(item) { return item.role_id === roleId; });
    const roleName = role ? role.role_name : '未选择角色';

    $('.role-row').removeClass('selected');
    $(`.role-row[data-id="${roleId}"]`).addClass('selected');
    $('#selectedRoleName').text(roleName);
    $('#memberRoleLabel').text('· ' + roleName);
    $('#saveMenuBtn').prop('disabled', false);

    loadPermissions(roleId);
    loadMembers(roleId);
}

/* ---------------- 菜单授权 ---------------- */
function loadPermissions(roleId) {
    $.when(
        $.ajax({ url: `${MENU_API}?page_size=200`, method: 'GET' }),
        $.ajax({ url: `${ROLE_MENU_API}?role_id=${roleId}&page_size=200`, method: 'GET' })
    ).then(function(menuResp, roleMenuResp) {
        menuList = normalizeList(menuResp[0]);
        const assignedIds = normalizeList(roleMenuResp[0]).map(function(item) { return item.menu_id; });
        renderMenuGroups(assignedIds);
    }).catch(function(err) {
        console.error('加载菜单权限失败', err);
        showToast(parseApiError(err, '加载菜单权限失败'), 2200);
        $('#menuGroups').html('<div class="empty-tip">菜单权限加载失败</div>');
    });
}

function renderMenuGroups(assignedIds) {
    if (!menuList.length) {
        $('#menuGroups').html('<div class="empty-tip">暂无可授权菜单</div>');
        return;
    }

    const groups = {};
    menuList.forEach(function(menu) {
        const groupName = (menu.menu_group || '').trim() || '其他';
        (groups[groupName] = groups[groupName] || []).push(menu);
    });

    let html = '';
    Object.keys(groups).forEach(function(groupName) {
        groups[groupName].sort(function(a, b) {
            return (a.sort_order || 0) - (b.sort_order || 0);
        });
        html += `<div class="menu-section">
            <h4 class="menu-section-title"><i class="fas fa-layer-group"></i> ${escapeHtml(groupName)}</h4>
            <div class="menu-items">`;
        groups[groupName].forEach(function(menu) {
            const checked = assignedIds.indexOf(menu.menu_id) !== -1;
            html += `<div class="menu-item ${checked ? 'selected' : ''}" data-menu-id="${menu.menu_id}">
                <input type="checkbox" id="menu_${menu.menu_id}" ${checked ? 'checked' : ''}>
                <label for="menu_${menu.menu_id}">${escapeHtml(menu.menu_name)}</label>
            </div>`;
        });
        html += '</div></div>';
    });

    $('#menuGroups').html(html);

    $('.menu-item').off('click').on('click', function(e) {
        const checkbox = $(this).find('input[type="checkbox"]');
        if (e.target !== checkbox[0]) {
            checkbox.prop('checked', !checkbox.prop('checked'));
        }
        $(this).toggleClass('selected', checkbox.prop('checked'));
    });
}

function saveMenuPermissions() {
    if (!selectedRoleId) {
        showToast('请先选择角色', 1500);
        return;
    }
    const menuIds = [];
    $('.menu-item input[type="checkbox"]:checked').each(function() {
        menuIds.push(parseInt($(this).attr('id').replace('menu_', '')));
    });

    $('#saveMenuBtn').prop('disabled', true);
    $.ajax({
        url: `${ROLE_MENU_API}batch/`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ role_id: selectedRoleId, menu_ids: menuIds })
    }).then(function() {
        showToast('菜单授权已保存', 1600);
    }).catch(function(err) {
        showToast(parseApiError(err, '保存菜单授权失败'), 2400);
    }).always(function() {
        $('#saveMenuBtn').prop('disabled', false);
    });
}

/* ---------------- 角色成员 ---------------- */
function fetchUsers() {
    return $.ajax({
        url: `${USER_API}?page_size=500`,
        method: 'GET'
    }).then(function(resp) {
        userList = normalizeList(resp);
        let html = '<option value="">请选择系统用户</option>';
        userList.forEach(function(user) {
            html += `<option value="${user.user_id}">${escapeHtml(user.user_name)}（ID ${user.user_id}）</option>`;
        });
        $('#userSelect').html(html);
        return userList;
    }).catch(function(err) {
        console.error('获取系统用户失败', err);
        return [];
    });
}

function loadMembers(roleId) {
    $.ajax({
        url: `${USER_ROLE_API}?role_id=${roleId}&page_size=200`,
        method: 'GET'
    }).then(function(resp) {
        memberList = normalizeList(resp);
        renderMembers();
    }).catch(function(err) {
        console.error('获取角色成员失败', err);
        $('#memberTableBody').html('<tr class="empty-row"><td colspan="4">成员加载失败</td></tr>');
        $('#memberCount').text('0 人');
    });
}

function userNameById(userId) {
    const user = userList.find(function(item) { return item.user_id === userId; });
    return user ? user.user_name : `用户 ${userId}`;
}

function renderMembers() {
    const tbody = $('#memberTableBody');
    const role = roleList.find(function(item) { return item.role_id === selectedRoleId; });
    const roleName = role ? role.role_name : '';

    $('#memberCount').text(memberList.length + ' 人');

    if (!memberList.length) {
        tbody.html('<tr class="empty-row"><td colspan="4">该角色暂无成员</td></tr>');
        return;
    }

    let html = '';
    memberList.forEach(function(item) {
        html += `<tr>
            <td>${item.user_id}</td>
            <td><strong>${escapeHtml(userNameById(item.user_id))}</strong></td>
            <td><span class="pill">${escapeHtml(roleName)}</span></td>
            <td class="action-buttons">
                <button class="delete-btn remove-member" data-id="${item.id}" title="移除"><i class="fas fa-user-minus"></i></button>
            </td>
        </tr>`;
    });
    tbody.html(html);

    $('.remove-member').off('click').on('click', function() {
        removeMember(parseInt($(this).data('id')));
    });
}

function addMember() {
    const userId = parseInt($('#userSelect').val());
    if (!selectedRoleId) {
        showToast('请先选择角色', 1500);
        return;
    }
    if (!userId) {
        showToast('请选择系统用户', 1500);
        return;
    }

    $('#addMemberBtn').prop('disabled', true);
    $.ajax({
        url: USER_ROLE_API,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ user_id: userId, role_id: selectedRoleId })
    }).then(function() {
        showToast('成员添加成功', 1500);
        $('#userSelect').val('');
        loadMembers(selectedRoleId);
    }).catch(function(err) {
        showToast(parseApiError(err, '添加成员失败'), 2400);
    }).always(function() {
        $('#addMemberBtn').prop('disabled', false);
    });
}

function removeMember(assignmentId) {
    if (!confirm('确定要将该用户从当前角色移除吗？')) return;

    $.ajax({
        url: `${USER_ROLE_API}${assignmentId}/`,
        method: 'DELETE'
    }).then(function() {
        showToast('成员已移除', 1500);
        loadMembers(selectedRoleId);
    }).catch(function(err) {
        showToast(parseApiError(err, '移除成员失败'), 2400);
    });
}

/* ---------------- 角色增删改 ---------------- */
function addRole(payload) {
    return $.ajax({
        url: ROLE_API,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(payload)
    }).then(function() {
        showToast('角色创建成功', 1500);
    }).catch(function(err) {
        showToast(parseApiError(err, '角色创建失败'), 2400);
        return Promise.reject(err);
    });
}

function updateRole(id, payload) {
    return $.ajax({
        url: `${ROLE_API}${id}/`,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(payload)
    }).then(function() {
        showToast('角色更新成功', 1500);
    }).catch(function(err) {
        showToast(parseApiError(err, '角色更新失败'), 2400);
        return Promise.reject(err);
    });
}

function deleteRole(id) {
    return $.ajax({
        url: `${ROLE_API}${id}/`,
        method: 'DELETE'
    }).then(function() {
        showToast('角色已删除', 1500);
    }).catch(function(err) {
        showToast(parseApiError(err, '删除角色失败'), 2400);
        return Promise.reject(err);
    });
}

let currentMode = 'add';

function openAddModal() {
    currentMode = 'add';
    $('#modalTitle').text('新建角色');
    $('#dataForm')[0].reset();
    $('#editId').val('');
    $('#dataModal').addClass('active');
}

function openEditModal(id) {
    const role = roleList.find(function(item) { return item.role_id === id; });
    if (!role) {
        showToast('未找到角色数据', 1200);
        return;
    }
    currentMode = 'edit';
    $('#modalTitle').text('编辑角色');
    $('#editId').val(role.role_id);
    $('#role_name').val(role.role_name);
    $('#description').val(role.description || '');
    $('#dataModal').addClass('active');
}

function closeModal() {
    $('#dataModal').removeClass('active');
}

function onSave() {
    const roleName = $('#role_name').val().trim();
    if (!roleName) {
        showToast('角色名称不能为空', 1500);
        return;
    }
    const payload = {
        role_name: roleName,
        description: $('#description').val().trim()
    };
    const action = currentMode === 'add'
        ? addRole(payload)
        : updateRole(parseInt($('#editId').val()), payload);
    action.then(function() {
        closeModal();
        fetchRoles(parseInt($('#editId').val()) || selectedRoleId);
    }).catch(function() {});
}

function confirmDeleteRole(id) {
    if (!confirm('确定要删除这个角色吗？已分配给用户的角色需先解除分配。')) return;
    deleteRole(id).then(function() {
        if (selectedRoleId === id) {
            selectedRoleId = null;
        }
        fetchRoles();
    }).catch(function() {});
}

let toastTimer = null;
function showToast(msg, duration) {
    let $toast = $('#roleToast');
    if (!$toast.length) {
        $toast = $('<div id="roleToast" class="toast"></div>');
        $('body').append($toast);
    }
    $toast.text(msg).addClass('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function() { $toast.removeClass('show'); }, duration || 2000);
}

$(document).ready(function() {
    fetchUsers();
    fetchRoles();

    $('#refreshBtn').on('click', function() {
        fetchUsers();
        fetchRoles(selectedRoleId);
    });
    $('#openAddModalBtn').on('click', openAddModal);
    $('#closeModalBtn, #cancelModalBtn').on('click', closeModal);
    $('#submitBtn').on('click', onSave);
    $('#dataModal').on('click', function(e) {
        if ($(e.target).hasClass('modal-overlay')) closeModal();
    });
    $('#saveMenuBtn').on('click', saveMenuPermissions);
    $('#addMemberBtn').on('click', addMember);
});
