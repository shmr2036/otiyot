// Meta Pixel (ID 1649137836854163). Kept in a file rather than inline so the page CSP
// can stay script-src 'self' + connect.facebook.net.
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '1649137836854163');
fbq('track', 'PageView');

// Conversion signals: payment is completed on Invoice4U, outside this page, so the
// closest measurable step is the click that leaves for checkout.
document.addEventListener('click', (e) => {
  const link = e.target.closest && e.target.closest('a[href]');
  if (!link) return;
  if (link.href.includes('invoice4u.co.il')) fbq('track', 'InitiateCheckout');
  else if (link.href.startsWith('https://wa.me/')) fbq('track', 'Contact');
});
