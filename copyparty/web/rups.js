"use strict";

var J_RUP = 1;

function render() {
    var html = ['<table id="tab"><thead><tr><th>' + I18N.t('size') + '</th><th>' + I18N.t('who') + '</th><th>ip</th><th>' + I18N.t('when') + '</th><th>' + I18N.t('age') + '</th><th>' + I18N.t('directory') + '</th><th>' + I18N.t('file') + '</th></tr></thead><tbody>'];
    var ups = V.ups, now = V.now;
    ebi('filter').value = V.filter;
    ebi('hits').textContent = I18N.tf('showing_files', {n: ups.length});

    for (var a = 0; a < ups.length; a++) {
        var f = ups[a],
            vsp = vsplit(f.vp.split('?')[0]),
            dn = esc(uricom_dec(vsp[0])),
            fn = esc(uricom_dec(vsp[1])),
            at = f.at,
            td = now - f.at,
            ts = !at ? '(?)' : unix2ui(at),
            sa = !at ? '(?)' : td > 60 ? shumantime(td) : (td + 's'),
            sz = ('' + f.sz).replace(/\B(?=(\d{3})+(?!\d))/g, " ");

        html.push('<tr><td>' + sz +
            '</td><td>' + (f.un || '') +
            '</td><td>' + f.ip +
            '</td><td>' + ts +
            '</td><td>' + sa +
            '</td><td><a href="' + vsp[0] + '">' + dn +
            '</a></td><td><a href="' + f.vp + '">' + fn +
            '</a></td></tr>');
    }
    if (!ups.length) {
        var t = V.filter ? I18N.t('matching_filter') : '';
        html = ['<tr><td colspan="7">' + I18N.t('no_uploads') + t + '</td></tr>'];
    }
    html.push('</tbody></table>');
    ebi('tw').innerHTML = html.join('\n');
}
render();

var ti;
function ask(e) {
    ev(e);
    clearTimeout(ti);
    ebi('hits').textContent = I18N.t('loading') + '...';

    var xhr = new XHR(),
        filter = unsmart(ebi('filter').value);

    hist_replace(get_evpath().split('?')[0] + '?ru&filter=' + uricom_enc(filter));

    xhr.onload = xhr.onerror = function () {
        try {
            V = JSON.parse(this.responseText)
        }
        catch (ex) {
            ebi('tw').innerHTML = 'failed to decode server response as json: <pre>' + esc(this.responseText) + '</pre>';
            return;
        }
        render();
    };
    xhr.open('GET', SR + '/?ru&j&filter=' + uricom_enc(filter), true);
    xhr.send();
}
ebi('re').onclick = ask;
ebi('filter').oninput = function () {
    clearTimeout(ti);
    ti = setTimeout(ask, 500);
    ebi('hits').innerHTML = '...';
};
ebi('filter').onkeydown = function (e) {
    if (('' + e.key).endsWith('Enter'))
        ask();
};

J_RUP = 2;
