/**
 * Sentinel Finance OS — Full Application JavaScript
 * Setup wizard + product deal search + dashboard tabs.
 */

const API = '/api/v1';
const SETUP_API = '/api/setup';
const PRODUCT_API = '/api/product';

// ── State ──────────────────────────────────────────────────────────────────
let detectedCards = [];       // Cards returned from Gmail scan
let selectedCards = [];       // Cards checked by user
let allOffers = [];
let currentFilter = 'all';

// ── DOM Helpers ──────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const loading = (show, text = 'Agents working...') => {
    const el = $('loading-overlay');
    if (show) { el.classList.remove('hidden'); $('loading-text').textContent = text; }
    else { el.classList.add('hidden'); }
};
const log = (msg, type = 'info') => {
    const logEl = $('agent-log');
    if (!logEl) return;
    const e = document.createElement('p');
    e.className = `log-entry ${type}`;
    e.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    logEl.prepend(e);
};

// ════════════════════════════════════════════════════════════
// SETUP WIZARD
// ════════════════════════════════════════════════════════════

function wizardStep(num) {
    // Hide all steps
    document.querySelectorAll('.wizard-step').forEach(s => s.classList.add('hidden'));
    document.getElementById(`step-${num}`)?.classList.remove('hidden');

    // Update step indicators
    document.querySelectorAll('.step-dot').forEach((dot, i) => {
        const stepNum = parseInt(dot.dataset.step);
        dot.classList.remove('active', 'done');
        if (stepNum < num) dot.classList.add('done');
        else if (stepNum === num) dot.classList.add('active');
    });
}

async function startGmailScan() {
    const btn = $('btn-scan');
    const statusEl = $('gmail-status');
    btn.disabled = true;
    btn.textContent = '⏳ Scanning...';
    statusEl.innerHTML = `<p style="color:#06b6d4;font-size:14px">🔍 Scanning your Gmail inbox for credit card emails...</p>`;

    try {
        const res = await fetch(`${SETUP_API}/scan_gmail`, { method: 'POST' });
        const data = await res.json();

        detectedCards = data.cards || [];

        const modeText = data.source === 'demo'
            ? '⚠️ Demo mode: check the cards you hold.'
            : `✅ Scanned ${data.emails_scanned} emails. Found ${detectedCards.length} card(s).`;

        statusEl.innerHTML = `<p class="scan-result">${modeText}</p>`;

        // Render checklist in step 3
        $('step3-desc').textContent = data.source === 'demo'
            ? 'Select the credit cards you have:'
            : `We found these cards in your inbox. Check the ones you have:`;

        renderCardChecklist(detectedCards);
        wizardStep(3);
    } catch (e) {
        statusEl.innerHTML = `<p style="color:#ef4444;font-size:13px">Scan failed: ${e.message}</p>`;
        btn.disabled = false;
        btn.textContent = '📧 Scan Gmail for Cards';
    }
}

function skipToManual() {
    // Jump to step 3 with demo cards pre-loaded
    fetch(`${SETUP_API}/scan_gmail`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            detectedCards = data.cards || [];
            renderCardChecklist(detectedCards);
            $('step3-desc').textContent = 'Select the credit cards you have:';
            wizardStep(3);
        });
}

function renderCardChecklist(cards) {
    const container = $('card-checklist');
    container.innerHTML = '';
    cards.forEach((card, idx) => {
        const item = document.createElement('div');
        item.className = 'card-check-item selected'; // default: all selected
        item.dataset.idx = idx;
        item.innerHTML = `
            <div class="card-check-box"></div>
            <div class="card-check-info">
                <div class="card-check-name">${card.name}</div>
                <div class="card-check-meta">${card.bank} · ${card.network} · ${card.card_type} · ${(card.cashback_rate * 100).toFixed(1)}% cashback</div>
            </div>
        `;
        item.addEventListener('click', () => {
            item.classList.toggle('selected');
        });
        container.appendChild(item);
    });
    selectedCards = [...cards]; // all selected by default
}

