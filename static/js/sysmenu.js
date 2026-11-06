let currentList = [];
let paginationInfo = {
    currentPage: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 1
};
const API_BASE_URL = '/api/menu/';

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[m]));
}

function renderTable(data) {
    const tbody = $('#dataTableBody');
    if (!data || data.length === 0) {
        tbody.html('<tr class="empty-row"><td colspan="8">暂无菜单数据</td></tr>');
        return;
    }
    const parentNames = {};
    data.forEach(item => { parentNames[item.menu_id] = item.menu_name; });

    let html = '';
    data.forEach(item => {
        const parentText = item.parent_id ? (parentNames[item.parent_id] || item.parent_id) : '顶级';
        html += `<tr data-id="${item.menu_id}">
            <td>${item.menu_id}</td>
            <td><strong>${escapeHtml(item.menu_name)}</strong></td>
            <td>${escapeHtml(item.menu_url || '—')}</td>
            <td><i class="${escapeHtml(item.icon || 'fas fa-circle')}" style="margin-right:6px;"></i>${escapeHtml(item.icon || '—')}</td>
            <td>${escapeHtml(item.menu_group || '其他')}</td>
            <td>${escapeHtml(String(parentText))}</td>
            <td>${item.sort_order}</td>
            <td class="action-buttons">
                <button class="edit-btn" data-id="${item.menu_id}" title="编辑"><i class="fas fa-edit"></i></button>
                <button class="delete-btn" data-id="${item.menu_id}" title="删除"><i class="fas fa-trash-alt"></i></button>
            </td>
        </tr>`;
    });
    tbody.html(html);
    $('.edit-btn').off('click').on('click', function() { openEditModal(parseInt($(this).data('id'))); });
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
        }

        currentList = data;
        paginationInfo.currentPage = page;
        paginationInfo.totalCount = count;
        paginationInfo.totalPages = Math.max(1, Math.ceil(count / paginationInfo.pageSize));

        renderTable(currentList);
        updatePaginationUI(count, paginationInfo.totalPages);
        return data;
    }).catch(err => {
        console.error('获取菜单列表失败:', err);
        currentList = [];
        renderTable([]);
        updatePaginationUI(0, 1);
        showToast(parseApiError(err, '获取菜单列表失败'), 2500);
        return null;
    });
}

function updatePaginationUI(totalCount, totalPages) {
    $('#totalCount').text(totalCount);
    $('#currentPage').text(paginationInfo.currentPage);
    $('#totalPages').text(totalPages);
    const $wrapper = $('#paginationWrapper');
    if (totalCount <= paginationInfo.pageSize) {
        $wrapper.hide();
        return;
    }
    $wrapper.show();
    $('#firstPageBtn, #prevPageBtn').prop('disabled', paginationInfo.currentPage === 1);
    $('#nextPageBtn, #lastPageBtn').prop('disabled', paginationInfo.currentPage >= totalPages);
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
        const $btn = $(`<button style="width: 32px; height: 32px; border: 1px solid #e5e7eb; border-radius: 6px; background: ${i === paginationInfo.currentPage ? '#2c6e9e' : 'white'}; color: ${i === paginationInfo.currentPage ? 'white' : '#374151'}; cursor: pointer; font-size: 0.85rem;">${i}</button>`);
        $btn.on('click', () => { paginationInfo.currentPage = i; fetchList(i); });
        $container.append($btn);
    }
}

function showToast(msg, duration = 2000) {
    let toastEl = $('#dynamicToast');
    if (toastEl.length === 0) {
        $('body').append('<div id="dynamicToast" style="position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:#2c3e50; color:white; padding:10px 20px; border-radius:40px; z-index:2000; font-size:0.85rem; box-shadow:0 5px 12px rgba(0,0,0,0.2); opacity:0; transition:0.2s; pointer-events:none;"></div>');
        toastEl = $('#dynamicToast');
    }
    toastEl.text(msg).css('opacity', '1');
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => { toastEl.css('opacity', '0'); }, duration);
}

