let currentList = [];
let isApiAvailable = true;
let paginationInfo = {
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};
const API_BASE_URL = '/api/role/';
const MENU_API_URL = '/api/menu/';
const ROLE_MENU_API_URL = '/api/role_menu/';

const menuList = [
    { menu_id: 1, menu_name: '客户管理', parent_id: 0, type: 'business' },
    { menu_id: 2, menu_name: '银行卡管理', parent_id: 0, type: 'business' },
    { menu_id: 3, menu_name: '交易管理', parent_id: 0, type: 'business' },
    { menu_id: 4, menu_name: '系统用户', parent_id: 0, type: 'permission' },
    { menu_id: 5, menu_name: '角色管理', parent_id: 0, type: 'permission' },
    { menu_id: 6, menu_name: '用户角色关联', parent_id: 0, type: 'permission' }
];

function renderTable(data) {
    const tbody = $('#dataTableBody');
    if (!data || data.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="4">暂无角色数据</td></tr>');
        return;
    }
    let html = '';
    data.forEach(item => {
        html += `<tr data-id="${item.role_id}">
            <td>${item.role_id}</td>
            <td><strong>${escapeHtml(item.role_name)}</strong></td>
            <td>${escapeHtml(item.description || '—')}</td>
            <td class="action-buttons">
                <button class="edit-btn" data-id="${item.role_id}" title="编辑"><i class="fas fa-edit"></i></button>
                <button class="menu-btn" data-id="${item.role_id}" title="分配菜单"><i class="fas fa-list"></i></button>
                <button class="delete-btn" data-id="${item.role_id}" title="删除"><i class="fas fa-trash-alt"></i></button>
            </td>
        </tr>`;
    });
    tbody.html(html);
    $('.edit-btn').off('click').on('click', function() { openEditModal(parseInt($(this).data('id'))); });
    $('.menu-btn').off('click').on('click', function() { openMenuModal(parseInt($(this).data('id'))); });
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
    }).catch(() => {
        isApiAvailable = false;
        renderTable([]);
        showToast("⚠️ 接口调用失败", 3000);
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
    }).catch(() => {
        isApiAvailable = false;
        const newId = currentList.length ? Math.max(...currentList.map(u => u.role_id)) + 1 : 1;
        currentList.push({ role_id: newId, ...payload });
        renderTable(currentList);
        showToast("⚠️ 已本地新增", 2000);
    });
}

