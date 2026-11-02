import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const greeting = {
  role: "assistant",
  content: "Namaste! What are we shopping for today? I can help narrow it down.",
};

async function request(path, options) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

function App() {
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [address, setAddress] = useState("");
  const [budget, setBudget] = useState("");
  const [proposal, setProposal] = useState(null);
  const [approved, setApproved] = useState(false);
  const [orders, setOrders] = useState([]);
  const [messages, setMessages] = useState([greeting]);
  const [chatText, setChatText] = useState("");
  const [voiceStatus, setVoiceStatus] = useState(null);
  const [tab, setTab] = useState("shop");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  async function search(searchQuery = query) {
    setBusy(true);
    try {
      const data = await request(`/api/products?q=${encodeURIComponent(searchQuery)}`);
      setProducts(data.products);
      setQuery(searchQuery);
      setStatus(data.products.length ? `${data.products.length} demo options found.` : "No matches in the demo catalog. Try groceries, rice, home, or headphones.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function loadOrders() {
    try {
      const data = await request("/api/orders");
      setOrders(data.orders);
    } catch (error) {
      setStatus(error.message);
    }
  }

  useEffect(() => {
    search("");
    request("/api/voice/status").then(setVoiceStatus).catch(() => setVoiceStatus(null));
    loadOrders();
  }, []);

  function updateCart(product, delta) {
    setProposal(null);
    setApproved(false);
    setCart((items) => {
      const existing = items.find((item) => item.id === product.id);
      if (!existing && delta > 0) return [...items, { ...product, quantity: 1 }];
      return items
        .map((item) => item.id === product.id ? { ...item, quantity: item.quantity + delta } : item)
        .filter((item) => item.quantity > 0);
    });
  }

  async function sendMessage(event) {
    event.preventDefault();
    const text = chatText.trim();
    if (!text || busy) return;
    const next = [...messages, { role: "user", content: text }];
    setMessages(next);
    setChatText("");
    setBusy(true);
    try {
      const result = await request("/api/chat", {
        method: "POST",
        body: JSON.stringify({ messages: next.slice(-20) }),
      });
      setMessages([...next, { role: "assistant", content: result.reply }]);
    } catch (error) {
      setMessages([...next, { role: "assistant", content: `I couldn't reach the assistant: ${error.message}` }]);
    } finally {
      setBusy(false);
    }
  }

  async function createProposal(event) {
    event.preventDefault();
    setBusy(true);
    setStatus("");
    try {
      const data = await request("/api/proposals", {
        method: "POST",
        body: JSON.stringify({
          items: cart.map((item) => ({ product_id: item.id, quantity: item.quantity })),
          budget: budget ? Number(budget) : null,
          address,
        }),
      });
      setProposal(data);
      setApproved(false);
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function approveProposal() {
    if (!proposal || !approved || busy) return;
    setBusy(true);
    try {
      const order = await request(`/api/proposals/${proposal.id}/approve`, {
        method: "POST",
        body: JSON.stringify({
          approved: true,
          idempotency_key: crypto.randomUUID(),
        }),
      });
      setProposal(null);
      setCart([]);
      setApproved(false);
      setTab("orders");
      await loadOrders();
      setStatus(`Demo order ${order.id.slice(0, 8)} created. No payment was taken.`);
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="#"><span className="brand-mark">v</span>vaani<span>buy</span></a>
        <div className="top-note"><span className="live-dot" /> YOUR PERSONAL SHOPPING ASSISTANT</div>
        <nav className="nav-tabs">
          <button className={tab === "shop" ? "nav-active" : ""} onClick={() => setTab("shop")}>Shop</button>
          <button className={tab === "orders" ? "nav-active" : ""} onClick={() => { setTab("orders"); loadOrders(); }}>Orders</button>
        </nav>
      </header>

      <section className="intro">
        <div className="eyebrow"><span>✳</span> A MORE HUMAN WAY TO SHOP</div>
        <h1>Tell us what you need.<br /><em>We'll find your fit.</em></h1>
        <p>Thoughtful recommendations, in your language and on your terms.</p>
      </section>

      {status && <div className="notice" role="status">{status}<button onClick={() => setStatus("")}>×</button></div>}

      {tab === "shop" ? <div className="workspace">
        <section className="search-panel">
          <div className="panel-heading">
            <div><span className="step">01</span><h2>Start with a wish</h2></div>
            <span className="language">ENGLISH⌄</span>
          </div>
          <div className="assistant">
            <div className="assistant-icon">v</div>
            <div><strong>Namaste! What are we shopping for?</strong><p>{status || "Share your needs, budget and preferences. You stay in control."}</p></div>
          </div>
          <form onSubmit={(event) => { event.preventDefault(); search(); }} className="search-form">
            <label htmlFor="request">SEARCH THE DEMO CATALOG</label>
            <div className="input-wrap">
              <span className="search-icon">⌕</span>
              <input id="request" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="e.g. pantry essentials for the week..." />
              <button type="submit" disabled={busy}>{busy ? "Working..." : "Find items"} <span>↗</span></button>
            </div>
          </form>
          <div className="suggestions">
            <span>TRY</span>
            {["Groceries", "Rice", "Headphones"].map((item) => <button key={item} onClick={() => search(item)}>{item}</button>)}
          </div>
          <div className="voice-note">
            <span className="mic">◉</span>
            <span><b>Voice shopping</b> {voiceStatus?.ready ? "is ready to connect." : "needs Samvaad setup."}</span>
            <span className="soon">{voiceStatus?.ready ? "READY" : "SETUP NEEDED"}</span>
          </div>
          <div className="chat-box">
            <div className="chat-title"><b>Talk it through</b><span>AI REQUIREMENTS ASSISTANT</span></div>
            <div className="chat-messages">
              {messages.slice(-6).map((message, index) => <p className={`chat-message ${message.role}`} key={`${index}-${message.content.slice(0, 12)}`}>{message.content}</p>)}
            </div>
            <form className="chat-input" onSubmit={sendMessage}>
              <input value={chatText} onChange={(event) => setChatText(event.target.value)} placeholder="Tell me what you're looking for..." maxLength={2000} />
              <button disabled={busy || !chatText.trim()} aria-label="Send message">↑</button>
            </form>
            <small>AI helps gather needs; catalog prices are demo data.</small>
          </div>
        </section>

        <aside className="list-panel">
          <div className="list-heading"><div><span className="step">02</span><h2>Your shortlist</h2></div><span className="count">{cart.reduce((sum, item) => sum + item.quantity, 0)}</span></div>
          {cart.length ? <div className="shortlist">
            {cart.map((item) => <div className="short-item" key={item.id}>
              <span>{item.emoji}</span><div><b>{item.name}</b><small>₹{item.price} / {item.unit}</small></div>
              <div className="quantity"><button onClick={() => updateCart(item, -1)} aria-label="Decrease quantity">−</button><b>{item.quantity}</b><button onClick={() => updateCart(item, 1)} aria-label="Increase quantity">+</button></div>
            </div>)}
            <div className="total"><span>ITEM SUBTOTAL</span><b>₹{cartTotal.toLocaleString("en-IN")}</b></div>
            <form className="proposal-form" onSubmit={createProposal}>
              <label>DELIVERY ADDRESS<input required minLength="5" maxLength="300" value={address} onChange={(event) => setAddress(event.target.value)} placeholder="Your delivery address" /></label>
              <label>BUDGET (OPTIONAL)<input type="number" min="1" value={budget} onChange={(event) => setBudget(event.target.value)} placeholder="₹ Set a max budget" /></label>
              <button className="approval" disabled={busy}>{proposal ? "Refresh proposal" : "Review proposal"} <span>→</span></button>
            </form>
            {proposal && <div className="proposal">
              <b>Purchase proposal · Demo only</b>
              <div><span>Items</span><span>₹{proposal.subtotal}</span></div>
              <div><span>Delivery</span><span>₹{proposal.delivery_fee}</span></div>
              <div className="proposal-total"><span>Total</span><b>₹{proposal.total}</b></div>
              <small>Deliver to: {proposal.address}</small>
              <label className="approve-check"><input type="checkbox" checked={approved} onChange={(event) => setApproved(event.target.checked)} /> I approve this simulated order for ₹{proposal.total}.</label>
              <button className="confirm-order" disabled={!approved || busy} onClick={approveProposal}>{busy ? "Processing..." : "Confirm demo order"}</button>
            </div>}
            <p className="demo-caption">Mock catalog and checkout. No real payment or order.</p>
          </div> : <div className="empty"><div className="basket">＋</div><b>Your list starts here</b><p>Add an item you like and we'll keep everything together.</p></div>}
        </aside>
      </div> : <section className="orders-panel">
        <div className="results-heading"><div><span className="step">04</span><h2>Order history</h2></div><span>DEMO ORDERS ONLY</span></div>
        {orders.length ? <div className="order-list">{orders.map((order) => <article className="order-card" key={order.id}>
          <div className="order-icon">✓</div><div className="order-main"><b>Demo order · {order.id.slice(0, 8)}</b><small>{new Date(`${order.created_at}Z`).toLocaleString()} · {order.items.length} item(s)</small><small>Payment: not charged · Tracking: simulated</small></div><strong>₹{order.total}</strong><a href={`${API}/api/orders/${order.id}/receipt`}>Receipt PDF ↗</a>
        </article>)}</div> : <div className="empty"><div className="basket">↗</div><b>No orders yet</b><p>Your approved demo orders will appear here.</p></div>}
      </section>}

      {tab === "shop" && <section className="results">
        <div className="results-heading"><div><span className="step">03</span><h2>{products.length ? "Picked for you" : "A little more personal"}</h2></div><span>{products.length ? `${products.length} DEMO PICKS` : "BUILT AROUND YOU"}</span></div>
        {products.length ? <div className="product-grid">{products.map((item) => {
          const quantity = cart.find((product) => product.id === item.id)?.quantity || 0;
          return <article className="product" key={item.id}>
            <div className="product-art"><span>{item.emoji}</span><small>DEMO CATALOG</small></div>
            <div className="product-info"><div className="category">{item.category}</div><h3>{item.name}</h3>
              <div className="product-bottom"><div><b>₹{item.price}</b><small> / {item.unit}</small></div><button className={quantity ? "added" : ""} onClick={() => updateCart(item, 1)} aria-label="Add to shortlist">{quantity ? `+ ${quantity}` : "+"}</button></div>
              <small className="seller">Sample seller · {item.seller}</small>
            </div>
          </article>;
        })}</div> : <div className="trust-row"><div><span>01</span><b>We listen first</b><small>Your needs, budget and preferences come before recommendations.</small></div><div><span>02</span><b>You stay in control</b><small>Nothing is ordered without your explicit approval.</small></div><div><span>03</span><b>Made for Bharat</b><small>Shop naturally across Indian languages.</small></div></div>}
      </section>}
      <footer><span>vaanibuy</span><span>Thoughtful commerce, with you in control.</span><span>DEMO CATALOG · NO REAL ORDERS</span></footer>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
