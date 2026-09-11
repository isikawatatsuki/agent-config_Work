'use strict';

const byId = id => document.getElementById(id);
let file;
let pageNumber = 0;
let pageCount = 0;
let imageURL;
let requestNumber = 0;

function message(text) {
  const paragraph = document.createElement('p');
  paragraph.className = 'viewer-message';
  paragraph.textContent = text;
  byId('file-stage').replaceChildren(paragraph);
}

async function showPage() {
  const request = ++requestNumber;
  byId('file-stage').setAttribute('aria-busy', 'true');
  byId('previous-page').disabled = true;
  byId('next-page').disabled = true;
  if (imageURL) URL.revokeObjectURL(imageURL);
  message('ページを読み込み中');
  try {
    const response = await fetch(`/api/pdf-page?${new URLSearchParams({ path: file.path, page: pageNumber })}`);
    if (!response.ok) throw new Error('PDFページを表示できません。');
    const blob = await response.blob();
    if (request !== requestNumber) return;
    pageCount = Number(response.headers.get('X-Page-Count'));
    imageURL = URL.createObjectURL(blob);
    const image = document.createElement('img');
    image.alt = `${file.title} ${pageNumber + 1}ページ`;
    image.src = imageURL;
    byId('file-stage').replaceChildren(image);
    byId('file-stage').scrollTop = 0;
    byId('page-label').textContent = `${pageNumber + 1} / ${pageCount}`;
  } catch (error) { message(error.message); }
  finally {
    byId('file-stage').setAttribute('aria-busy', 'false');
    byId('previous-page').disabled = pageNumber === 0;
    byId('next-page').disabled = pageNumber + 1 >= pageCount;
  }
}

async function init() {
  window.lucide?.createIcons({ attrs: { 'aria-hidden': 'true' } });
  try {
    const identity = Number(new URLSearchParams(location.search).get('id'));
    const response = await fetch('/api/library?scope=all');
    if (!response.ok) throw new Error('資料一覧を読み込めません。');
    const library = await response.json();
    file = library.items.find(item => item.id === identity);
    if (!file) throw new Error('資料が見つかりません。一覧へ戻って確認してください。');
    document.title = `${file.title} | Artifact Library`;
    byId('file-title').textContent = file.title;
    byId('file-path').textContent = file.path;
    byId('download').href = `/api/download?${new URLSearchParams({ path: file.path })}`;
    byId('download').hidden = false;
    for (const [label, value] of [['形式', file.kind.toUpperCase()], ['保存場所', file.path], ['概要', file.summary || '未登録'], ['タグ', file.tags.join(', ') || 'なし'], ['更新日時', new Date(file.modified).toLocaleString('ja-JP')], ['本文索引', file.error || '索引化済み']]) {
      const term = document.createElement('dt');
      term.textContent = label;
      const detail = document.createElement('dd');
      detail.textContent = value;
      byId('properties').append(term, detail);
    }
    byId('file-details').disabled = false;
    if (file.kind === 'pdf') {
      byId('pdf-navigation').hidden = false;
      await showPage();
    } else {
      const frame = document.createElement('iframe');
      frame.title = file.title;
      frame.setAttribute('sandbox', 'allow-scripts');
      frame.referrerPolicy = 'no-referrer';
      frame.src = `/content/${file.path.split('/').map(encodeURIComponent).join('/')}`;
      byId('file-stage').replaceChildren(frame);
    }
  } catch (error) {
    byId('file-title').textContent = '読み込めません';
    message(error.message);
  } finally { byId('file-stage').setAttribute('aria-busy', 'false'); }
}
byId('previous-page').onclick = () => { if (pageNumber > 0) { --pageNumber; showPage(); } };
byId('next-page').onclick = () => { if (pageNumber + 1 < pageCount) { ++pageNumber; showPage(); } };
byId('file-details').onclick = () => byId('details-dialog').showModal();
byId('close-details').onclick = () => byId('details-dialog').close();
init();