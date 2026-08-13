#!/usr/bin/env node
/* Focused static contract tests for the custom up2k terminal-task controls. */
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const up2k = fs.readFileSync(path.join(root, 'copyparty/web/up2k.js'), 'utf8');
const browser = fs.readFileSync(path.join(root, 'copyparty/web/browser.js'), 'utf8');

function must(re, text, message) {
    assert(re.test(text), message);
}

must(/function unqueue_up\(t\)/, up2k, 'keeps low-level unqueue_up');
must(/function retry_terminal\(t\)/, up2k, 'adds an explicit retry action');
must(/function remove_terminal\(t\)/, up2k, 'adds an explicit remove action');
must(/if \(!t \|\| !t\.terminal \|\| t\.removed \|\| t\.done\)/, up2k,
    'retry/remove are limited to terminal tasks');
must(/abort_task_requests\(t\);[\s\S]*drop_from\(st\.todo\.head, t\);[\s\S]*drop_from\(st\.busy\.upload, t, t\.n\);/,
    up2k, 'remove aborts requests and removes only this task from all queues');
must(/try \{ xhr\.abort\(\); \} catch \(ex\) \{ \}/, up2k,
    'remove aborts tracked XHRs');
must(/t\.abort_controller\.abort\(\)/, up2k, 'remove supports an AbortController when one is attached');
must(/function task_live\(t, generation\)[\s\S]*!t\.removed && !t\.terminal && !t\.done[\s\S]*t\.generation === generation/, up2k,
    'all async task callbacks share a generation/terminal/removal liveness guard');
must(/function mark_terminal\(t, why\) \{[\s\S]*if \(t\.removed \|\| t\.terminal\)[\s\S]*t\.generation = \(t\.generation \|\| 0\) \+ 1;[\s\S]*if \(!t\.terminal_counted\)[\s\S]*st\.bytes\.finished \+= t\.size;/, up2k,
    'terminal transition is idempotent and counts finished once');
must(/function wexec_hash\(t, chunksize, nchunks\)[\s\S]*function go_fail\(\) \{[\s\S]*apop\(st\.busy\.hash, t\);[\s\S]*\n\s*\}/, up2k,
    'worker failure leaves finished accounting exclusively to mark_terminal');
must(/function exec_hash\(\) \{[\s\S]*if \(!t \|\| t\.removed \|\| t\.terminal \|\| t\.done\)[\s\S]*var generation = t\.generation \|\| 0;/, up2k,
    'hash executor skips terminal/removed tasks and captures a generation');
must(/reader\.onload = function \(e\) \{[\s\S]*task_live\(t, generation\)/, up2k,
    'FileReader completion is guarded');
must(/if \(!task_live\(t, generation\)\)[\s\S]*return;[\s\S]*var hslice = new Uint8Array\(hashbuf\)/, up2k,
    'digest completion is guarded before hash mutation');
must(/function exec_handshake\(\) \{[\s\S]*if \(!t \|\| t\.removed \|\| t\.terminal \|\| t\.done\)[\s\S]*var generation = t\.generation \|\| 0;/, up2k,
    'handshake executor skips terminal/removed tasks');
must(/function exec_upload\(\) \{[\s\S]*if \(!t \|\| t\.removed \|\| t\.terminal \|\| t\.done\)[\s\S]*upt\.generation = t\.generation \|\| 0;/, up2k,
    'upload executor skips terminal/removed tasks and captures a generation');
must(/if \(t\.hash && t\.hash\.length\)[\s\S]*push_t\(st\.todo\.handshake, t\)/,
    up2k, 'retry preserves hashes and re-handshakes for server missing chunks');
must(/if \(t\.done\)\n\s*t\.fobj = null;/, up2k,
    '404 terminal path keeps fobj available for Retry; only success releases it');
must(/row\.in == 'ng' && st\.files\[nfile\]\.terminal/, up2k,
    'Retry/Remove controls appear only on terminal failed/cancelled rows');
must(/"u_retry": "Retry"/, browser, 'English Retry string is present');
must(/"u_remove": "Remove"/, browser, 'English Remove string is present');

console.log('upload-ui static contract tests: ok');
