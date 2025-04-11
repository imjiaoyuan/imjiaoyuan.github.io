document.addEventListener('DOMContentLoaded', function() {
  const titleElement = document.getElementById('comment-issue-title');
  if (!titleElement) return;

  const owner = 'imjiaoyuan';
  const repo = 'imjiaoyuan.github.io';
  const issueTitle = titleElement.dataset.title;
  const btn = document.querySelector('.comment-link');
  const loadingEl = document.getElementById('comment-loading');
  const textEl = document.getElementById('comment-text');

  if (!btn || !loadingEl || !textEl) return;

  async function checkIssue() {
    try {
      loadingEl.style.display = 'inline-block';
      const response = await fetch(`https://api.github.com/search/issues?q=repo:${owner}/${repo}+"${issueTitle}"+in:title`);
      const data = await response.json();

      if (data.items && data.items.length > 0) {
        btn.href = data.items[0].html_url;
        textEl.textContent = 'View or Add Comments';
      } else {
        btn.href = `https://github.com/${owner}/${repo}/issues/new?title=${encodeURIComponent(issueTitle)}`;
        textEl.textContent = 'Create New Comment';
      }
    } catch (error) {
      console.error('Error checking issue:', error);
      textEl.textContent = 'View or Add Comments (API call failed)';
    } finally {
      loadingEl.style.display = 'none';
    }
  }

  checkIssue();
});