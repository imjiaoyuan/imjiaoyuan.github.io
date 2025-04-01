document.addEventListener('DOMContentLoaded', function() {
  var titleElement = document.getElementById('comment-issue-title');
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
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const data = await response.json();
      
      if (data.items && data.items.length > 0) {
        btn.href = data.items[0].html_url;
        textEl.textContent = '查看或添加评论';
      }
    } catch (error) {
      console.error('Error checking issue:', error);
      textEl.textContent = '查看或添加评论 (API调用失败)';
    } finally {
      loadingEl.style.display = 'none';
    }
  }

  checkIssue();
}); 