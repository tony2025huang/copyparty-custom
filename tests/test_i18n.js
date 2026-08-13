#!/usr/bin/env node
/* Static contract tests for phase-one Chinese browser i18n. */
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const browser = read('copyparty/web/browser.js');
const chi = read('copyparty/web/tl/chi.js');

function must(re, text, message) { assert(re.test(text), message); }

// Browser UI: no explicit preference starts in Chinese; cplng=eng remains authoritative.
must(/function cplang\(fallback\)/, browser, 'browser exposes a language resolver');
must(/return m \? decodeURIComponent\(m\[1\]\) : fallback;/, browser, 'cookie preference wins over fallback');
must(/lang = cplang\(lang \|\| 'chi'\);/, browser, 'browser uses the server-injected Chinese default');
must(new RegExp('\\["chi", /\\^zh\\(\\?:\\$\\|\\[-_\\]\\)/i\\]'), browser,
  'Chinese mapping accepts bare zh and hyphen/underscore variants');
must(/!\/\\bcplng=\/\.test\(document\.cookie\)/, browser,
  'browser-language detection is bypassed when cplng (including cplng=eng) is set');

const chineseLocale = /^zh(?:$|[-_])/i;
for (const locale of ['zh', 'zh-CN', 'zh-TW', 'zh-HK'])
  assert(chineseLocale.test(locale), locale + ' maps to Chinese');
for (const locale of ['en', 'en-US', 'zho'])
  assert(!chineseLocale.test(locale), locale + ' does not map to Chinese');

// Fork-specific terminal upload controls must be localized in Chinese too.
must(/"u_retry": "重试"/, chi, 'Chinese Retry string is present');
must(/"u_remove": "移除"/, chi, 'Chinese Remove string is present');
must(/"u_cancelled": "已取消"/, chi, 'Chinese cancelled string is present');

const boot = read('copyparty/web/i18n.js');
must(/var I18N = \{/, boot, 'shared auxiliary-page bootstrap exists');
must(/defaultLang: 'chi'/, boot, 'shared bootstrap defaults to Chinese');
for (const key of ['refresh', 'control_panel', 'loading', 'error', 'confirm', 'empty'])
  must(new RegExp('\\b' + key + '\\s*:'), boot, 'bootstrap includes ' + key);

for (const page of ['browser', 'splash', 'shares', 'rups', 'svcs', 'idp', 'md', 'mde', 'msg'])
  must(/<html lang="\{\{ 'zh-CN' if lang == 'chi' else 'en' \}\}"/, read('copyparty/web/' + page + '.html'),
    page + ' emits the selected document language');

const httpcli = read('copyparty/httpcli.py');
must(/def ui_lang\(self\)/, httpcli, 'server centralizes template language selection');
must(/return self\.cookies\.get\("cplng"\) or self\.args\.lang/, httpcli,
  'language cookie overrides the server default');
must(/ka\["lang"\] = self\.ui_lang\(\)/, httpcli,
  'browser templates receive the selected language');
must(/"lang": self\.ui_lang\(\)/, httpcli,
  'markdown templates receive the selected language');

console.log('i18n static contract tests: ok');
