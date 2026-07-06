document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const searchInput = document.getElementById("searchInput");
  const filtersContainer = document.getElementById("filtersContainer");
  const trendingGrid = document.getElementById("trendingGrid");
  const detailsDrawer = document.getElementById("detailsDrawer");
  const drawerBackdrop = document.getElementById("drawerBackdrop");
  const closeDrawerBtn = document.getElementById("closeDrawer");
  const themeToggleBtn = document.getElementById("themeToggle");

  // Drawer Elements
  const drawerBadge = document.getElementById("drawerBadge");
  const drawerTitle = document.getElementById("drawerTitle");
  const drawerStat = document.getElementById("drawerStat");
  const drawerDescription = document.getElementById("drawerDescription");
  const drawerTips = document.getElementById("drawerTips");
  const drawerResources = document.getElementById("drawerResources");

  // App State
  let activeCategory = "all";
  let searchQuery = "";

  // Category Labels Translations
  const categoryLabels = {
    ai: "IA & Tecnologia",
    harassment: "Assédio & Violência",
    privacy: "Privacidade",
    protection: "Proteção & Prevenção"
  };

  // 1. Theme management
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);

  themeToggleBtn.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
  });

  // 2. Render Cards
  function renderCards() {
    // Clear previous items
    trendingGrid.innerHTML = "";

    // Filter data
    const filteredData = trendingData.filter(topic => {
      const matchesCategory = activeCategory === "all" || topic.category === activeCategory;
      
      const searchLower = searchQuery.toLowerCase();
      const matchesSearch = 
        topic.title.toLowerCase().includes(searchLower) ||
        topic.shortDescription.toLowerCase().includes(searchLower) ||
        topic.originalTag.toLowerCase().includes(searchLower);

      return matchesCategory && matchesSearch;
    });

    // Sort by Trend Score (highest first)
    filteredData.sort((a, b) => b.trendScore - a.trendScore);

    // Empty state
    if (filteredData.length === 0) {
      trendingGrid.innerHTML = `
        <div class="no-results">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="8" y1="12" x2="16" y2="12"></line>
          </svg>
          <h4>Nenhum tópico encontrado</h4>
          <p>Tente refinar sua pesquisa ou tente selecionar outra categoria.</p>
        </div>
      `;
      return;
    }

    // Render cards
    filteredData.forEach((topic, index) => {
      const card = document.createElement("article");
      card.className = "topic-card";
      card.setAttribute("tabindex", "0");
      card.setAttribute("aria-label", `Tópico: ${topic.title}. Trend score: ${topic.trendScore}%`);

      // Determine category badge class
      const badgeClass = `badge-${topic.category}`;
      const badgeText = categoryLabels[topic.category] || topic.category;

      card.innerHTML = `
        <div class="card-header">
          <span class="topic-badge ${badgeClass}">${badgeText}</span>
          <div class="trend-rank">
            <span class="trend-up">▲</span>
            <span>${topic.trendScore}%</span>
          </div>
        </div>
        <div>
          <h3>${topic.title}</h3>
          <p>${topic.shortDescription}</p>
        </div>
        <div class="card-footer">
          <div class="card-stat">
            <span class="card-stat-label">Dados Críticos</span>
            <span class="card-stat-val">${topic.statistic.length > 40 ? topic.statistic.slice(0, 37) + '...' : topic.statistic}</span>
          </div>
          <button class="learn-more-btn" aria-label="Saber mais sobre ${topic.title}">
            Ver Detalhes
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </button>
        </div>
      `;

      // Event listener to open drawer
      const openAction = () => openDrawer(topic);
      card.addEventListener("click", openAction);
      
      // Accessibility support for keyboard navigation
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openAction();
        }
      });

      trendingGrid.appendChild(card);
    });
  }

  // 3. Open Details Drawer
  function openDrawer(topic) {
    // Fill Drawer Content
    const badgeText = categoryLabels[topic.category] || topic.category;
    drawerBadge.textContent = badgeText;
    drawerBadge.className = `topic-badge badge-${topic.category}`;
    
    drawerTitle.textContent = topic.title;
    drawerStat.textContent = topic.statistic;
    drawerDescription.textContent = topic.longDescription;

    // Render Tips list
    drawerTips.innerHTML = "";
    topic.tips.forEach(tip => {
      const li = document.createElement("li");
      li.textContent = tip;
      drawerTips.appendChild(li);
    });

    // Render Resources list
    drawerResources.innerHTML = "";
    topic.resources.forEach(res => {
      const a = document.createElement("a");
      a.href = res.url;
      a.className = "resource-card";
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.innerHTML = `
        <span>${res.label}</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
          <polyline points="15 3 21 3 21 9"></polyline>
          <line x1="10" y1="14" x2="21" y2="3"></line>
        </svg>
      `;
      drawerResources.appendChild(a);
    });

    // Animate Open
    detailsDrawer.classList.add("open");
    drawerBackdrop.classList.add("open");
    detailsDrawer.setAttribute("aria-hidden", "false");
    
    // Focus close button for accessibility
    setTimeout(() => {
      closeDrawerBtn.focus();
    }, 100);

    // Prevent body scroll
    document.body.style.overflow = "hidden";
  }

  // 4. Close Details Drawer
  function closeDrawer() {
    detailsDrawer.classList.remove("open");
    drawerBackdrop.classList.remove("open");
    detailsDrawer.setAttribute("aria-hidden", "true");
    
    // Restore body scroll
    document.body.style.overflow = "";
  }

  // Drawer Event Listeners
  closeDrawerBtn.addEventListener("click", closeDrawer);
  drawerBackdrop.addEventListener("click", closeDrawer);

  // Close drawer on Escape key press
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && detailsDrawer.classList.contains("open")) {
      closeDrawer();
    }
  });

  // 5. Search Input Handler
  searchInput.addEventListener("input", (e) => {
    searchQuery = e.target.value;
    renderCards();
  });

  // 6. Category Filter Buttons Handler
  filtersContainer.addEventListener("click", (e) => {
    const btn = e.target.closest(".filter-btn");
    if (!btn) return;

    // Toggle Active class
    filtersContainer.querySelectorAll(".filter-btn").forEach(button => {
      button.classList.remove("active");
    });
    btn.classList.add("active");

    // Set Category State & Render
    activeCategory = btn.dataset.category;
    renderCards();
  });

  // Initial render
  renderCards();
});
