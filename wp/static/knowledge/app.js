const API_BASE = '/api/knowledge';
const API_KEY_STORAGE = 'kb_api_key';

const COLUMN_DEFINITIONS = [
    { key: 'article_id', label: '文章ID', default: false },
    { key: 'article_title', label: '文章标题', default: true },
    { key: 'article_url', label: '文章链接', default: false },
    { key: 'tag', label: '标签', default: true },
    { key: 'original_link', label: '原始分享', default: true },
    { key: 'original_password', label: '原始密码', default: true },
    { key: 'new_link', label: '新分享', default: true },
    { key: 'new_password', label: '新密码', default: true },
    { key: 'new_title', label: '新标题', default: false },
    { key: 'status', label: '状态', default: true },
    { key: 'error_message', label: '错误信息', default: false },
    { key: 'created_at', label: '创建时间', default: true },
    { key: 'updated_at', label: '更新时间', default: false }
];

const STATUS_LABELS = {
    pending: '待处理',
    processing: '处理中',
    transferred: '已转存',
    completed: '已完成',
    failed: '失败'
};

class KnowledgeApp {
    constructor() {
        this.apiKey = localStorage.getItem(API_KEY_STORAGE) || '';
        this.currentPage = 1;
        this.pageSize = 50;
        this.filters = {
            search: '',
            status: [],
            tag: '',
            dateFrom: '',
            dateTo: '',
            sort: 'created_at',
            order: 'DESC'
        };
        this.visibleColumns = COLUMN_DEFINITIONS
            .filter(col => col.default)
            .map(col => col.key);
        this.allTags = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        if (this.apiKey) {
            this.showMainContent();
            this.loadInitialData();
        }
    }

    setupEventListeners() {
        document.getElementById('saveApiKeyBtn').addEventListener('click', () => this.saveApiKey());
        document.getElementById('apiKeyInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.saveApiKey();
        });

