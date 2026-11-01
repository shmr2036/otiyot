// Header background on scroll
const header = document.getElementById('siteHeader');
const onScroll = () => header.classList.toggle('scrolled', window.scrollY > 40);
onScroll();
window.addEventListener('scroll', onScroll, { passive: true });

// Reveal-on-scroll (content is visible by default; see .js .reveal)
const reveals = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  reveals.forEach((el) => io.observe(el));
} else {
  reveals.forEach((el) => el.classList.add('in'));
}

// Testimonials: one quote at a time, 4s each; long quotes get 2-3s more.
// Pauses on hover/focus and via the button; never auto-advances under reduced motion.
const rot = document.querySelector('.rotator');
if (rot) {
  const slides = [...rot.querySelectorAll('.slide')];
  const dotsWrap = rot.querySelector('.dots');
  const pauseBtn = rot.querySelector('.rot-pause');
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let current = 0, paused = reduce, holding = false;

  const dots = slides.map((_, n) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'rot-dot';
    b.setAttribute('aria-label', `המלצה ${n + 1} מתוך ${slides.length}`);
    b.addEventListener('click', () => { show(n); restart(); });
    dotsWrap.appendChild(b);
    return b;
  });

  function show(n) {
    current = (n + slides.length) % slides.length;
    slides.forEach((s, k) => {
      s.classList.toggle('is-active', k === current);
      s.setAttribute('aria-hidden', String(k !== current));
    });
    dots.forEach((d, k) => d.setAttribute('aria-current', String(k === current)));
  }
  const durations = slides.map((s) => {
    const len = s.querySelector('blockquote').textContent.replace(/\s+/g, ' ').trim().length;
    return 4000 + (len > 300 ? 3000 : len > 240 ? 2000 : 0);
  });
  let timer;
  function restart() {
    clearTimeout(timer);
    timer = setTimeout(function step() {
      if (!paused && !holding) show(current + 1);
      timer = setTimeout(step, durations[current]);
    }, durations[current]);
  }
  function setPaused(p) {
    paused = p;
    pauseBtn.setAttribute('aria-pressed', String(p));
    pauseBtn.setAttribute('aria-label', p ? 'הפעלת החלפת ההמלצות' : 'עצירת החלפת ההמלצות');
  }
  pauseBtn.addEventListener('click', () => setPaused(!paused));
  rot.addEventListener('mouseenter', () => { holding = true; });
  rot.addEventListener('mouseleave', () => { holding = false; });
  rot.addEventListener('focusin', () => { holding = true; });
  rot.addEventListener('focusout', () => { holding = false; });

  setPaused(paused);
  show(0);
  restart();
}

// Manifesto: pause/resume the running background text
const manifesto = document.querySelector('.manifesto');
const marqueeBtn = manifesto && manifesto.querySelector('.marquee-toggle');
if (marqueeBtn) {
  marqueeBtn.addEventListener('click', () => {
    const paused = manifesto.classList.toggle('is-paused');
    marqueeBtn.setAttribute('aria-pressed', String(paused));
    marqueeBtn.setAttribute('aria-label', paused ? 'הפעלת הטקסט הנע' : 'עצירת הטקסט הנע');
  });
}

// FAQ — allow only one open at a time (optional, feels tidy)
const items = document.querySelectorAll('.faq-item');
items.forEach((it) => it.addEventListener('toggle', () => {
  if (it.open) items.forEach((o) => { if (o !== it) o.open = false; });
}));
