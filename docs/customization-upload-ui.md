# Upload UI customization: terminal Retry / Remove

This customization changes only the browser-side uploader (`copyparty/web/up2k.js`)
and the built-in English strings in `copyparty/web/browser.js`. It does not change
Copyparty Python code, server behavior, authentication, or deployment settings.

## Behavior

* A task that reaches a terminal failed/cancelled state in the Failed card shows
  **Retry** and **Remove**.
* **Retry** is only accepted for a terminal task. If it already has hashes, it
  reuses them and queues a handshake; the server's missing-hash response decides
  which chunks remain, so chunks already accepted by the server are not submitted
  again. An unhashed task is queued for hashing instead. This is separate from,
  and does not alter, the uploader's normal automatic retry paths or the
  low-level `unqueue_up()` helper.
* **Remove** is only accepted for a terminal task. It aborts XHRs tracked for
  that task (and an attached `AbortController`, when present), clears only that
  task's `todo`/`busy` head/hash/handshake/upload records plus `postlist` and a
  task retry timer, adjusts byte/card counters, and removes its row. It never
  cancels another task's requests or queue entries.
* Terminal failures, including a 404 search result, retain the browser `File`
  object so **Retry** remains possible. The object is released only after a
  successful completion or an explicit **Remove**.
* Each attempt has a generation token. FileReader, digest, hashing-worker and
  network callbacks verify that token and terminal/removal state before they
  mutate counters or enqueue follow-up work. A late callback after failure or
  removal is ignored; `mark_terminal()` is idempotent and is the sole
  terminal-failure increment of `bytes.finished`.
* The only new source strings are English `u_retry`, `u_remove`, and
  `u_cancelled`. Copyparty's existing `langtest2()` fills missing language keys
  from the loaded English resource, so other translations fall back to English
  until translators add native equivalents.

## Manual browser regression check

1. Start a disposable Copyparty instance with write access and open its upload
   UI. Do not use production uploads for this check.
2. Force one upload into a terminal failure (for example, choose a target that
   rejects the upload); confirm the Failed card exposes **Retry** and **Remove**.
3. Click **Retry**. Verify the row returns to the queue and completes after the
   cause is fixed. In DevTools Network, confirm that after handshake it uploads
   only hashes reported as missing (or performs hashing first for a pre-hash
   failure).
4. Create two independent failed uploads. Remove one and verify the other
   remains in the Failed card and can still be retried. Confirm its network
   request is not aborted.
5. With an upload request visible in DevTools, cause it to become terminal,
   click **Remove**, and verify the request is aborted, the row disappears, and
   busy/queued counters and completion notification do not include it.
6. Repeat steps 2--5 with a non-English UI. The action labels should fall back
   to English unless that translation supplies the new keys.

## Limits

The browser cannot prove whether a server received an in-flight chunk before a
network abort. Retry therefore always performs the normal up2k handshake and
uses the server as the authority for missing chunks. Hashing workers/FileReader
operations are not cancellable through this UI; the generation guard prevents
their late results from mutating state or scheduling network follow-up after a
terminal transition or Remove.

## Verification

```sh
node --check copyparty/web/browser.js
node --check copyparty/web/up2k.js
node tests/test_upload_ui.js
python3 -m unittest tests.test_custom_tools -v
git diff --check
```
