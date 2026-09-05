document.addEventListener('DOMContentLoaded', () => {
  // Copy to clipboard functionality
  const copyBtn = document.getElementById('copy-btn');
  const copyFeedback = document.getElementById('copy-feedback');
  const installCmd = document.getElementById('install-cmd');

  if (copyBtn && installCmd) {
    copyBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(installCmd.innerText);
        const originalText = copyFeedback.innerText;
        copyFeedback.innerText = 'Copied!';
        copyFeedback.style.color = '#34d399';
        copyBtn.style.borderColor = '#34d399';

        setTimeout(() => {
          copyFeedback.innerText = originalText;
          copyFeedback.style.color = '';
          copyBtn.style.borderColor = '';
        }, 2000);
      } catch (err) {
        console.error('Failed to copy to clipboard', err);
      }
    });
  }

  // Smooth scrolling for navigation links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        e.preventDefault();
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
});
