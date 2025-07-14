// 全局变量
let currentTable = null;
let currentData = null;
let selectedRow = null;
let currentPage = 1;
let totalPages = 1;
let perPage = 10;
let searchTerm = '';
let searchColumn = '';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeTableSelection();
    initializeSearchInput();
    initializeFormSubmissions();
});

// 初始化表选择
function initializeTableSelection() {
    document.querySelectorAll('.table-item').forEach(item => {
        item.addEventListener('click', function() {
            document.querySelectorAll('.table-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            currentTable = this.dataset.table;
        });
    });
}

// 初始化搜索输入框
function initializeSearchInput() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
}

// 初始化表单提交
function initializeFormSubmissions() {
    // 插入表单提交
    document.getElementById('insertForm').addEventListener('submit', handleInsertSubmit);
    
    // 更新表单提交
    document.getElementById('updateForm').addEventListener('submit', handleUpdateSubmit);
}

// 加载表数据
function loadTableData() {
    if (!currentTable) {
        showMessage('请先选择一个表', 'error');
        return;
    }

    // 重置分页和搜索
    currentPage = 1;
    searchTerm = '';
    searchColumn = '';
    
    fetchTableData();
}

// 获取表数据
function fetchTableData() {
    const params = new URLSearchParams({
        page: currentPage,
        per_page: perPage,
        search: searchTerm,
        search_column: searchColumn
    });

    fetch(`/db/api/tables/${currentTable}?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showMessage(data.error, 'error');
                return;
            }

            currentData = data;
            displayTableData(data);
            updateSearchControls(data);
            updatePaginationControls(data.pagination);
        })
        .catch(error => {
            showMessage('加载数据失败: ' + error, 'error');
        });
}

// 显示表数据
function displayTableData(data) {
    const container = document.getElementById('dataContainer');

    if (!data.columns || !data.rows) {
        container.innerHTML = '<div class="loading">没有数据</div>';
        return;
    }

    let html = '<table class="data-table">';
    html += '<thead><tr>';
    data.columns.forEach(column => {
        html += `<th>${column}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.rows.forEach((row, index) => {
        html += '<tr onclick="selectRow(this, ' + index + ')" style="cursor: pointer;">';
        row.forEach((cell, cellIndex) => {
            const cellValue = cell || '';
            const cellContent = formatCellContent(cellValue, index, cellIndex);
            html += `<td>${cellContent}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// 格式化单元格内容
function formatCellContent(content, rowIndex, cellIndex) {
    // 确保content是字符串类型
    const contentStr = String(content || '');
    
    if (!contentStr || contentStr.length <= 50) {
        return contentStr;
    }
    
    const shortText = contentStr.substring(0, 50) + '...';
    const fullText = contentStr;
    const cellId = `cell-${rowIndex}-${cellIndex}`;
    
    // 转义特殊字符，避免JavaScript错误
    const escapedFullText = fullText
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r');
    
    return `
        <div class="cell-content" id="${cellId}" 
             onclick="toggleCellExpand(event, '${cellId}', '${escapedFullText}')" 
             title="点击展开/折叠">
            ${shortText}
            <span class="expand-btn">展开</span>
        </div>
    `;
}

// 切换单元格展开状态
function toggleCellExpand(event, cellId, fullText) {
    event.stopPropagation(); // 阻止行选择事件
    
    const cellElement = document.getElementById(cellId);
    
    // 解码转义的文本
    const decodedFullText = fullText
        .replace(/\\n/g, '\n')
        .replace(/\\r/g, '\r')
        .replace(/\\"/g, '"')
        .replace(/\\'/g, "'")
        .replace(/\\\\/g, '\\');

    if (cellElement.classList.contains('expanded')) {
        // 折叠
        cellElement.classList.remove('expanded');
        const shortText = decodedFullText.length > 50 ? 
            decodedFullText.substring(0, 50) + '...' : 
            decodedFullText;
        cellElement.innerHTML = shortText + '<span class="expand-btn">展开</span>';
    } else {
        // 展开
        cellElement.classList.add('expanded');
        cellElement.innerHTML = decodedFullText + '<span class="expand-btn">折叠</span>';
    }
}

// 更新搜索控件
function updateSearchControls(data) {
    const searchControls = document.getElementById('searchControls');
    const searchColumnSelect = document.getElementById('searchColumn');
    
    // 显示搜索控件
    searchControls.style.display = 'block';
    
    // 更新列选择器
    searchColumnSelect.innerHTML = '<option value="">所有列</option>';
    if (data.columns) {
        data.columns.forEach(column => {
            searchColumnSelect.innerHTML += `<option value="${column}">${column}</option>`;
        });
    }
    
    // 设置当前搜索值
    document.getElementById('searchInput').value = searchTerm;
    searchColumnSelect.value = searchColumn;
}

// 更新分页控件
function updatePaginationControls(pagination) {
    if (!pagination) return;
    
    currentPage = pagination.current_page;
    totalPages = pagination.total_pages;
    perPage = pagination.per_page;
    
    // 更新分页信息
    const start = (currentPage - 1) * perPage + 1;
    const end = Math.min(currentPage * perPage, pagination.total_records);
    document.getElementById('paginationInfo').textContent = 
        `显示 ${start}-${end} 条，共 ${pagination.total_records} 条记录`;
    
    // 更新每页显示数量
    document.getElementById('perPageSelect').value = perPage;
    
    // 更新分页按钮状态
    document.getElementById('firstPage').disabled = currentPage <= 1;
    document.getElementById('prevPage').disabled = currentPage <= 1;
    document.getElementById('nextPage').disabled = currentPage >= totalPages;
    document.getElementById('lastPage').disabled = currentPage >= totalPages;
    
    // 生成页码
    generatePageNumbers();
}

// 生成页码
function generatePageNumbers() {
    const pageNumbersContainer = document.getElementById('pageNumbers');
    pageNumbersContainer.innerHTML = '';
    
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('span');
        pageBtn.className = `page-number ${i === currentPage ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => changePage(i);
        pageNumbersContainer.appendChild(pageBtn);
    }
}

// 执行搜索
function performSearch() {
    searchTerm = document.getElementById('searchInput').value;
    searchColumn = document.getElementById('searchColumn').value;
    currentPage = 1; // 重置到第一页
    fetchTableData();
}

// 清除搜索
function clearSearch() {
    document.getElementById('searchInput').value = '';
    document.getElementById('searchColumn').value = '';
    searchTerm = '';
    searchColumn = '';
    currentPage = 1;
    fetchTableData();
}

// 切换页面
function changePage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    fetchTableData();
}

// 改变每页显示数量
function changePerPage() {
    perPage = parseInt(document.getElementById('perPageSelect').value);
    currentPage = 1; // 重置到第一页
    fetchTableData();
}

// 选择行
function selectRow(row, index) {
    document.querySelectorAll('.data-table tbody tr').forEach(r => r.style.backgroundColor = '');
    row.style.backgroundColor = '#e3f2fd';
    selectedRow = index;
}

// 显示插入模态框
function showInsertModal() {
    if (!currentTable) {
        showMessage('请先选择一个表', 'error');
        return;
    }

    // 获取表结构信息
    fetch(`/db/api/table-structure/${currentTable}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showMessage(data.error, 'error');
                return;
            }

            // 保存表结构信息供批量输入使用
            window.tableStructure = data.structure;
            window.tableColumns = data.structure.filter(field => !field.can_omit).map(field => field.name);

            const fieldsContainer = document.getElementById('insertFields');
            fieldsContainer.innerHTML = '';

            data.structure.forEach(field => {
                // 跳过自增字段和有默认值的字段
                if (field.can_omit) {
                    return;
                }

                const required = field.is_nullable ? '' : 'required';
                const requiredText = field.is_nullable ? '' : ' *';
                
                fieldsContainer.innerHTML += `
                    <div class="form-group">
                        <label>${field.name}:${requiredText}</label>
                        <input type="text" name="${field.name}" placeholder="输入${field.name}" ${required}>
                        <small class="field-info">类型: ${field.type}</small>
                    </div>
                `;
            });

            // 重置输入模式
            switchInputMode('single');
            document.getElementById('insertModal').style.display = 'block';
        })
        .catch(error => {
            showMessage('获取表结构失败: ' + error, 'error');
        });
}

// 切换输入模式
function switchInputMode(mode) {
    const singleMode = document.getElementById('singleInputMode');
    const batchMode = document.getElementById('batchInputMode');
    const singleBtn = document.getElementById('singleModeBtn');
    const batchBtn = document.getElementById('batchModeBtn');
    
    if (mode === 'single') {
        singleMode.style.display = 'block';
        batchMode.style.display = 'none';
        singleBtn.classList.add('active');
        batchBtn.classList.remove('active');
    } else {
        singleMode.style.display = 'none';
        batchMode.style.display = 'block';
        singleBtn.classList.remove('active');
        batchBtn.classList.add('active');
    }
}

// 预览批量数据
function previewBatchData() {
    const inputData = document.getElementById('batchInputData').value.trim();
    if (!inputData) {
        showMessage('请输入数据', 'error');
        return;
    }

    const lines = inputData.split('\n').filter(line => line.trim());
    if (lines.length === 0) {
        showMessage('没有有效数据', 'error');
        return;
    }

    const previewDiv = document.getElementById('batchPreview');
    let previewHtml = '<table class="preview-table">';
    
    // 表头
    previewHtml += '<thead><tr>';
    window.tableColumns.forEach(col => {
        previewHtml += `<th>${col}</th>`;
    });
    previewHtml += '</tr></thead><tbody>';

    // 数据行
    lines.forEach((line, index) => {
        const values = parseBatchLine(line);
        if (values.length > 0) {
            previewHtml += '<tr>';
            window.tableColumns.forEach((col, colIndex) => {
                const value = values[colIndex] || '';
                previewHtml += `<td>${value}</td>`;
            });
            previewHtml += '</tr>';
        }
    });

    previewHtml += '</tbody></table>';
    previewDiv.innerHTML = previewHtml;
}

// 解析批量输入的行
function parseBatchLine(line) {
    // 支持制表符和逗号分隔
    if (line.includes('\t')) {
        return line.split('\t').map(val => val.trim());
    } else {
        return line.split(',').map(val => val.trim());
    }
}

// 提交批量数据
function submitBatchData() {
    const inputData = document.getElementById('batchInputData').value.trim();
    if (!inputData) {
        showMessage('请输入数据', 'error');
        return;
    }

    const lines = inputData.split('\n').filter(line => line.trim());
    if (lines.length === 0) {
        showMessage('没有有效数据', 'error');
        return;
    }

    const batchData = [];
    lines.forEach(line => {
        const values = parseBatchLine(line);
        if (values.length > 0) {
            batchData.push(values);
        }
    });

    if (batchData.length === 0) {
        showMessage('没有有效数据', 'error');
        return;
    }

    // 发送批量插入请求
    fetch(`/db/api/batch-insert/${currentTable}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            columns: window.tableColumns,
            data: batchData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(`批量插入成功：${data.inserted_count} 条记录`, 'success');
            closeModal('insertModal');
            fetchTableData();
        } else {
            showMessage(data.error, 'error');
        }
    })
    .catch(error => {
        showMessage('批量插入失败: ' + error, 'error');
        });
}

// 显示更新模态框
function showUpdateModal() {
    if (!currentTable || !currentData || selectedRow === null) {
        showMessage('请先选择一条记录', 'error');
        return;
    }

    const fieldsContainer = document.getElementById('updateFields');
    fieldsContainer.innerHTML = '';

    const selectedData = currentData.rows[selectedRow];
    currentData.columns.forEach((column, index) => {
        fieldsContainer.innerHTML += `
            <div class="form-group">
                <label>${column}:</label>
                <input type="text" name="${column}" value="${selectedData[index] || ''}" placeholder="输入${column}">
            </div>
        `;
    });

    document.getElementById('updateModal').style.display = 'block';
}

// 删除记录
function deleteSelectedRecord() {
    if (!currentTable || !currentData || selectedRow === null) {
        showMessage('请先选择一条记录', 'error');
        return;
    }

    if (!confirm('确定要删除这条记录吗？')) {
        return;
    }

    const selectedData = currentData.rows[selectedRow];
    const whereClause = currentData.columns.map(col => `${col} = %s`).join(' AND ');

    fetch(`/db/api/delete/${currentTable}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            where_clause: whereClause,
            values: selectedData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
            fetchTableData();
        } else {
            showMessage(data.error, 'error');
        }
    })
    .catch(error => {
        showMessage('删除失败: ' + error, 'error');
    });
}

// 关闭模态框
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// 显示消息
function showMessage(message, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.innerHTML = `<div class="${type}">${message}</div>`;
    setTimeout(() => {
        messageDiv.innerHTML = '';
    }, 3000);
}

// 处理插入表单提交
function handleInsertSubmit(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const columns = [];
    const values = [];

    // 只获取表单中实际存在的字段
    const formInputs = this.querySelectorAll('input[name]');
    formInputs.forEach(input => {
        const columnName = input.name;
        const value = input.value.trim();
        
        // 检查必填字段
        if (input.hasAttribute('required') && !value) {
            showMessage(`请填写必填字段: ${columnName}`, 'error');
            return;
        }
        
        columns.push(columnName);
        values.push(value);
    });

    if (columns.length === 0) {
        showMessage('没有可提交的字段', 'error');
        return;
    }

    fetch(`/db/api/insert/${currentTable}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            columns: columns,
            values: values
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
            closeModal('insertModal');
            fetchTableData();
        } else {
            showMessage(data.error, 'error');
        }
    })
    .catch(error => {
        showMessage('插入失败: ' + error, 'error');
    });
}

// 处理更新表单提交
function handleUpdateSubmit(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const setClause = currentData.columns.map(col => `${col} = %s`).join(', ');
    const whereClause = currentData.columns.map(col => `${col} = %s`).join(' AND ');
    const values = [];

    currentData.columns.forEach(column => {
        values.push(formData.get(column) || '');
    });

    // 添加WHERE条件的值
    const selectedData = currentData.rows[selectedRow];
    values.push(...selectedData);

    fetch(`/db/api/update/${currentTable}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            set_clause: setClause,
            where_clause: whereClause,
            values: values
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
            closeModal('updateModal');
            fetchTableData();
        } else {
            showMessage(data.error, 'error');
        }
    })
    .catch(error => {
        showMessage('更新失败: ' + error, 'error');
    });
}

// 点击模态框外部关闭
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
} 