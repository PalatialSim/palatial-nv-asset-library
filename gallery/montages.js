/* Full-size contact sheets, using the same batch inventory as the cards. */
(() => {
  const dialog = document.getElementById('montageDialog');
  const batchFilter = document.getElementById('batch');
  const batches = [...new Set(assets.map(asset => asset.batch))]
    .sort((a, b) => a.localeCompare(b, undefined, {numeric: true}));
  const viewport = document.getElementById('sheetViewport');
  const image = document.getElementById('sheetImage');
  const status = document.getElementById('sheetStatus');
  let selected = 0;
  let kind = 'render';
  let request = 0;

  function showSheet() {
    const version = ++request;
    const batch = batches[selected];
    const label = batch.replace('batch', 'Batch ');
    const count = assets.filter(asset => asset.batch === batch).length;
    document.getElementById('montageTitle').textContent = label;
    document.getElementById('montageCount').textContent = `${count} assets`;
    document.getElementById('prevMontage').disabled = selected === 0;
    document.getElementById('nextMontage').disabled = selected === batches.length - 1;
    const base = batch === 'batch1' && dialog.dataset.localBatch1 === 'true'
      ? '' : dialog.dataset.montageBase || '';
    const url = new URL(`${base}montages/${batch}-${kind}.jpg`, location.href).href;
    document.getElementById('fullMontage').href = url;
    image.hidden = true;
    status.hidden = false;
    status.textContent = 'Loading montage…';
    viewport.scrollTop = 0;
    const preload = new Image();
    preload.onload = () => {
      if (version !== request || !dialog.open) return;
      image.alt = `${label} — ${kind === 'render' ? 'rendered assets' : 'collision shapes'}`;
      image.src = url;
      image.hidden = false;
      status.hidden = true;
    };
    preload.onerror = () => {
      if (version !== request || !dialog.open) return;
      status.textContent = 'This sheet could not be loaded. You can still view these assets below.';
    };
    preload.src = url;
  }

  document.getElementById('openMontage').addEventListener('click', () => {
    selected = Math.max(0, batches.indexOf(batchFilter.value));
    kind = collision ? 'colliders' : 'render';
    for (const button of dialog.querySelectorAll('[data-montage-kind]')) {
      button.setAttribute('aria-pressed', String(button.dataset.montageKind === kind));
    }
    dialog.showModal();
    showSheet();
  });
  document.getElementById('closeMontage').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { request++; });
  document.getElementById('prevMontage').addEventListener('click', () => { selected--; showSheet(); });
  document.getElementById('nextMontage').addEventListener('click', () => { selected++; showSheet(); });
  for (const button of dialog.querySelectorAll('[data-montage-kind]')) {
    button.addEventListener('click', () => {
      kind = button.dataset.montageKind;
      for (const other of dialog.querySelectorAll('[data-montage-kind]')) {
        other.setAttribute('aria-pressed', String(other === button));
      }
      showSheet();
    });
  }
  document.getElementById('fitMontage').addEventListener('click', event => {
    const fit = viewport.classList.toggle('fit');
    event.currentTarget.setAttribute('aria-pressed', String(fit));
    event.currentTarget.textContent = fit ? 'Fit width' : 'Fit sheet';
  });
  document.getElementById('montageAssets').addEventListener('click', () => {
    batchFilter.value = batches[selected];
    document.getElementById('search').value = '';
    document.getElementById('articulation').value = '';
    batchFilter.dispatchEvent(new Event('change'));
    dialog.close();
  });
})();
