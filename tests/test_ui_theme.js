#!/usr/bin/env node
/* Static contract tests for the self-contained copyparty modern UI theme. */
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const must = (re, text, message) => assert(re.test(text), message);

const theme = read('copyparty/web/custom-modern.css');
const resources = read('copyparty/__init__.py');

must(/web\/custom-modern\.css/, resources,
  'modern stylesheet is registered as a same-origin embedded web resource');
must(/:root\s*\{[\s\S]*color-scheme:\s*light;[\s\S]*--sf-primary:\s*#1677e8;/, theme,
  'theme defaults to the light blue SaaS palette');
must(/html\.z\s*\{[\s\S]*color-scheme:\s*dark;[\s\S]*--sf-bg:\s*#101827;/, theme,
  'dark copyparty theme classes receive an explicit dark palette');
must(/html\.y\s*\{\s*color-scheme:\s*light;/, theme,
  'light copyparty theme classes remain explicitly supported');

for (const selector of [
  '#ops', '#path', '#tree', '#files', '#u2btn', '#u2tabw', '#u2cards',
  '#toast', '#tt', '#rcm', '#ht_spl #wrap', '#ht_md #mh', '#ht_msg #box'
]) {
  assert(theme.includes(selector), 'theme styles key UI selector ' + selector);
}

must(/@media \(max-width: 48em\)[\s\S]*#files td:nth-child\(n\+4\)/, theme,
  'narrow screens reduce secondary browser list columns');
must(/@media \(max-width: 48em\)[\s\S]*#u2tab\s*\{[\s\S]*min-width:\s*34rem;/, theme,
  'narrow screens preserve upload task table usability by scrolling it');
must(/@media \(prefers-reduced-motion: reduce\)/, theme,
  'theme respects reduced-motion preferences');
assert(!/https?:\/\//.test(theme), 'theme does not depend on an external CDN or web asset');

const pages = ['browser', 'splash', 'shares', 'rups', 'idp', 'md', 'mde', 'msg', 'svcs'];
for (const page of pages) {
  const html = read('copyparty/web/' + page + '.html');
  must(/<link rel="stylesheet" media="screen" href="\{\{ r \}\}\/.cpr\/w\/custom-modern\.css\?_\=\{\{ ts \}\}">/, html,
    page + ' injects the same-origin modern stylesheet');
  assert(html.indexOf('custom-modern.css') < html.indexOf('{{ html_head }}'),
    page + ' loads the built-in theme before optional html_head customizations');
}

console.log('ui-theme static contract tests: ok');