function fillParentOptions(excludeId) {
    const $select = $('#parent_id');
    $select.html('<option value="0">顶级菜单</option>');
    currentList.forEach(item => {
        if (excludeId && item.menu_id === excludeId) return;
        $select.append(`<option value="${item.menu_id}">${escapeHtml(item.menu_name)}</option>`);
    });
}

function openAddModal() {
    $('#modalTitle').text('新增菜单');
    $('#dataForm')[0].reset();
    $('#editId').val('');
    $('#parent_id').val('0');
    fillParentOptions(null);
    $('#dataModal').addClass('active');
}

function openEditModal(menuId) {
    const item = currentList.find(m => m.menu_id === menuId);
    if (!item) { showToast('未找到数据', 1000); return; }
    $('#modalTitle').text('编辑菜单');
    $('#editId').val(item.menu_id);
    $('#menu_name').val(item.menu_name);
    $('#menu_url').val(item.menu_url || '');
    $('#icon').val(item.icon || '');
    $('#menu_group').val(item.menu_group || '');
    $('#sort_order').val(item.sort_order || 0);
    $('#remark').val(item.remark || '');
    fillParentOptions(item.menu_id);
    $('#parent_id').val(item.parent_id || 0);
    $('#dataModal').addClass('active');
}

function closeModal() { $('#dataModal').removeClass('active'); }

function onSave() {
    const menuName = $('#menu_name').val().trim();
    const menuUrl = $('#menu_url').val().trim();
    if (!menuName) { showToast('菜单名称不能为空', 1500); return; }
    if (!menuUrl) { showToast('菜单地址不能为空', 1500); return; }

    const parentId = parseInt($('#parent_id').val()) || 0;
    if (parentId && parentId === parseInt($('#editId').val())) {
        showToast('父菜单不能选择自身', 1500);
        return;
    }

    const payload = {
        menu_name: menuName,
        menu_url: menuUrl,
        icon: $('#icon').val().trim(),
        menu_group: $('#menu_group').val().trim(),
        parent_id: parentId,
        sort_order: parseInt($('#sort_order').val()) || 0,
        remark: $('#remark').val().trim()
    };

    const isEdit = !!$('#editId').val();
    const url = isEdit ? `${API_BASE_URL}${$('#editId').val()}/` : API_BASE_URL;
    $.ajax({
        url: url,
        method: isEdit ? 'PUT' : 'POST',
        contentType: 'application/json',
        data: JSON.stringify(payload)
    }).then(() => {
        closeModal();
        fetchList();
        showToast(isEdit ? '更新成功' : '新增成功', 1500);
    }).catch(err => {
        console.error('保存菜单失败:', err);
        showToast(parseApiError(err, '保存菜单失败'), 2500);
    });
}

function confirmDelete(menuId) {
    if (!confirm('确定要删除该菜单吗？删除后所有角色上的该菜单授权也会一并移除。')) return;
    $.ajax({ url: `${API_BASE_URL}${menuId}/`, method: 'DELETE' })
        .then(() => {
            fetchList();
            showToast('删除成功', 1500);
        })
        .catch(err => {
            console.error('删除菜单失败:', err);
            showToast(parseApiError(err, '删除菜单失败'), 2500);
        });
}

$(document).ready(function() {
    fetchList();
    $('#refreshBtn').on('click', function() { paginationInfo.currentPage = 1; fetchList(1); showToast('已刷新', 1500); });
    $('#openAddModalBtn').on('click', openAddModal);
    $('#closeModalBtn, #cancelModalBtn').on('click', closeModal);
    $('#submitBtn').on('click', onSave);
    $('#dataModal').on('click', function(e) { if ($(e.target).hasClass('modal-overlay')) closeModal(); });
    $('#firstPageBtn').on('click', function() { paginationInfo.currentPage = 1; fetchList(1); });
    $('#prevPageBtn').on('click', function() { if (paginationInfo.currentPage > 1) fetchList(paginationInfo.currentPage - 1); });
    $('#nextPageBtn').on('click', function() { if (paginationInfo.currentPage < paginationInfo.totalPages) fetchList(paginationInfo.currentPage + 1); });
    $('#lastPageBtn').on('click', function() { fetchList(paginationInfo.totalPages); });
});
