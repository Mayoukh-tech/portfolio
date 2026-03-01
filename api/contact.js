/**
 * /api/contact.js
 * Serverless contact form handler — works on Vercel & Netlify.
 *
 * Environment variables needed (set in platform dashboard):
 *   BREVO_API_KEY   → your Brevo API key (Settings → API Keys)
 *   BREVO_FROM      → verified sender email in Brevo (e.g. hello@yourdomain.com)
 *
 * The TO address is hardcoded below — change it to your email.
 */

const TO_EMAIL = 'mayoukhmodak.01@gmail.com';
const TO_NAME  = 'Mayoukh Modak';

export default async function handler(req, res) {

  // ── Only accept POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // ── Parse body (Vercel auto-parses JSON; Netlify needs manual parse)
  let body = req.body;
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch { body = {}; }
  }

  const { name, email, message } = body || {};

  // ── Basic validation
  if (!name || !email || !message) {
    return res.status(400).json({ error: 'All fields are required.' });
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ error: 'Invalid email address.' });
  }
  if (message.length > 5000) {
    return res.status(400).json({ error: 'Message too long.' });
  }

  // ── Read secrets from environment — never exposed to browser
  const apiKey   = process.env.BREVO_API_KEY;
  const fromEmail = process.env.BREVO_FROM;

  if (!apiKey || !fromEmail) {
    console.error('Missing env vars: BREVO_API_KEY or BREVO_FROM');
    return res.status(500).json({ error: 'Server misconfiguration.' });
  }

  // ── Build Brevo payload
  const payload = {
    sender:      { name: 'Portfolio Contact Form', email: fromEmail },
    to:          [{ email: TO_EMAIL, name: TO_NAME }],
    replyTo:     { email, name },
    subject:     `[Portfolio] New message from ${name}`,
    htmlContent: `
      <div style="font-family:monospace;background:#0b0c0e;color:#e8e6de;
                  padding:2rem;border-left:3px solid #f5a623;max-width:600px">
        <p style="color:#f5a623;font-size:11px;letter-spacing:3px;
                  margin:0 0 1.5rem;text-transform:uppercase">
          Portfolio Contact Form
        </p>
        <table style="width:100%;border-collapse:collapse;margin-bottom:1.5rem">
          <tr>
            <td style="color:#6a6660;font-size:11px;padding:.5rem 0;
                       width:70px;vertical-align:top">FROM</td>
            <td style="color:#e8e6de;font-size:13px">${escHtml(name)}</td>
          </tr>
          <tr>
            <td style="color:#6a6660;font-size:11px;padding:.5rem 0;
                       vertical-align:top">REPLY TO</td>
            <td>
              <a href="mailto:${escHtml(email)}"
                 style="color:#f5a623;text-decoration:none;font-size:13px">
                ${escHtml(email)}
              </a>
            </td>
          </tr>
        </table>
        <hr style="border:none;border-top:1px solid #2a2d35;margin:0 0 1.5rem"/>
        <p style="color:#6a6660;font-size:11px;letter-spacing:2px;
                  margin:0 0 .6rem;text-transform:uppercase">Message</p>
        <p style="color:#e8e6de;font-size:13px;line-height:1.9;
                  white-space:pre-wrap;margin:0">${escHtml(message)}</p>
      </div>
    `,
  };

  // ── Call Brevo
  try {
    const brevoRes = await fetch('https://api.brevo.com/v3/smtp/email', {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        'api-key':       apiKey,
      },
      body: JSON.stringify(payload),
    });

    if (!brevoRes.ok) {
      const errBody = await brevoRes.json().catch(() => ({}));
      console.error('Brevo error:', errBody);
      return res.status(502).json({
        error: errBody.message || `Brevo returned ${brevoRes.status}`,
      });
    }

    return res.status(200).json({ ok: true });

  } catch (err) {
    console.error('Fetch to Brevo failed:', err);
    return res.status(500).json({ error: 'Failed to reach mail service.' });
  }
}

/** Escape HTML special chars to prevent injection in email body */
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