function addManualCard() {
    const input = $('manual-card-input');
    const name = input.value.trim();
    if (!name) return;

    // Create a basic card entry
    const newCard = {
        name: name,
        bank: name.split(' ')[0],
        network: 'Visa',
        card_type: 'cashback',
        cashback_rate: 0.02,
        annual_fee: 0,
        benefits: [],
        source: 'manual'
    };
    detectedCards.push(newCard);
    renderCardChecklist(detectedCards);
    input.value = '';
}

async function approveCards() {
    // Collect selected cards
    const checkItems = document.querySelectorAll('.card-check-item.selected');
    selectedCards = [...checkItems].map(item => detectedCards[parseInt(item.dataset.idx)]).filter(Boolean);

    if (!selectedCards.length) {
        alert('Please select at least one card.');
        return;
    }

    const btn = $('btn-approve-cards');
    btn.textContent = 'Saving...';
    btn.disabled = true;

    try {
        const res = await fetch(`${SETUP_API}/save_cards`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cards: selectedCards })
        });
        const data = await res.json();

        if (data.status === 'SAVED') {
            wizardStep(4);
            startEnrichmentPolling(selectedCards);
        }
    } catch (e) {
        btn.textContent = 'Save These Cards →';
        btn.disabled = false;
        alert(`Save failed: ${e.message}`);
    }
}

function startEnrichmentPolling(cards) {
    // Show card list in enrichment step
    const list = $('enrich-cards-list');
    list.innerHTML = cards.map((c, i) => `
        <div class="enrich-card-item" id="enrich-${i}">
            <span class="enrich-status-icon">⏳</span>
            <span>${c.name}</span>
        </div>
    `).join('');

    const fill = $('progress-fill');
    const txt = $('progress-text');
    let lastProgress = 0;

    const poll = setInterval(async () => {
        try {
            const res = await fetch(`${SETUP_API}/enrich_status`);
            const data = await res.json();
            const prog = data.progress || 0;
            const total = data.total || cards.length;
            const pct = total > 0 ? (prog / total) * 100 : 0;

            fill.style.width = `${pct}%`;
            txt.textContent = `Enriched ${prog} of ${total} cards...`;

            // Mark enriched cards
            for (let i = lastProgress; i < prog; i++) {
                const el = document.getElementById(`enrich-${i}`);
                if (el) el.querySelector('.enrich-status-icon').textContent = '✅';
            }
            lastProgress = prog;

            if (data.status === 'complete' || prog >= total) {
                clearInterval(poll);
                fill.style.width = '100%';
                txt.textContent = 'All cards enriched!';
                setTimeout(() => showFinalStep(cards), 800);
            }
        } catch (e) {
            clearInterval(poll);
            showFinalStep(cards);
        }
    }, 1000);

    // Fallback: move to next step after 12 seconds max
    setTimeout(() => { clearInterval(poll); showFinalStep(cards); }, 12000);
}

function showFinalStep(cards) {
    const summary = $('final-card-summary');
    summary.innerHTML = cards.map(c => `
        <div class="final-card-item">
            <span>✅</span>
            <div>
                <div class="final-card-name">${c.name}</div>
                <div class="final-card-meta">${c.bank} · ${c.network} · ${(c.cashback_rate * 100).toFixed(1)}% cashback</div>
            </div>
        </div>
    `).join('');
    wizardStep(5);
}

function finishSetup() {
    $('wizard-overlay').classList.add('hidden');
    $('main-app').classList.remove('hidden');
    initDashboard();
}

// ════════════════════════════════════════════════════════════
// PRODUCT SEARCH MODAL
// ════════════════════════════════════════════════════════════

function openProductModal() {
    $('product-modal').classList.remove('hidden');
    $('product-input').focus();
    newSearch(); // Reset to input state
}

function closeProductModal() {
    $('product-modal').classList.add('hidden');
}

function newSearch() {
    $('product-search-state').classList.remove('hidden');
    $('product-results-state').classList.add('hidden');
    $('product-loading-state').classList.add('hidden');
    $('product-input').value = '';
}

function quickSearch(product) {
    $('product-input').value = product;
    searchProduct();
}

