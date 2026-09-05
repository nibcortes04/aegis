document.addEventListener('DOMContentLoaded', () => {
  // 1. Copy to clipboard functionality with fluid feedback
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
        copyBtn.style.boxShadow = '0 0 14px rgba(52, 211, 153, 0.4)';

        setTimeout(() => {
          copyFeedback.innerText = originalText;
          copyFeedback.style.color = '';
          copyBtn.style.borderColor = '';
          copyBtn.style.boxShadow = '';
        }, 2200);
      } catch (err) {
        console.error('Failed to copy text', err);
      }
    });
  }

  // 2. Interactive Terminal Tab Switching
  const tabButtons = document.querySelectorAll('.terminal-tab-selector .tab-btn');
  const terminalPanes = document.querySelectorAll('.terminal-body .terminal-pane');
  const termTitle = document.getElementById('term-title');
  const termBadge = document.getElementById('term-badge');

  const tabMetadata = {
    statusline: {
      title: 'bash — konsole · session-87c8834d (🔔 Tab Bell Active)',
      badge: 'Live Telemetry'
    },
    automode: {
      title: 'agy — auto mode classifier · workspace-safe profile',
      badge: 'Sub-10ms Gate'
    },
    safety: {
      title: 'aegis — two-factor confirmation ledger (TTL: 120s)',
      badge: 'Fail-Closed'
    },
    notifications: {
      title: 'aegis — multi-session notification telemetry',
      badge: 'Isolated Debounce'
    }
  };

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');

      // Update button states
      tabButtons.forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');

      // Update terminal pane
      terminalPanes.forEach(pane => pane.classList.remove('active'));
      const activePane = document.getElementById(`pane-${targetTab}`);
      if (activePane) {
        activePane.classList.add('active');
      }

      // Update terminal title & badge
      if (tabMetadata[targetTab]) {
        if (termTitle) termTitle.textContent = tabMetadata[targetTab].title;
        if (termBadge) termBadge.textContent = tabMetadata[targetTab].badge;
      }
    });
  });

  // 3. GitHub Star Count Fetcher (Graceful API query)
  const starBadge = document.getElementById('star-count');
  if (starBadge) {
    fetch('https://api.github.com/repos/nibcortes04/aegis')
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data && typeof data.stargazers_count === 'number') {
          starBadge.textContent = `★ ${data.stargazers_count}`;
        }
      })
      .catch(() => {
        // Fallback default remains ★ Star
      });
  }

  // 4. Ambient card glow tracking
  const cards = document.querySelectorAll('.feature-card, .install-card, .step-card');
  cards.forEach(card => {
    card.addEventListener('pointermove', e => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });

  // 5. Smooth scrolling for navigation links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (!targetId || targetId === '#') return;
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
