"use strict";

/* Shared lightweight i18n for auxiliary pages which do not load browser.js.
 * cplng is the same preference cookie used by browser.js. */
var I18N = {
    defaultLang: 'chi',
    en: {
        refresh: 'refresh', control_panel: 'control panel', loading: 'Loading',
        error: 'Error', confirm: 'Confirm', empty: 'Nothing to show',
        files: 'files', filter: 'Filter', forget: 'forget', user: 'user',
        groups: 'groups', delete: 'delete', source: 'source', created: 'created',
        expires: 'expires', browse_files: 'browse files', show_qr: 'show QR',
        use_password: 'use real password', go_dark: 'go dark', hide_nav: 'hide nav',
        save: 'save', tools: 'tools', help: 'help', view_raw: 'view raw',
        no_active_shares: "you don't have any active shares", no_uploads: 'there are no uploads',
        permissions: 'permissions', file_count: 'file count', time_left: 'time left',
        add_time: 'add time', share_key: 'share key', password: 'password',
        size: 'size', who: 'who', when: 'when', age: 'age', directory: 'directory',
        file: 'file', showing_files: 'showing {n} files', matching_filter: ' matching the filter',
        no_idp_users: 'there are no IdP users in the cache', choose_os: 'or choose your OS for cooler alternatives:',
        placeholders: 'placeholders'
    },
    chi: {
        refresh: '刷新', control_panel: '控制面板', loading: '正在加载', error: '错误',
        confirm: '确认', empty: '暂无内容', files: '文件', filter: '筛选', forget: '忘记',
        user: '用户', groups: '群组', delete: '删除', source: '来源', created: '创建时间',
        expires: '过期时间', browse_files: '浏览文件', show_qr: '显示二维码',
        use_password: '使用真实密码', go_dark: '切换深色', hide_nav: '隐藏导航',
        save: '保存', tools: '工具', help: '帮助', view_raw: '查看原文',
        no_active_shares: '你没有活跃的分享', no_uploads: '没有上传记录',
        permissions: '权限', file_count: '文件数', time_left: '剩余时间',
        add_time: '增加时间', share_key: '分享密钥', password: '密码',
        size: '大小', who: '用户', when: '时间', age: '距今', directory: '目录',
        file: '文件', showing_files: '显示 {n} 个文件', matching_filter: '（匹配筛选条件）',
        no_idp_users: 'IdP 缓存中没有用户', choose_os: '或选择你的操作系统以获取其他连接方式：',
        placeholders: '占位符'
    },
    lang: function () {
        var m = /(?:^|;\s*)cplng=([^;]+)/.exec(document.cookie || '');
        var v = m ? decodeURIComponent(m[1]) : (window.lang || I18N.defaultLang);
        return v === 'eng' ? 'en' : 'chi';
    },
    t: function (key) {
        var d = I18N[I18N.lang()];
        return d[key] || I18N.en[key] || key;
    },
    tf: function (key, values) {
        var s = I18N.t(key);
        for (var k in values) s = s.replace('{' + k + '}', values[k]);
        return s;
    },
    apply: function () {
        document.documentElement.lang = I18N.lang() === 'chi' ? 'zh-CN' : 'en';
        var es = document.querySelectorAll('[data-i18n]');
        for (var i = 0; i < es.length; i++) es[i].textContent = I18N.t(es[i].getAttribute('data-i18n'));
        var ps = document.querySelectorAll('[data-i18n-placeholder]');
        for (var j = 0; j < ps.length; j++) ps[j].placeholder = I18N.t(ps[j].getAttribute('data-i18n-placeholder'));
    }
};

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', I18N.apply);
else I18N.apply();