async function searchProduct() {
    const product = $('product-input').value.trim();
    if (!product) return;

    // Show loading
    $('product-search-state').classList.add('hidden');
    $('product-results-state').classList.add('hidden');
    $('product-loading-state').classList.remove('hidden');

    const statusTexts = [
        'Finding best price on Amazon & Flipkart...',
        'Checking HDFC Millennia offer...',
        'Checking Chase Sapphire cashback...',
        'Checking Axis Bank Magnus deal...',
        'Comparing savings across all cards...',
    ];
    let idx = 0;
    const rotateText = setInterval(() => {
        $('search-status-text').textContent = statusTexts[idx % statusTexts.length];
        idx++;
    }, 1800);

    try {
        const res = await fetch(`${PRODUCT_API}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product })
        });
        const data = await res.json();
        clearInterval(rotateText);

        if (data.error) {
            alert(data.error);
            newSearch();
            return;
        }

        renderProductResults(data);
    } catch (e) {
        clearInterval(rotateText);
        alert(`Search failed: ${e.message}`);
        newSearch();
    }
}

function renderProductResults(data) {
    $('product-loading-state').classList.add('hidden');
    $('product-results-state').classList.remove('hidden');

    $('results-product-name').textContent = data.product;
    const currency = data.currency === 'INR' ? '₹' : '$';
    $('results-base-price').textContent = `Base price: ${currency}${data.base_price?.toLocaleString('en-IN')} · ${data.base_price_source || 'Market price'}`;

    const best = data.best_deal;
    const container = $('deal-comparison');

    // Summary banner
    let banner = '';
    if (best) {
        banner = `
            <div class="deal-summary-banner">
                🏆 Best deal: Use your <strong>${best.card_name}</strong> — save <strong>${currency}${best.total_savings?.toLocaleString('en-IN')}</strong>, net price <strong>${currency}${best.net_price?.toLocaleString('en-IN')}</strong>
            </div>
        `;
    }

    const deals = (data.deals || []).map(deal => `
        <div class="deal-row ${deal.is_best ? 'best-deal' : ''}">
            <div>
                <div class="deal-card-name">${deal.card_name}</div>
                <div class="deal-card-sub">${deal.bank || ''} · ${deal.card_type || ''}</div>
                ${deal.deal_text ? `<div class="deal-card-sub" style="color:#94a3b8;margin-top:4px;font-size:11px">${deal.deal_text.substring(0, 100)}</div>` : ''}
            </div>
            <div class="deal-stat">
                <div class="deal-stat-value deal-base">${currency}${deal.base_cashback?.toLocaleString('en-IN') || '0'}</div>
                <div class="deal-stat-label">Cashback</div>
            </div>
            <div class="deal-stat">
                <div class="deal-stat-value deal-savings">${currency}${deal.total_savings?.toLocaleString('en-IN') || '0'}</div>
                <div class="deal-stat-label">Total Savings</div>
            </div>
            <div class="deal-stat">
                <div class="deal-stat-value deal-net-price">${currency}${deal.net_price?.toLocaleString('en-IN') || '—'}</div>
                <div class="deal-stat-label">Net Price</div>
                ${deal.is_best ? '<div class="best-badge">BEST DEAL</div>' : ''}
            </div>
        </div>
    `).join('');

    container.innerHTML = banner + deals;
}

// ════════════════════════════════════════════════════════════
// DASHBOARD & TAB SYSTEM
// ════════════════════════════════════════════════════════════

function setupTabs() {
    document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            switchTab(item.dataset.tab);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const nav = document.getElementById(`nav-${tabId}`);
    if (nav) nav.classList.add('active');

    document.querySelectorAll('.tab-content').forEach(t => {
        t.classList.remove('active');
        t.classList.add('hidden');
    });
    const tab = document.getElementById(`tab-${tabId}`);
    if (tab) { tab.classList.add('active'); tab.classList.remove('hidden'); }

    const titles = { dashboard: 'Financial Intelligence', accounts: 'My Cards', offers: 'All Deals', gmail: 'Gmail Scanner', settings: 'Agent Settings' };
    $('page-title').textContent = titles[tabId] || 'Sentinel';

    if (tabId === 'accounts') loadAccounts();
    if (tabId === 'offers') loadOffers();
    if (tabId === 'settings') loadSettings();
}

async function loadOfferOfTheDay() {
    try {
        const res = await fetch(`${API}/offer-of-the-day`);
        const data = await res.json();
        $('offer-title').textContent = data.title;
        $('offer-description').textContent = data.description;
        $('offer-erv').textContent = `ERV: $${data.erv?.toFixed(2)}`;
        $('offer-category').textContent = (data.category || '').charAt(0).toUpperCase() + (data.category || '').slice(1);
        $('stat-savings').textContent = `$${data.erv?.toFixed(2)}`;
        log(`Winning move: ${data.title} — ERV $${data.erv?.toFixed(2)}`, 'success');

        // Update card count stat
        const cardsRes = await fetch(`${SETUP_API}/status`);
        // just check DB cards
    } catch (e) {
        log(`Offer load error: ${e.message}`, 'warning');
    }
}

async function loadCardsCount() {
    try {
        const res = await fetch(`${API}/accounts`);
        const data = await res.json();
        $('stat-cards').textContent = data.accounts?.length || '—';
    } catch (e) {}
}

async function runAuction() {
    loading(true, '⚡ Specialist agents scanning for deals...');
    log('Auction triggered', 'info');
    try {
        await fetch(`${API}/trigger_auction`, { method: 'POST' });
        let attempts = 0;
        const poll = setInterval(async () => {
            attempts++;
            const s = await (await fetch(`${API}/auction_status`)).json();
            if (s.status === 'WINNING_MOVE_GENERATED') {
                clearInterval(poll);
                loading(false);
                log(`🏆 Winner: ${s.winning_agent} — ERV $${s.erv?.toFixed(2)}`, 'success');
                await loadOfferOfTheDay();
                await loadOffers();
            } else if (s.status === 'ERROR' || attempts > 20) {
                clearInterval(poll);
                loading(false);
                await loadOfferOfTheDay();
            }
        }, 1500);
    } catch (e) {
        loading(false);
        log(`Auction error: ${e.message}`, 'warning');
    }
}

// ── Accounts Tab (from DB) ────────────────────────────────────────────────
async function loadAccounts() {
    const container = $('accounts-list');
    container.innerHTML = '<div class="loading-placeholder">Loading your cards...</div>';
    try {
        // First try DB cards
        const dbRes = await fetch(`${SETUP_API}/status`);
        const dbData = await dbRes.json();

        const res = await fetch(`${API}/accounts`);
        const data = await res.json();
        if (!data.accounts?.length) {
            container.innerHTML = '<div class="loading-placeholder">No cards found. <a href="#" onclick="resetSetup()">Run setup again</a>.</div>';
            return;
        }
        container.innerHTML = data.accounts.map(acc => `
            <div class="account-card">
                <div class="account-name">${acc.name}</div>
                <div class="account-type">${acc.type || ''} · ${acc.network || ''}</div>
                ${acc.offer_title ? `<div class="account-offer-title">${acc.offer_title}</div>` : ''}
                <div class="account-offer-desc">${acc.top_offer}</div>
                <div style="margin-top:12px">
                    <button class="btn btn-success" style="font-size:12px;padding:6px 14px"
                        onclick="quickProductSearchWithCard('${acc.name}')">
                        🔍 Find Best Deal with This Card
                    </button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<div class="loading-placeholder">Error: ${e.message}</div>`;
    }
}

function quickProductSearchWithCard(cardName) {
    openProductModal();
    log(`Finding deals for: ${cardName}`, 'info');
}

// ── Offers Tab ────────────────────────────────────────────────────────────
async function loadOffers() {
    const container = $('offers-list');
    container.innerHTML = '<div class="loading-placeholder">Scanning for deals...</div>';
    try {
        const res = await fetch(`${API}/offers`);
        const data = await res.json();
        allOffers = data.offers || [];
        $('stat-cards').textContent = allOffers.length;
        renderOffers(container, data.card_used ? `<p style="font-size:12px;color:#94a3b8;margin-bottom:14px">Card used: <strong>${data.card_used}</strong></p>` : '');
        log(`Loaded ${allOffers.length} deals`, 'success');
    } catch (e) {
        container.innerHTML = `<div class="loading-placeholder">Error: ${e.message}</div>`;
    }
}

function renderOffers(container, headerHtml = '') {
    const filtered = currentFilter === 'all' ? allOffers :
        allOffers.filter(o => (o.category || '').toLowerCase().includes(currentFilter) || o.source === currentFilter);
    if (!filtered.length) {
        container.innerHTML = headerHtml + '<div class="loading-placeholder">No deals for this filter. Click "Run Agents" first.</div>';
        return;
    }
    container.innerHTML = headerHtml + filtered.map(o => `
        <div class="offer-item">
            <div class="offer-item-header">
                <div class="offer-item-title">${o.title || 'Deal'}</div>
                ${o.erv > 0 ? `<div class="offer-item-erv">ERV ~$${o.erv?.toFixed(0)}</div>` : ''}
            </div>
            <div class="offer-item-desc">${o.description || ''}</div>
            <div class="offer-item-footer">
                <span class="offer-category-tag">${o.category}</span>
                <span class="offer-source-tag">${o.source === 'gmail' ? '📧 Inbox' : o.source === 'curated' ? '⚡ Curated' : '🔍 Live'}</span>
                ${o.url ? `<a href="${o.url}" target="_blank" class="btn-outline btn" style="padding:4px 10px;font-size:11px">View →</a>` : ''}
            </div>
        </div>
    `).join('');
}

function setupOfferFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderOffers($('offers-list'));
        });
    });
}

// ── Gmail Tab ────────────────────────────────────────────────────────────
async function scanGmail() {
    const container = $('gmail-results');
    loading(true, '📧 Scanning Gmail...');
    try {
        const res = await fetch(`${API}/gmail_summary`);
        const data = await res.json();
        loading(false);
        if (data.status === 'ERROR') {
            container.innerHTML = `<div class="loading-placeholder">Gmail error: ${data.message}</div>`;
            return;
        }
        const items = [
            ...(data.rewards || []).map(r => ({ ...r, _type: 'REWARD' })),
            ...(data.subscriptions || []).map(r => ({ ...r, _type: 'SUBSCRIPTION' })),
            ...(data.cashback_offers || []).map(r => ({ ...r, _type: 'CASHBACK_OFFER' })),
        ];
        container.innerHTML = items.length === 0
            ? '<div class="loading-placeholder">No rewards or subscriptions found.</div>'
            : `<p style="font-size:13px;color:#94a3b8;margin-bottom:14px">Found ${data.total_parsed} items</p>` +
              items.map(item => `
                <div class="gmail-item">
                    <div class="gmail-type ${item._type}">${(item._type || '').replace('_',' ')}</div>
                    <div class="gmail-title">${item.source_subject || item.program || 'Email Signal'}</div>
                    <div class="gmail-detail">${item.offer_detail || ''}${item.amount ? ` — ${item.currency === 'INR' ? '₹' : '$'}${item.amount}` : ''}</div>
                </div>
              `).join('');
        log(`Gmail: ${data.total_parsed} items`, 'success');
    } catch (e) {
        loading(false);
        container.innerHTML = `<div class="loading-placeholder">Error: ${e.message}</div>`;
    }
}

// ── Settings Tab ─────────────────────────────────────────────────────────
async function loadSettings() {
    try {
        const res = await fetch(`${API}/settings`);
        const data = await res.json();
        if ($('input-budget')) $('input-budget').value = data.monthly_budget || 15000;
        if ($('input-travel')) $('input-travel').value = data.travel_budget || 30000;
        if ($('input-bills')) $('input-bills').value = data.monthly_bills || 4000;
        const mutedDisplay = $('muted-display');
        if (mutedDisplay) mutedDisplay.innerHTML = (data.muted_categories || []).map(c => `<span class="muted-tag">🔇 ${c}</span>`).join('') || '<span style="color:#475569;font-size:13px">No categories muted.</span>';
        const agentList = $('agent-toggle-list');
        if (agentList) {
            agentList.innerHTML = ['lifestyle','travel','utility'].map(agent => {
                const on = (data.active_agents || []).includes(agent);
                return `<div class="toggle-item"><span class="toggle-label">${agent.charAt(0).toUpperCase()+agent.slice(1)} Agent</span><div class="toggle-switch ${on ? 'on' : ''}" data-agent="${agent}" onclick="toggleAgent(this)"></div></div>`;
            }).join('');
        }
    } catch (e) { log(`Settings error: ${e.message}`, 'warning'); }
}

async function toggleAgent(el) {
    el.classList.toggle('on');
    const agent = el.dataset.agent;
    const isOn = el.classList.contains('on');
    const data = await (await fetch(`${API}/settings`)).json();
    let active = data.active_agents || [];
    if (isOn && !active.includes(agent)) active.push(agent);
    if (!isOn) active = active.filter(a => a !== agent);
    await fetch(`${API}/settings`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ active_agents: active }) });
    log(`${agent} agent ${isOn ? 'enabled' : 'disabled'}`, 'info');
}

async function saveSettings() {
    const body = { monthly_budget: parseInt($('input-budget')?.value), travel_budget: parseInt($('input-travel')?.value), monthly_bills: parseInt($('input-bills')?.value) };
    await fetch(`${API}/settings`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
    log('Settings saved.', 'success');
}

async function muteCategory() {
    const category = $('intent-category')?.value;
    if (!category) return;
    await fetch(`${API}/intent_update`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ user_id: 'default_user', category, intent: 'MUTE' }) });
    log(`Muted: ${category}`, 'warning');
    loadSettings();
}

async function unmuteAll() {
    await fetch(`${API}/settings`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ muted_categories: [], active_agents: ['lifestyle','travel','utility'] }) });
    log('All unmuted.', 'success');
    loadSettings();
}

async function applyMove() {
    try {
        const res = await fetch(`${API}/apply_move`, { method: 'POST' });
        if (!res.ok) { const e = await res.json(); log(`Apply failed: ${e.detail}`, 'warning'); return; }
        const data = await res.json();
        log(`✅ Move applied! Agent: ${data.agent}, ERV: $${data.erv?.toFixed(2)}`, 'success');
        alert(`✅ Move Applied!\n\nAgent: ${data.agent}\nERV Saved: $${data.erv?.toFixed(2)}\n\n${data.message}`);
    } catch (e) { log(`Apply error: ${e.message}`, 'warning'); }
}

async function resetSetup() {
    if (!confirm('Re-run setup? This will clear all saved cards.')) return;
    await fetch(`${SETUP_API}/reset`, { method: 'DELETE' });
    location.reload();
}

// ════════════════════════════════════════════════════════════
// INIT
// ════════════════════════════════════════════════════════════

function initDashboard() {
    $('current-date').textContent = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    setupTabs();
    setupOfferFilters();

    $('btn-run-auction').addEventListener('click', runAuction);
    $('btn-scan-gmail').addEventListener('click', () => { switchTab('gmail'); scanGmail(); });
    $('btn-scan-gmail-full')?.addEventListener('click', scanGmail);
    $('btn-apply').addEventListener('click', applyMove);
    $('btn-dismiss').addEventListener('click', () => {
        const c = $('offer-of-the-day-container');
        c.style.opacity = '0'; c.style.transition = 'opacity 0.3s';
        setTimeout(() => c.style.display = 'none', 300);
    });
    $('btn-refresh-offer').addEventListener('click', loadOfferOfTheDay);
    $('btn-save-settings')?.addEventListener('click', saveSettings);
    $('btn-mute-category')?.addEventListener('click', muteCategory);
    $('btn-unmute-all')?.addEventListener('click', unmuteAll);

    // Close modal on overlay click
    $('product-modal').addEventListener('click', e => { if (e.target === $('product-modal')) closeProductModal(); });

    loadOfferOfTheDay();
    loadCardsCount();
    log('Sentinel Financial OS ready. Run Agents or Find a Deal.', 'info');
}

document.addEventListener('DOMContentLoaded', async () => {
    // Check if setup is complete
    try {
        const res = await fetch(`${SETUP_API}/status`);
        const data = await res.json();
        if (data.is_complete) {
            $('wizard-overlay').classList.add('hidden');
            $('main-app').classList.remove('hidden');
            initDashboard();
        } else {
            // Show wizard
            $('wizard-overlay').classList.remove('hidden');
            $('main-app').classList.add('hidden');
            wizardStep(1);
        }
    } catch (e) {
        // If setup check fails, show app directly
        $('wizard-overlay').classList.add('hidden');
        $('main-app').classList.remove('hidden');
        initDashboard();
    }
});
