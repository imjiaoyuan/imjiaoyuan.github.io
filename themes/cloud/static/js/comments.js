document.addEventListener('DOMContentLoaded', function() {
  const commentsWidget = document.querySelector('.comments-widget');
  const titleElement = document.getElementById('comment-issue-title');
  if (!titleElement || !commentsWidget) return;

  const owner = 'imjiaoyuan';
  const repo = 'imjiaoyuan.github.io';
  const issueTitle = titleElement.dataset.title;
  const articleUrl = window.location.href;
  const btn = document.querySelector('.comment-link');
  const loadingEl = document.getElementById('comment-loading');
  const textEl = document.getElementById('comment-text');

  if (!btn || !loadingEl || !textEl) return;

  async function checkIssue() {
    try {
      loadingEl.style.display = 'inline-block';
      const response = await fetch(`https://api.github.com/search/issues?q=repo:${owner}/${repo}+"${encodeURIComponent(issueTitle)}"+in:title`);
      const data = await response.json();

      if (data.items && data.items.length > 0) {
        btn.href = data.items[0].html_url;
        textEl.textContent = 'View or Add issue';
      } else {
        const body = `Article URL: ${articleUrl}\n\n`;
        btn.href = `https://github.com/${owner}/${repo}/issues/new?title=${encodeURIComponent(issueTitle)}&body=${encodeURIComponent(body)}`;
        textEl.textContent = 'Create New Issue';
      }
    } catch (error) {
      console.error('Error checking issue:', error);
      textEl.textContent = 'View or Add issue (API call failed)';
    } finally {
      loadingEl.style.display = 'none';
      commentsWidget.classList.remove('hidden');
    }
  }

  checkIssue();
});