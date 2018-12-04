'use strict';

async function fetchCode(e, lang, src) {
    const resp = await fetch(src);
    let t = await resp.text();
    if (lang) t = hljs.highlight(lang, t).value;
    e.innerHTML = t;
}

function fetchAndHighlightAll() {
    const el = document.getElementsByTagName('code');
    for (const e of el) {
    	const src = e.getAttribute('src');
    	if (!src) continue;
    	const lang = e.getAttribute('lang');
    	const title = document.createElement('b');
    	title.innerText = src;
    	title.style.textAlign = 'center';
    	title.style.display = 'block';
    	e.parentElement.insertBefore(title, e);
    	fetchCode(e, lang, src);
    }
}

setTimeout(fetchAndHighlightAll, 0);