        document.getElementById('applyFiltersBtn').addEventListener('click', () => this.applyFilters());
        document.getElementById('resetFiltersBtn').addEventListener('click', () => this.resetFilters());
        
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.applyFilters();
        });

        document.getElementById('refreshBtn').addEventListener('click', () => this.refreshData());
        document.getElementById('exportBtn').addEventListener('click', () => this.showExportModal());
        document.getElementById('columnSettingsBtn').addEventListener('click', () => this.showColumnModal());

        document.getElementById('prevPageBtn').addEventListener('click', () => this.goToPage(this.currentPage - 1));
        document.getElementById('nextPageBtn').addEventListener('click', () => this.goToPage(this.currentPage + 1));
        document.getElementById('pageSizeSelect').addEventListener('change', (e) => {
            this.pageSize = parseInt(e.target.value);
            this.currentPage = 1;
            this.loadEntries();
        });

        document.getElementById('retryBtn').addEventListener('click', () => this.loadEntries());

        this.setupModalListeners('columnModal');
        this.setupModalListeners('exportModal');

        document.getElementById('applyColumnsBtn').addEventListener('click', () => this.applyColumnSettings());
        document.getElementById('selectAllColumnsBtn').addEventListener('click', () => this.toggleAllColumns());
        document.getElementById('confirmExportBtn').addEventListener('click', () => this.exportData());
    }

    setupModalListeners(modalId) {
        const modal = document.getElementById(modalId);
        const closeBtn = modal.querySelector('.modal-close');
        const cancelBtn = modal.querySelector('.modal-cancel');

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideModal(modalId));
        }
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideModal(modalId));
        }

        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.hideModal(modalId);
        });
    }

    async saveApiKey() {
        const input = document.getElementById('apiKeyInput');
        const key = input.value.trim();
        
        if (!key) {
            this.showToast('请输入API密钥', 'error');
            return;
        }

        this.apiKey = key;
        localStorage.setItem(API_KEY_STORAGE, key);
        
        try {
            const response = await this.fetchAPI('/tags');
            if (response.success) {
                this.showToast('API密钥验证成功', 'success');
                this.showMainContent();
                this.loadInitialData();
            }
        } catch (error) {
            this.apiKey = '';
            localStorage.removeItem(API_KEY_STORAGE);
            this.showToast('API密钥验证失败', 'error');
        }
    }

    showMainContent() {
        document.getElementById('apiKeySection').style.display = 'none';
        document.getElementById('mainContent').style.display = 'grid';
    }

    async loadInitialData() {
        await Promise.all([
            this.loadTags(),
            this.loadStatuses(),
            this.loadEntries()
        ]);
    }

    async loadTags() {
        try {
            const response = await this.fetchAPI('/tags');
            if (response.success) {
                this.allTags = response.data.tags;
                this.populateTagFilter();
            }
        } catch (error) {
            console.error('加载标签失败:', error);
        }
    }

    populateTagFilter() {
        const select = document.getElementById('tagFilter');
        select.innerHTML = '<option value="">全部标签</option>';
        this.allTags.forEach(tag => {
            const option = document.createElement('option');
            option.value = tag;
            option.textContent = tag;
            select.appendChild(option);
        });
    }

    async loadStatuses() {
        try {
            const response = await this.fetchAPI('/statuses');
            if (response.success) {
                this.renderStatusFilters(response.data.statuses);
                this.renderSummaryCards(response.data.statuses);
            }
        } catch (error) {
            console.error('加载状态失败:', error);
        }
    }

    renderStatusFilters(statuses) {
        const container = document.getElementById('statusFilters');
        container.innerHTML = '';
        
        Object.keys(statuses).forEach(status => {
            const div = document.createElement('div');
            div.className = 'checkbox-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `status_${status}`;
            checkbox.value = status;
            checkbox.checked = this.filters.status.includes(status);
            
            const label = document.createElement('label');
            label.htmlFor = `status_${status}`;
            label.textContent = `${STATUS_LABELS[status] || status} (${statuses[status]})`;
            
            div.appendChild(checkbox);
            div.appendChild(label);
            container.appendChild(div);
        });
    }

    renderSummaryCards(statuses) {
        const container = document.getElementById('summaryCards');
        container.innerHTML = '';
        
        const statusOrder = ['pending', 'processing', 'transferred', 'completed', 'failed'];
        
        statusOrder.forEach(status => {
            if (statuses[status] !== undefined) {
                const card = document.createElement('div');
                card.className = `summary-card ${status}`;
                card.innerHTML = `
                    <span class="label">${STATUS_LABELS[status] || status}</span>
                    <span class="count">${statuses[status]}</span>
                `;
                container.appendChild(card);
            }
        });
    }

    async loadEntries() {
        this.showLoadingState();
        
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize,
                sort: this.filters.sort,
                order: this.filters.order
            });

            if (this.filters.search) params.append('search', this.filters.search);
            if (this.filters.status.length === 1) params.append('status', this.filters.status[0]);
            if (this.filters.tag) params.append('tag', this.filters.tag);
            if (this.filters.dateFrom) params.append('date_from', this.filters.dateFrom);
            if (this.filters.dateTo) params.append('date_to', this.filters.dateTo);

            const response = await this.fetchAPI(`/entries?${params}`);
            
            if (response.success) {
                this.renderTable(response.data.entries);
                this.renderPagination(response.data.pagination);
                this.updateResultsCount(response.data.pagination);
                
                if (response.summary) {
                    this.renderSummaryCards(response.summary);
                }
            }
        } catch (error) {
            this.showErrorState(error.message);
        }
    }

    renderTable(entries) {
        if (entries.length === 0) {
            this.showEmptyState();
            return;
        }

        const header = document.getElementById('tableHeader');
        const body = document.getElementById('tableBody');
        
        header.innerHTML = '';
        body.innerHTML = '';

        this.visibleColumns.forEach(colKey => {
            const colDef = COLUMN_DEFINITIONS.find(c => c.key === colKey);
            if (colDef) {
                const th = document.createElement('th');
                th.textContent = colDef.label;
                header.appendChild(th);
            }
        });

        const actionsHeader = document.createElement('th');
        actionsHeader.textContent = '操作';
        header.appendChild(actionsHeader);

        entries.forEach(entry => {
            const tr = document.createElement('tr');
            
            this.visibleColumns.forEach(colKey => {
                const td = document.createElement('td');
                td.innerHTML = this.formatCell(colKey, entry);
                tr.appendChild(td);
            });

            const actionsTd = document.createElement('td');
            actionsTd.innerHTML = this.renderActions(entry);
            tr.appendChild(actionsTd);
            
            body.appendChild(tr);
        });

        this.showTableState();
    }

    formatCell(key, entry) {
        const value = entry[key] || '';
        
        switch (key) {
            case 'status':
                return `<span class="status-badge ${value}">${STATUS_LABELS[value] || value}</span>`;
            
            case 'tag':
                return `<span class="tag-chip">${value}</span>`;
            
            case 'article_url':
            case 'original_link':
            case 'new_link':
                if (!value) return '<span style="color: #bbb;">-</span>';
                return `<a href="${this.escapeHtml(value)}" target="_blank" rel="noopener" class="link-text" title="${this.escapeHtml(value)}">${this.escapeHtml(this.truncate(value, 30))}</a>`;
            
            case 'original_password':
            case 'new_password':
                if (!value) return '<span style="color: #bbb;">-</span>';
                return `<span class="password-hidden" title="${this.escapeHtml(value)}">••••</span>`;
            
            case 'created_at':
            case 'updated_at':
                if (!value) return '<span style="color: #bbb;">-</span>';
                return this.formatDateTime(value);
            
            case 'error_message':
                if (!value) return '<span style="color: #bbb;">-</span>';
                return `<span title="${this.escapeHtml(value)}">${this.escapeHtml(this.truncate(value, 30))}</span>`;
            
            case 'article_title':
            case 'new_title':
                if (!value) return '<span style="color: #bbb;">-</span>';
                return `<span title="${this.escapeHtml(value)}">${this.escapeHtml(this.truncate(value, 40))}</span>`;
            
            default:
                return this.escapeHtml(value);
        }
    }

    renderActions(entry) {
        const actions = [];
        
        if (entry.new_link) {
            actions.push(`<button class="btn-icon" onclick="app.copyToClipboard('${this.escapeHtml(entry.new_link)}', '新链接')" title="复制新链接">📋 链接</button>`);
        }
        
        if (entry.new_password) {
            actions.push(`<button class="btn-icon" onclick="app.copyToClipboard('${this.escapeHtml(entry.new_password)}', '新密码')" title="复制新密码">🔑 密码</button>`);
        }
        
        if (entry.original_link) {
            actions.push(`<button class="btn-icon" onclick="window.open('${this.escapeHtml(entry.original_link)}', '_blank')" title="打开原始链接">🔗 原始</button>`);
        }
        
        return `<div class="cell-actions">${actions.join('')}</div>`;
    }

    renderPagination(pagination) {
        document.getElementById('pageInfo').textContent = 
            `第 ${pagination.page} / ${pagination.total_pages} 页 (共 ${pagination.total} 条)`;
        
        document.getElementById('prevPageBtn').disabled = pagination.page <= 1;
        document.getElementById('nextPageBtn').disabled = pagination.page >= pagination.total_pages;
        
        document.getElementById('paginationContainer').style.display = 'flex';
    }

    updateResultsCount(pagination) {
        document.getElementById('resultsCount').textContent = 
            `显示 ${pagination.total} 条结果`;
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadEntries();
    }

    applyFilters() {
        this.filters.search = document.getElementById('searchInput').value.trim();
        this.filters.tag = document.getElementById('tagFilter').value;
        this.filters.dateFrom = document.getElementById('dateFrom').value;
        this.filters.dateTo = document.getElementById('dateTo').value;
        this.filters.sort = document.getElementById('sortField').value;
        this.filters.order = document.getElementById('sortOrder').value;
        
        const statusCheckboxes = document.querySelectorAll('#statusFilters input[type="checkbox"]:checked');
        this.filters.status = Array.from(statusCheckboxes).map(cb => cb.value);
        
        this.currentPage = 1;
        this.loadEntries();
        this.showToast('筛选条件已应用', 'info');
    }

    resetFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('tagFilter').value = '';
        document.getElementById('dateFrom').value = '';
        document.getElementById('dateTo').value = '';
        document.getElementById('sortField').value = 'created_at';
        document.getElementById('sortOrder').value = 'DESC';
        
        document.querySelectorAll('#statusFilters input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
        });
        
        this.filters = {
            search: '',
            status: [],
            tag: '',
            dateFrom: '',
            dateTo: '',
            sort: 'created_at',
            order: 'DESC'
        };
        
        this.currentPage = 1;
        this.loadEntries();
        this.showToast('筛选条件已重置', 'info');
    }

    refreshData() {
        this.loadInitialData();
        this.showToast('数据已刷新', 'success');
    }

    showColumnModal() {
        const container = document.getElementById('columnCheckboxes');
        container.innerHTML = '';
        
        COLUMN_DEFINITIONS.forEach(col => {
            const div = document.createElement('div');
            div.className = 'checkbox-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `col_${col.key}`;
            checkbox.value = col.key;
            checkbox.checked = this.visibleColumns.includes(col.key);
            
            const label = document.createElement('label');
            label.htmlFor = `col_${col.key}`;
            label.textContent = col.label;
            
            div.appendChild(checkbox);
            div.appendChild(label);
            container.appendChild(div);
        });
        
        this.showModal('columnModal');
    }

    toggleAllColumns() {
        const checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        checkboxes.forEach(cb => cb.checked = !allChecked);
    }

    applyColumnSettings() {
        const checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]:checked');
        this.visibleColumns = Array.from(checkboxes).map(cb => cb.value);
        
        if (this.visibleColumns.length === 0) {
            this.showToast('请至少选择一列', 'error');
            return;
        }
        
        this.hideModal('columnModal');
        this.loadEntries();
        this.showToast('列设置已更新', 'success');
    }

    showExportModal() {
        const info = document.getElementById('exportInfo');
        const columnNames = this.visibleColumns
            .map(key => COLUMN_DEFINITIONS.find(c => c.key === key)?.label)
            .filter(Boolean)
            .join(', ');
        
        const filterInfo = [];
        if (this.filters.search) filterInfo.push(`关键词: ${this.filters.search}`);
        if (this.filters.status.length) filterInfo.push(`状态: ${this.filters.status.map(s => STATUS_LABELS[s]).join(', ')}`);
        if (this.filters.tag) filterInfo.push(`标签: ${this.filters.tag}`);
        if (this.filters.dateFrom || this.filters.dateTo) {
            filterInfo.push(`日期: ${this.filters.dateFrom || '不限'} ~ ${this.filters.dateTo || '不限'}`);
        }
        
        info.innerHTML = `
            <p><strong>导出列:</strong> ${columnNames}</p>
            <p><strong>筛选条件:</strong> ${filterInfo.length ? filterInfo.join('; ') : '无'}</p>
        `;
        
        this.showModal('exportModal');
    }

    async exportData() {
        const btn = document.getElementById('confirmExportBtn');
        btn.disabled = true;
        btn.textContent = '导出中...';
        
        try {
            const params = new URLSearchParams({
                fields: this.visibleColumns.join(','),
                sort: this.filters.sort,
                order: this.filters.order
            });

            if (this.filters.search) params.append('search', this.filters.search);
            if (this.filters.status.length === 1) params.append('status', this.filters.status[0]);
            if (this.filters.tag) params.append('tag', this.filters.tag);
            if (this.filters.dateFrom) params.append('date_from', this.filters.dateFrom);
            if (this.filters.dateTo) params.append('date_to', this.filters.dateTo);

            const response = await fetch(`${API_BASE}/export?${params}`, {
                headers: { 'X-API-Key': this.apiKey }
            });

            if (!response.ok) {
                throw new Error(`导出失败: ${response.statusText}`);
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `knowledge_export_${new Date().toISOString().slice(0, 10)}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.hideModal('exportModal');
            this.showToast('导出成功', 'success');
        } catch (error) {
            this.showToast(error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<span class="icon">📥</span> 确认导出';
        }
    }

    async copyToClipboard(text, label) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast(`${label}已复制`, 'success');
        } catch (error) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            this.showToast(`${label}已复制`, 'success');
        }
    }

    async fetchAPI(endpoint) {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: { 'X-API-Key': this.apiKey }
        });

        if (!response.ok) {
            if (response.status === 401) {
                this.apiKey = '';
                localStorage.removeItem(API_KEY_STORAGE);
                location.reload();
            }
            throw new Error(`API请求失败: ${response.statusText}`);
        }

        return await response.json();
    }

    showModal(modalId) {
        document.getElementById(modalId).style.display = 'flex';
    }

    hideModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    showLoadingState() {
        document.getElementById('loadingState').style.display = 'block';
        document.getElementById('errorState').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('tableContainer').style.display = 'none';
        document.getElementById('paginationContainer').style.display = 'none';
    }

    showErrorState(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('errorState').style.display = 'block';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('tableContainer').style.display = 'none';
        document.getElementById('paginationContainer').style.display = 'none';
    }

    showEmptyState() {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('errorState').style.display = 'none';
        document.getElementById('emptyState').style.display = 'block';
        document.getElementById('tableContainer').style.display = 'none';
        document.getElementById('paginationContainer').style.display = 'none';
    }

    showTableState() {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('errorState').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('tableContainer').style.display = 'block';
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = 'block';

        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    truncate(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    formatDateTime(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateStr;
        }
    }
}

const app = new KnowledgeApp();
