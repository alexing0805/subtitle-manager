export function buildScanConfirmHtml({ title, description, steps = [] }) {
  const stepItems = steps
    .map(step => `<div class="status-item"><span class="dot"></span>${step}</div>`)
    .join('')

  return `<div class="scan-confirm-content">
    <div class="scan-icon-pulse">
      <svg viewBox="0 0 24 24" width="60" height="60" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9"></circle>
        <path d="M12 3v4"></path>
        <path d="M21 12h-4"></path>
        <path d="M12 21v-4"></path>
        <path d="M3 12h4"></path>
        <path d="m18.4 5.6-2.8 2.8"></path>
        <path d="m18.4 18.4-2.8-2.8"></path>
        <path d="m5.6 18.4 2.8-2.8"></path>
        <path d="m5.6 5.6 2.8 2.8"></path>
      </svg>
    </div>
    <h3>${title}</h3>
    <p>${description}</p>
    <div class="scan-status-list">${stepItems}</div>
  </div>`
}

export function createScanDialogOptions(loadingText = '扫描中...') {
  return {
    confirmButtonText: '开始扫描',
    cancelButtonText: '取消',
    dangerouslyUseHTMLString: true,
    confirmButtonClass: 'infuse-btn-scan-main',
    cancelButtonClass: 'infuse-btn-cancel-main',
    showClose: false,
    center: true,
    customClass: 'infuse-message-box scan-modal',
    beforeClose: (action, instance, done) => {
      if (action === 'confirm') {
        instance.confirmButtonLoading = true
        instance.confirmButtonText = loadingText
        instance.showCancelButton = false
        window.setTimeout(done, 700)
        return
      }
      done()
    }
  }
}
