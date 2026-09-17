(() => {
  'use strict';
  const slides = [...document.querySelectorAll('.slide')];
  const previous = document.querySelector('#previous');
  const next = document.querySelector('#next');
  const toggle = document.querySelector('#notes-toggle');
  const panel = document.querySelector('#notes-panel');
  let current = 0;
  let showNotes = false;
  const fromHash = () => {
    const match = /^#slide-(\d+)$/.exec(location.hash);
    return match ? Math.max(0, Math.min(slides.length - 1, Number(match[1]) - 1)) : 0;
  };
  function render(index, updateHash = true) {
    current = Math.max(0, Math.min(slides.length - 1, index));
    slides.forEach((slide, i) => {
      slide.classList.toggle('active', i === current);
      slide.setAttribute('aria-hidden', String(i !== current));
      slide.inert = i !== current;
    });
    document.querySelector('#position').textContent = `${current + 1} / ${slides.length}`;
    document.querySelector('#announcement').textContent = slides[current].querySelector('h1, h2').textContent;
    previous.disabled = current === 0;
    next.disabled = current === slides.length - 1;
    panel.innerHTML = slides[current].querySelector('.speaker-notes')?.innerHTML || '';
    panel.hidden = !showNotes;
    if (updateHash) history.replaceState(null, '', `#slide-${current + 1}`);
  }
  function resize() {
    const scale = Math.min(innerWidth / 1280, Math.max(1, innerHeight - 64) / 720);
    document.documentElement.style.setProperty('--scale', String(scale));
  }
  function toggleNotes() {
    showNotes = !showNotes;
    toggle.setAttribute('aria-pressed', String(showNotes));
    panel.hidden = !showNotes;
  }
  const fullscreen = document.querySelector('#fullscreen');
  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      document.querySelector('#announcement').textContent = 'Full screen is unavailable. Use your browser’s full-screen command.';
    }
  }
  previous.addEventListener('click', () => render(current - 1));
  next.addEventListener('click', () => render(current + 1));
  toggle.addEventListener('click', toggleNotes);
  fullscreen.addEventListener('click', toggleFullscreen);
  fullscreen.hidden = !document.fullscreenEnabled;
  document.addEventListener('fullscreenchange', () => {
    fullscreen.textContent = document.fullscreenElement ? 'Exit full screen' : 'Full screen';
    resize();
  });
  document.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || /^(INPUT|TEXTAREA|SELECT|BUTTON|A)$/.test(event.target.tagName) || event.target.isContentEditable) return;
    const key = event.key.toLowerCase();
    if (['arrowright', 'arrowdown', 'pagedown', ' ', 'arrowleft', 'arrowup', 'pageup', 'home', 'end', 'n', 'f', 'escape'].includes(key)) event.preventDefault();
    if (['arrowright', 'arrowdown', 'pagedown', ' '].includes(key)) render(current + 1);
    else if (['arrowleft', 'arrowup', 'pageup'].includes(key)) render(current - 1);
    else if (key === 'home') render(0);
    else if (key === 'end') render(slides.length - 1);
    else if (key === 'n') toggleNotes();
    else if (key === 'f') toggleFullscreen();
    else if (key === 'escape' && showNotes) toggleNotes();
  });
  window.addEventListener('hashchange', () => render(fromHash(), false));
  window.addEventListener('resize', resize);
  document.body.classList.add('presenting');
  document.querySelector('.controls').hidden = false;
  resize();
  render(fromHash(), false);
})();
