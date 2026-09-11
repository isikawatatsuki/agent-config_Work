'use strict';

const byId = id => document.getElementById(id);
const state = { token: '', data: null, query: '', folder: '', scope: 'all', kind: '', tag: '', sort: 'modified', layout: 'list', index: false, selected: null, request: 0, dialog: null };
const icons = () => window.lucide?.createIcons({ attrs: { 'aria-hidden': 'true' } });
function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}
function icon(name) {
  const element = node('i');
  element.dataset.lucide = name;
  return element;
}
function iconButton(name, label, callback) {
  const button = node('button', 'icon-button');
  button.title = label;
  button.setAttribute('aria-label', label);
  button.append(icon(name));
  button.onclick = callback;
  return button;
}
function parentOf(path) { return path.includes('/') ? path.slice(0, path.lastIndexOf('/')) : ''; }
function filename(path) { return path.split('/').at(-1); }
function size(bytes) { return bytes < 1024 ? `${bytes} B` : bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`; }
const date = (value, full = false) => new Intl.DateTimeFormat('ja-JP', full ? { dateStyle: 'medium', timeStyle: 'short' } : { month: '2-digit', day: '2-digit' }).format(new Date(value));
let toastTimer;
function toast(message) {
  byId('toast').textContent = message;
  byId('toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { byId('toast').hidden = true; }, 3500);
}
async function api(path, data) {
  const options = data ? { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Artifact-Token': state.token }, body: JSON.stringify(data) } : {};
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'リクエストに失敗しました。');
  return result;
}
async function load() {
  const request = ++state.request;
  byId('document-list').setAttribute('aria-busy', 'true');
  byId('error-banner').hidden = true;
  const params = new URLSearchParams({ q: state.query, folder: state.folder, scope: state.scope, kind: state.kind, tag: state.tag, sort: state.index ? 'title' : state.sort });
  try {
    const result = await api(`/api/library?${params}`);
    if (request !== state.request) return;
    state.data = result;
    renderNavigation();
    renderList();
    const selected = result.items.find(item => item.id === state.selected?.id);
    if (selected) {
      state.selected = selected;
    } else {
      state.selected = null;
    }
    updateSelection();
  } catch (error) {
    if (request !== state.request) return;
    byId('error-banner').textContent = error.message;
    byId('error-banner').hidden = false;
    byId('result-count').textContent = '読み込みに失敗しました';
  } finally {
    if (request === state.request) byId('document-list').setAttribute('aria-busy', 'false');
  }
}
function navigate(folder = '', scope = 'folder', index = false) {
  state.folder = folder;
  state.scope = scope;
  state.index = index;
  document.body.classList.remove('menu-open', 'preview-open');
  load();
}
function renderNavigation() {
  byId('total-count').textContent = state.data.stats.total;
  byId('view-title').textContent = state.query ? '検索結果' : state.index ? 'タイトル索引' : state.scope === 'all' ? 'すべての資料' : filename(state.folder) || '成果物';
  byId('eyebrow').textContent = state.query ? 'SEARCH' : state.index ? 'INDEX' : state.scope === 'all' ? 'LIBRARY' : 'FOLDER';
  document.querySelectorAll('[data-nav]').forEach(button => {
    button.classList.toggle('active', button.dataset.nav === 'index' ? state.index : state.scope === 'all' && !state.index);
  });
  const tree = byId('folder-tree');
  tree.replaceChildren();
  for (const path of state.data.folders) {
    const row = node('div', 'folder-row');
    row.classList.toggle('active', state.scope === 'folder' && state.folder === path);
    const button = node('button', 'folder-button');
    button.append(icon(path === state.folder && state.scope === 'folder' ? 'folder-open' : 'folder'), node('span', '', path ? filename(path) : '成果物'));
    button.title = path || '.agents/artifacts';
    button.style.paddingLeft = `${10 + (path ? path.split('/').length : 0) * 10}px`;
    button.onclick = () => navigate(path);
    row.append(button);
    if (path) row.append(iconButton('ellipsis', `${filename(path)}を整理`, () => moveDialog(path, true)));
    tree.append(row);
  }
  const tags = byId('tag-list');
  tags.replaceChildren();
  if (!state.data.tags.length) tags.append(node('p', 'tag-empty', 'タグなし'));
  for (const label of state.data.tags) {
    const button = node('button', 'tag-button');
    button.classList.toggle('active', state.tag === label);
    button.append(icon('tag'), node('span', '', label));
    button.onclick = () => { state.tag = state.tag === label ? '' : label; load(); };
    tags.append(button);
  }
  const breadcrumbs = byId('breadcrumbs');
  breadcrumbs.replaceChildren();
  const root = node('button', '', '成果物');
  root.onclick = () => navigate('');
  breadcrumbs.append(icon('hard-drive'), root);
  if (state.scope === 'all') breadcrumbs.append(icon('chevron-right'), node('span', '', state.index ? 'タイトル索引' : 'すべての資料'));
  else {
    const parts = state.folder.split('/').filter(Boolean);
    parts.forEach((part, index) => {
      const button = node('button', '', part);
      button.onclick = () => navigate(parts.slice(0, index + 1).join('/'));
      breadcrumbs.append(icon('chevron-right'), button);
    });
  }
  byId('index-status').textContent = `${state.data.stats.total}件の索引${state.data.stats.errors ? ` / 本文未取得 ${state.data.stats.errors}件` : ''}`;
  byId('reset-filters').hidden = !state.query && !state.kind && !state.tag;
  byId('sort').disabled = state.index;
  byId('delete-folder').hidden = state.scope !== 'folder' || !state.folder;
  icons();
}
function renderList() {
  const list = byId('document-list');
  list.replaceChildren();
  list.className = `document-list${state.layout === 'grid' && !state.index ? ' grid' : ''}`;
  const children = state.scope === 'folder' && !state.query && !state.kind && !state.tag ? state.data.folders.filter(path => path && parentOf(path) === state.folder) : [];
  byId('result-count').textContent = `${state.data.items.length}件の資料${children.length ? ` / ${children.length}フォルダー` : ''}${state.tag ? ` · ${state.tag}` : ''}`;
  for (const path of children) {
    const button = node('button', 'folder-list-row');
    const arrow = icon('chevron-right');
    arrow.className = 'arrow';
    button.append(icon('folder'), node('span', '', filename(path)), arrow);
    button.onclick = () => navigate(path);
    list.append(button);
  }
  if (!state.data.items.length && !children.length) {
    const empty = node('div', 'empty-state');
    empty.append(icon(state.query || state.tag || state.kind ? 'search-x' : 'folder-open'), node('h2', '', state.query || state.tag || state.kind ? '該当する資料がありません' : 'このフォルダーに資料はありません'));
    if (state.query) empty.append(node('p', '', `「${state.query}」`));
    list.append(empty);
  }
  let lastLetter;
  for (const item of state.data.items) {
    if (state.index) {
      const letter = [...item.title.trim()][0]?.toLocaleUpperCase('ja-JP') || '#';
      if (letter !== lastLetter) list.append(node('h2', 'index-letter', letter));
      lastLetter = letter;
    }
    const row = node('button', 'document-row');
    row.dataset.id = item.id;
    row.classList.toggle('selected', state.selected?.id === item.id);
    row.setAttribute('aria-pressed', String(state.selected?.id === item.id));
    row.title = item.path;
    const fileIcon = node('span', `file-icon ${item.kind}`);
    fileIcon.append(icon(item.kind === 'html' ? 'file-code-2' : 'file-text'));
    const text = node('span', 'file-text');
    text.append(node('span', 'file-title', item.title), node('span', 'file-path', item.path));
    if (state.query && item.excerpt) text.append(node('span', 'file-excerpt', item.excerpt));
    if (item.tags.length) {
      const tags = node('span', 'row-tags');
      item.tags.slice(0, 3).forEach(tag => tags.append(node('span', '', tag)));
      text.append(tags);
    }
    const meta = node('span', 'file-meta');
    meta.append(node('span', `type-mini ${item.kind}`, item.kind.toUpperCase()), node('span', '', date(item.modified, true)), node('span', '', size(item.size)));
    row.append(fileIcon, text, meta);
    row.onclick = () => selectDocument(item);
    row.ondblclick = () => openDocument(item);
    row.onkeydown = event => {
      if (event.key === 'Enter') { event.preventDefault(); openDocument(item); }
    };
    list.append(row);
  }
  icons();
}
function selectDocument(item) {
  state.selected = item;
  document.querySelectorAll('.document-row').forEach(row => {
    const selected = Number(row.dataset.id) === item.id;
    row.classList.toggle('selected', selected);
    row.setAttribute('aria-pressed', String(selected));
  });
  updateSelection();
}
function updateSelection() {
  for (const id of ['open-document', 'edit-metadata', 'move-document', 'delete-document']) byId(id).disabled = !state.selected;
  byId('selection-status').textContent = state.selected ? `${filename(state.selected.path)} を選択` : '選択なし';
}
function openDocument(item = state.selected) {
  if (!item) return;
  sessionStorage.setItem('artifact-explorer-list', JSON.stringify({ query: state.query, folder: state.folder, scope: state.scope, kind: state.kind, tag: state.tag, sort: state.sort, layout: state.layout, index: state.index, selectedId: item.id, scroll: byId('document-list').scrollTop }));
  location.href = `/viewer.html?id=${encodeURIComponent(item.id)}`;
}
function field(label, name, value = '', type = 'input') {
  const group = node('div', 'field');
  const labelElement = node('label', '', label);
  labelElement.htmlFor = `field-${name}`;
  const input = node(type);
  input.name = name;
  input.id = `field-${name}`;
  if (type !== 'select') input.value = value;
  group.append(labelElement, input);
  byId('dialog-fields').append(group);
  return input;
}
function folderSelect(name, value = '', exclude = null) {
  const select = field('保存先フォルダー', name, '', 'select');
  state.data.folders.filter(path => exclude === null || (path !== exclude && !path.startsWith(`${exclude}/`))).forEach(path => {
    const option = node('option', '', path || '成果物（ルート）');
    option.value = path;
    select.append(option);
  });
  select.value = value;
  return select;
}
function openDialog(title, callback, action = '保存', success = '保存しました') {
  byId('dialog-title').textContent = title;
  byId('dialog-fields').replaceChildren();
  byId('dialog-error').textContent = '';
  byId('dialog-save').disabled = false;
  byId('dialog-save').querySelector('span').textContent = action;
  byId('dialog-save').classList.toggle('danger', action === '削除');
  state.dialogSuccess = success;
  state.dialog = callback;
}
function showDialog() { byId('editor-dialog').showModal(); icons(); }
function metadataDialog() {
  const item = state.selected;
  if (!item) return;
  openDialog('資料の属性を編集', async data => {
    await api('/api/metadata', { id: item.id, title: data.get('title'), summary: data.get('summary'), tags: data.get('tags').split(/[,、\n]/).map(tag => tag.trim()).filter(Boolean) });
  });
  const title = field('タイトル', 'title', item.title);
  title.required = true;
  title.maxLength = 200;
  field('概要', 'summary', item.summary, 'textarea').maxLength = 2000;
  field('タグ（カンマ区切り）', 'tags', item.tags.join(', '));
  showDialog();
}
function newFolderDialog() {
  openDialog('フォルダーを作成', async data => {
    await api('/api/folder', { parent: data.get('parent'), name: data.get('name') });
  });
  folderSelect('parent', state.folder);
  const name = field('フォルダー名', 'name');
  name.required = true;
  name.maxLength = 160;
  showDialog();
}
function moveDialog(source, isFolder = false) {
  openDialog(isFolder ? 'フォルダーを整理' : '移動・名前変更', async data => {
    const destination = [data.get('parent'), data.get('name')].filter(Boolean).join('/');
    await api('/api/move', { source, destination });
    if (isFolder && (state.folder === source || state.folder.startsWith(`${source}/`))) state.folder = destination + state.folder.slice(source.length);
    if (state.selected && (state.selected.path === source || state.selected.path.startsWith(`${source}/`))) state.selected.path = destination + state.selected.path.slice(source.length);
  });
  const name = field(isFolder ? 'フォルダー名' : 'ファイル名', 'name', filename(source));
  name.required = true;
  name.maxLength = 160;
  folderSelect('parent', parentOf(source), isFolder ? source : null);
  byId('dialog-fields').append(node('p', 'dialog-note', isFolder ? 'フォルダー内の画像・CSS・資料も一緒に移動します。ほかのフォルダーからの参照は自動更新されません。' : 'このファイルだけを移動します。関連画像・CSSがあるHTMLはフォルダー単位で整理してください。参照リンクは自動更新されません。'));
  showDialog();
}
function deleteDialog(source, isFolder = false) {
  if (!source) return;
  openDialog(isFolder ? 'フォルダーを削除しますか？' : 'ファイルを削除しますか？', async () => {
    await api('/api/delete', { source });
    if (isFolder && (state.folder === source || state.folder.startsWith(`${source}/`))) state.folder = parentOf(source);
    state.selected = null;
  }, '削除', 'ごみ箱に移動しました');
  byId('dialog-fields').append(
    node('p', 'delete-target', source),
    node('p', 'dialog-note', isFolder ? 'フォルダー内の資料・画像・CSSもすべてごみ箱へ移動します。他の資料からの参照リンクは更新されません。' : 'このファイルだけをごみ箱へ移動します。関連画像・CSSは残ります。他の資料からの参照リンクは更新されません。'),
    node('p', 'dialog-note', 'ごみ箱から元の場所に復元できます。')
  );
  showDialog();
  byId('dialog-cancel').focus();
}
async function refreshTrash() {
  const { items } = await api('/api/trash');
  const list = byId('trash-list');
  list.replaceChildren();
  if (!items.length) list.append(node('p', 'dialog-note', 'ごみ箱は空です。'));
  for (const item of items) {
    const row = node('div', 'trash-row');
    const text = node('div', 'trash-text');
    text.append(node('strong', '', item.path), node('small', '', `${item.folder ? 'フォルダー' : 'ファイル'} · ${date(item.deleted, true)}`));
    const restore = iconButton('undo-2', `${item.path}を復元`, async () => {
      byId('trash-error').textContent = '';
      byId('trash-close').disabled = true;
      list.querySelectorAll('button').forEach(button => { button.disabled = true; });
      try {
        await api('/api/restore', { id: item.id });
        await load();
        await refreshTrash();
        toast('元の場所に復元しました');
      } catch (error) { byId('trash-error').textContent = error.message; }
      finally {
        byId('trash-close').disabled = false;
        list.querySelectorAll('button').forEach(button => { button.disabled = false; });
        byId('trash-close').focus();
      }
    });
    row.append(icon(item.folder ? 'folder' : 'file'), text, restore);
    list.append(row);
  }
  icons();
}
async function openTrash() {
  document.body.classList.remove('menu-open');
  byId('trash-error').textContent = '';
  byId('trash-list').replaceChildren(node('p', 'dialog-note', '読み込み中'));
  byId('trash-dialog').showModal();
  try { await refreshTrash(); }
  catch (error) { byId('trash-error').textContent = error.message; }
}
async function scan() {
  byId('scan').disabled = true;
  byId('scan').classList.add('spin');
  byId('index-status').textContent = '索引を更新中';
  try {
    await api('/api/scan', {});
    let result;
    do {
      await new Promise(resolve => setTimeout(resolve, 450));
      result = await api('/api/status');
    } while (result.running);
    if (result.error) throw new Error(result.error);
    await load();
    toast(`${result.indexed}件の索引を更新しました`);
  } catch (error) { toast(error.message); }
  finally { byId('scan').disabled = false; byId('scan').classList.remove('spin'); }
}
let searchTimer;
byId('search').addEventListener('input', event => {
  state.query = event.target.value;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => load(), 220);
});
document.querySelectorAll('[data-nav]').forEach(button => { button.onclick = () => navigate('', 'all', button.dataset.nav === 'index'); });
document.querySelectorAll('[data-kind]').forEach(button => {
  button.onclick = () => {
    state.kind = button.dataset.kind;
    document.querySelectorAll('[data-kind]').forEach(item => item.classList.toggle('active', item === button));
    load();
  };
});
document.querySelectorAll('[data-layout]').forEach(button => {
  button.onclick = () => {
    state.layout = button.dataset.layout;
    document.querySelectorAll('[data-layout]').forEach(item => item.classList.toggle('active', item === button));
    renderList();
  };
});
byId('sort').onchange = event => { state.sort = event.target.value; load(); };
byId('clear-tag').onclick = () => { state.tag = ''; load(); };
byId('reset-filters').onclick = () => {
  state.query = ''; state.tag = ''; state.kind = '';
  byId('search').value = '';
  document.querySelectorAll('[data-kind]').forEach(button => button.classList.toggle('active', button.dataset.kind === ''));
  load();
};
byId('new-folder').onclick = newFolderDialog;
byId('new-folder-side').onclick = newFolderDialog;
byId('edit-metadata').onclick = metadataDialog;
byId('move-document').onclick = () => state.selected && moveDialog(state.selected.path);
byId('delete-document').onclick = () => state.selected && deleteDialog(state.selected.path);
byId('delete-folder').onclick = () => deleteDialog(state.folder, true);
byId('open-trash').onclick = openTrash;
byId('trash-close').onclick = () => byId('trash-dialog').close();
byId('trash-dialog').oncancel = event => { if (byId('trash-close').disabled) event.preventDefault(); };
byId('editor-dialog').oncancel = event => { if (byId('dialog-save').disabled) event.preventDefault(); };
byId('dialog-close').onclick = byId('dialog-cancel').onclick = () => byId('editor-dialog').close();
byId('editor-form').onsubmit = async event => {
  event.preventDefault();
  if (byId('dialog-save').disabled) return;
  byId('dialog-save').disabled = true;
  byId('dialog-cancel').disabled = byId('dialog-close').disabled = true;
  byId('dialog-error').textContent = '';
  try {
    await state.dialog(new FormData(event.target));
    byId('editor-dialog').close();
    await load();
    toast(state.dialogSuccess);
  } catch (error) { byId('dialog-error').textContent = error.message; }
  finally { byId('dialog-save').disabled = byId('dialog-cancel').disabled = byId('dialog-close').disabled = false; }
};
byId('open-document').onclick = () => openDocument();
byId('menu-toggle').onclick = () => document.body.classList.toggle('menu-open');
byId('scan').onclick = scan;
async function init() {
  icons();
  try {
    state.token = (await api('/api/bootstrap')).token;
    let saved;
    try { saved = JSON.parse(sessionStorage.getItem('artifact-explorer-list')); } catch {}
    if (saved) {
      for (const key of ['query', 'folder', 'scope', 'kind', 'tag', 'sort', 'layout', 'index']) if (Object.hasOwn(saved, key)) state[key] = saved[key];
      byId('search').value = state.query;
      byId('sort').value = state.sort;
      document.querySelectorAll('[data-kind]').forEach(button => button.classList.toggle('active', button.dataset.kind === state.kind));
      document.querySelectorAll('[data-layout]').forEach(button => button.classList.toggle('active', button.dataset.layout === state.layout));
    }
    await load();
    const selected = state.data?.items.find(item => item.id === saved?.selectedId);
    if (selected) selectDocument(selected);
    if (saved) byId('document-list').scrollTop = saved.scroll || 0;
  } catch (error) {
    byId('error-banner').hidden = false;
    byId('error-banner').textContent = error.message;
  }
}
init();