function updateItem(id, payload) {
    return $.ajax({
        url: `${API_BASE_URL}${id}/`,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(payload)
    }).then(() => {
        fetchList();
        showToast("更新成功", 1500);
    }).catch(() => {
        isApiAvailable = false;
        const idx = currentList.findIndex(u => u.role_id === id);
        if (idx !== -1) { currentList[idx] = { ...currentList[idx], ...payload, role_id: id }; }
        renderTable(currentList);
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
    }).catch(() => {
        const idx = currentList.findIndex(u => u.role_id === id);
        if (idx !== -1) { currentList.splice(idx, 1); }
        renderTable(currentList);
        showToast("⚠️ 删除失败，请检查是否有用户已分配该角色", 2000);
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
    $('#modalTitle').text('新增角色');
    $('#dataForm')[0].reset();
    $('#editId').val('');
    $('#dataModal').addClass('active');
}

function openEditModal(id) {
    const item = currentList.find(u => u.role_id === id);
    if (!item) { showToast("未找到数据", 1000); return; }
    currentMode = 'edit';
    $('#modalTitle').text('编辑角色');
    $('#editId').val(item.role_id);
    $('#role_name').val(item.role_name);
    $('#description').val(item.description || '');
    $('#dataModal').addClass('active');
}

function closeModal() { $('#dataModal').removeClass('active'); }

function onSave() {
    const roleName = $('#role_name').val().trim();
    if (!roleName) { showToast("角色名称不能为空", 1500); return; }

    const payload = {
        role_name: roleName,
        description: $('#description').val().trim()
    };

    if (currentMode === 'add') {
        addItem(payload).then(() => closeModal());
    } else {
        updateItem(parseInt($('#editId').val()), payload).then(() => closeModal());
    }
}

function confirmDelete(id) {
    if (confirm('确定要删除这个角色吗？')) { deleteItem(id); }
}

function openMenuModal(roleId) {
    const userId = sessionStorage.getItem('user_id');
    
    // 未登录/无角色时，和超级管理员一样可以使用此功能
    if (!userId) {
        $('#menuRoleId').val(roleId);
        const roleName = currentList.find(r => r.role_id === roleId)?.role_name || '';
        $('#menuModalTitle').text(`分配菜单权限 - ${roleName}`);
        loadMenuItems(roleId);
        $('#menuModal').addClass('active');
        return;
    }
    
    $.ajax({
        url: '/api/check_super_admin/',
        method: 'GET',
        data: { user_id: userId },
        timeout: 3000
    }).then(response => {
        if (response.is_super_admin) {
            $('#menuRoleId').val(roleId);
            const roleName = currentList.find(r => r.role_id === roleId)?.role_name || '';
            $('#menuModalTitle').text(`分配菜单权限 - ${roleName}`);
            loadMenuItems(roleId);
            $('#menuModal').addClass('active');
        } else {
            showToast("你目前无权限使用此功能", 2000);
        }
    }).catch(() => {
        showToast("你目前无权限使用此功能", 2000);
    });
}

function closeMenuModal() {
    $('#menuModal').removeClass('active');
}

function loadMenuItems(roleId) {
    $.ajax({
        url: `${ROLE_MENU_API_URL}?role_id=${roleId}`,
        method: 'GET',
        timeout: 5000
    }).then(response => {
        let assignedMenuIds = [];
        if (Array.isArray(response)) {
            assignedMenuIds = response.map(item => item.menu_id);
        } else if (response.results) {
            assignedMenuIds = response.results.map(item => item.menu_id);
        }
        renderMenuItems(assignedMenuIds);
    }).catch(() => {
        renderMenuItems([]);
    });
}

function renderMenuItems(assignedMenuIds) {
    const businessMenus = menuList.filter(m => m.type === 'business');
    const permissionMenus = menuList.filter(m => m.type === 'permission');
    
    let businessHtml = '';
    businessMenus.forEach(menu => {
        const isChecked = assignedMenuIds.includes(menu.menu_id);
        businessHtml += `
            <div class="menu-item ${isChecked ? 'selected' : ''}" data-menu-id="${menu.menu_id}">
                <input type="checkbox" id="menu_${menu.menu_id}" ${isChecked ? 'checked' : ''}>
                <label for="menu_${menu.menu_id}">${escapeHtml(menu.menu_name)}</label>
            </div>
        `;
    });
    
    let permissionHtml = '';
    permissionMenus.forEach(menu => {
        const isChecked = assignedMenuIds.includes(menu.menu_id);
        permissionHtml += `
            <div class="menu-item ${isChecked ? 'selected' : ''}" data-menu-id="${menu.menu_id}">
                <input type="checkbox" id="menu_${menu.menu_id}" ${isChecked ? 'checked' : ''}>
                <label for="menu_${menu.menu_id}">${escapeHtml(menu.menu_name)}</label>
            </div>
        `;
    });
    
    $('#businessMenuItems').html(businessHtml);
    $('#permissionMenuItems').html(permissionHtml);
    
    $('.menu-item').off('click').on('click', function(e) {
        const checkbox = $(this).find('input[type="checkbox"]');
        if (e.target !== checkbox[0]) {
            checkbox.prop('checked', !checkbox.prop('checked'));
        }
        $(this).toggleClass('selected', checkbox.prop('checked'));
    });
}

function saveMenuPermissions() {
    const roleId = parseInt($('#menuRoleId').val());
    const selectedMenus = [];
    
    $('.menu-item input[type="checkbox"]:checked').each(function() {
        selectedMenus.push(parseInt($(this).attr('id').replace('menu_', '')));
    });
    
    $.ajax({
        url: `${ROLE_MENU_API_URL}batch/`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ role_id: roleId, menu_ids: selectedMenus })
    }).then(() => {
        showToast("菜单权限分配成功", 1500);
        closeMenuModal();
    }).catch(() => {
        showToast("⚠️ 保存失败", 2000);
    });
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

    $('#closeMenuModalBtn, #cancelMenuModalBtn').on('click', closeMenuModal);
    $('#saveMenuBtn').on('click', saveMenuPermissions);
    $('#menuModal').on('click', function(e) { if ($(e.target).hasClass('modal-overlay')) closeMenuModal(); });

    setInterval(function() { fetchList(paginationInfo.currentPage); }, 30000);
});