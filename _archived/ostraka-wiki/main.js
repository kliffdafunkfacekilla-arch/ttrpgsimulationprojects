import './style.css'
import L from 'leaflet'
import { marked } from 'marked';

// ============================================================
// CONFIG
// ============================================================
let slides = [];
let currentSlide = 0;
let regionMap = null;
let currentMapSrc = '/map_full.png';

let allMarkers = [];
const slidesBySector = {};

const W_total = 2819;
const H_total = 1481;
const cell_width = W_total / 26;
const cell_height = H_total / 26;

// Types of markers we want to ignore for lore-matching because they are generic words
const ignoreLoreMatchNames = new Set([
  'heart', 'pirates', 'dungeon', 'ruined outpost', 'bridge', 'mine', 'inn', 'tavern', 'lighthouse', 'cave', 'ruins', 'camp', 'camp site', 'battlefield', 'ruined tower', 'ruined castle'
]);

// ============================================================
// DOM REFS
// ============================================================
const slideshow        = document.getElementById('slideshow');
const slideLabel       = document.getElementById('slide-label');
const slideChapTitle   = document.getElementById('slide-chapter-title');
const slideBody        = document.getElementById('slide-body');
const navTitle         = document.getElementById('nav-title');
const btnPrev          = document.getElementById('btn-prev');
const btnNext          = document.getElementById('btn-next');
const worldMapImg      = document.getElementById('world-map-img');
const worldGrid        = document.getElementById('world-grid');
const illustZone       = document.getElementById('illus-zone');
const illustImg        = document.getElementById('illus-img');
const eraMapZone       = document.getElementById('era-map-zone');
const regionView       = document.getElementById('region-view');
const btnBack          = document.getElementById('btn-back');
const tocSidebar       = document.getElementById('toc-sidebar');
const tocList          = document.getElementById('toc-list');
const regionLorePanel  = document.getElementById('region-lore-panel');
const regionLoreList   = document.getElementById('region-lore-list');

const mapView          = document.getElementById('map-view');
const explorerMapImg   = document.getElementById('explorer-map-img');
const mapVariantSelect = document.getElementById('map-variant-select');
const btnGotoMap       = document.getElementById('btn-goto-map');
const btnGotoWiki      = document.getElementById('btn-goto-wiki');

// ============================================================
// GRID: align invisible 26x26 grid over the map explorer image
// ============================================================
function syncGrid() {
  if (!explorerMapImg) return;
  const r = explorerMapImg.getBoundingClientRect();
  const w = explorerMapImg.closest('.world-map-wrapper').getBoundingClientRect();
  worldGrid.style.top    = (r.top  - w.top)  + 'px';
  worldGrid.style.left   = (r.left - w.left) + 'px';
  worldGrid.style.width  = r.width  + 'px';
  worldGrid.style.height = r.height + 'px';
}
explorerMapImg.addEventListener('load', syncGrid);
window.addEventListener('resize', syncGrid);
if (explorerMapImg.complete) syncGrid();

// Build 26x26 grid cells inside the map explorer view
for (let r = 0; r < 26; r++) {
  for (let c = 0; c < 26; c++) {
    const cell = document.createElement('div');
    cell.className = 'grid-cell';
    const rowChar = String.fromCharCode(65 + r);
    const colNum  = c + 1;
    const tileId  = `${rowChar}${colNum}`;
    cell.title = `Sector ${tileId}`;
    cell.addEventListener('click', () => {
      window.location.hash = `sector-${tileId}`;
    });
    worldGrid.appendChild(cell);
  }
}

// Map variant selector swapping the explorer map image
mapVariantSelect.addEventListener('change', (e) => {
  explorerMapImg.src = e.target.value;
});

// ============================================================
// REGION VIEW: open a single 11K tile in Leaflet (completely clean map)
// ============================================================
function openRegion(tileId) {
  if (!regionMap) {
    regionMap = L.map('region-map', {
      crs: L.CRS.Simple,
      minZoom: -3,
      maxZoom: 2,
      zoomControl: false
    });
    L.control.zoom({ position: 'bottomright' }).addTo(regionMap);
  }

  // Clear existing map layers (completely clean map, no visual markers added)
  regionMap.eachLayer(layer => regionMap.removeLayer(layer));

  const w = 11276, h = 5846;
  const bounds = [[0, 0], [h, w]];
  L.imageOverlay(`/tiles/${tileId}.png`, bounds).addTo(regionMap);
  regionMap.setMaxBounds(bounds);
  regionMap.fitBounds(bounds);

  // Update Region Archives lore panel
  const relatedSlideIndices = slidesBySector[tileId] || [];
  
  regionLorePanel.classList.remove('hidden');
  regionLoreList.innerHTML = '';

  if (relatedSlideIndices.length > 0) {
    relatedSlideIndices.forEach(idx => {
      const slide = slides[idx];
      const item = document.createElement('div');
      item.className = 'region-lore-item';
      
      const title = document.createElement('h4');
      title.textContent = slide.section_title;
      
      const chap = document.createElement('span');
      chap.className = 'region-lore-chapter';
      chap.textContent = slide.chapter_title;
      
      item.appendChild(title);
      item.appendChild(chap);
      item.addEventListener('click', () => {
        // Route to the specific slideshow article
        window.location.hash = `slide-${idx}`;
      });
      
      regionLoreList.appendChild(item);
    });
  } else {
    // Clean text indicator when no direct article links are matching
    const placeholder = document.createElement('div');
    placeholder.className = 'no-lore-placeholder';
    placeholder.innerHTML = '<p>No historical archives found for this sector.</p>';
    regionLoreList.appendChild(placeholder);
  }

  // Automatic Navigation: Display the relative article when zooming in
  let targetIdx = -1;
  if (relatedSlideIndices.length > 0) {
    // Use first matching lore article for this sector
    targetIdx = relatedSlideIndices[0];
  } else {
    // Calculate regional fallback based on coordinate grid rows/cols
    const row = tileId.charCodeAt(0) - 65;
    const col = parseInt(tileId.slice(1), 10) - 1;
    
    if (row < 6) {
      targetIdx = 419; // Chapter 8: Frozen North
    } else if (row > 18) {
      targetIdx = 374; // Chapter 7: Delta & Abyss
    } else if (col < 11) {
      targetIdx = 143; // Chapter 5: Heartland
    } else if (col > 15) {
      targetIdx = 258; // Chapter 6: Canopy & Steppes
    } else {
      targetIdx = 442; // Chapter 9: Coastal & Oceanic
    }
  }

  if (targetIdx !== -1 && targetIdx !== currentSlide) {
    goTo(targetIdx, targetIdx > currentSlide ? 'next' : 'prev', false);
  }
}

// Navigation Back to Map Explorer
btnBack.addEventListener('click', () => {
  window.location.hash = 'map';
});

// Routing controls
btnGotoMap.addEventListener('click', () => {
  window.location.hash = 'map';
});
btnGotoWiki.addEventListener('click', () => {
  window.location.hash = `slide-${currentSlide}`;
});

// ============================================================
// MAP SWITCHING: crossfade between era maps (static in slideshow)
// ============================================================
function switchMap(newSrc) {
  if (newSrc === currentMapSrc) return;
  currentMapSrc = newSrc;

  worldMapImg.style.transition = 'opacity 0.4s ease';
  worldMapImg.style.opacity = '0';
  setTimeout(() => {
    worldMapImg.onload = () => {
      worldMapImg.style.opacity = '1';
    };
    worldMapImg.src = newSrc;
    if (worldMapImg.complete) {
      worldMapImg.style.opacity = '1';
    }
  }, 400);
}

// ============================================================
// ILLUSTRATION SWITCHING: show/hide framed illustration
// ============================================================
function switchIllustration(src) {
  // Try loading; if it 404s, hide the panel
  const testImg = new Image();
  testImg.onload = () => {
    illustImg.src = src;
    illustZone.classList.remove('hidden');
    eraMapZone.classList.remove('with-illus');
    eraMapZone.classList.add('with-illus');
  };
  testImg.onerror = () => {
    illustZone.classList.add('hidden');
    eraMapZone.classList.remove('with-illus');
  };
  testImg.src = src;
}

// ============================================================
// SLIDE RENDERING
// ============================================================
function renderSlide(index, direction = 'next') {
  if (!slides.length) return;
  const slide = slides[index];

  // Animate out
  slideBody.classList.add(direction === 'next' ? 'slide-exit-left' : 'slide-exit-right');

  setTimeout(() => {
    // Update content
    slideLabel.textContent = `${slide.chapter_title}`;
    slideChapTitle.textContent = slide.section_title;
    navTitle.textContent = slide.chapter_title;
    slideBody.innerHTML = marked.parse(slide.body_markdown);

    // Animate in
    slideBody.classList.remove('slide-exit-left', 'slide-exit-right');
    slideBody.classList.add(direction === 'next' ? 'slide-enter-right' : 'slide-enter-left');
    requestAnimationFrame(() => {
      slideBody.classList.remove('slide-enter-right', 'slide-enter-left');
    });

    // Scroll text back to top
    slideBody.scrollTop = 0;

    // Check if slide references any location from markers
    const existingBadge = document.getElementById('slide-location-badge');
    if (existingBadge) existingBadge.remove();

    const slideText = (slide.section_title + " " + slide.body_markdown).toLowerCase();
    let matchedMarker = null;
    let matchedTileId = null;

    for (const marker of allMarkers) {
      const nameClean = marker.properties.name.split('—')[0].split(' - ')[0].trim();
      const nameLower = nameClean.toLowerCase();
      if (nameLower.length < 5 || ignoreLoreMatchNames.has(nameLower)) continue;
      
      const escaped = nameClean.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
      const nameRegex = new RegExp('\\b' + escaped + '\\b', 'i');
      if (nameRegex.test(slideText)) {
        matchedMarker = marker;
        const col = Math.floor(marker.properties.x / cell_width);
        const row = Math.floor(marker.properties.y / cell_height);
        if (row >= 0 && row < 26 && col >= 0 && col < 26) {
          const rowChar = String.fromCharCode(65 + row);
          const colNum = col + 1;
          matchedTileId = `${rowChar}${colNum}`;
        }
        break;
      }
    }

    if (matchedMarker && matchedTileId) {
      const badge = document.createElement('button');
      badge.id = 'slide-location-badge';
      badge.className = 'slide-location-badge';
      badge.textContent = `Explore: ${matchedMarker.properties.name} (Sector ${matchedTileId})`;
      badge.addEventListener('click', () => {
        window.location.hash = `sector-${matchedTileId}`;
      });
      slideLabel.after(badge);
    }

    // Map hiding for Chapters 1 and 2
    if (slide.chapter_file === 'Chapter_01_The_First_Age.md' || slide.chapter_file === 'Chapter_02_The_Fall.md') {
      eraMapZone.style.display = 'none';
      illustZone.style.flex = '1';
    } else {
      eraMapZone.style.display = '';
      illustZone.style.flex = '';
    }

    // Switch map and illustration (static visual panel inside slideshow)
    switchMap(slide.era_map);
    switchIllustration(slide.illustration);

    // Update nav buttons
    btnPrev.disabled = index === 0;
    btnNext.disabled = index === slides.length - 1;
  }, 250);
}

// ============================================================
// NAVIGATION
// ============================================================
function goTo(index, direction, updateHash = true) {
  if (index < 0 || index >= slides.length) return;
  currentSlide = index;
  renderSlide(currentSlide, direction);
  if (updateHash) {
    window.location.hash = 'slide-' + index;
  }
}

// ============================================================
// ROUTING
// ============================================================
function handleRouting() {
  const hash = window.location.hash;
  
  // Hide all views by default
  slideshow.classList.add('hidden');
  mapView.classList.add('hidden');
  regionView.classList.add('hidden');
  
  if (hash === '#map') {
    mapView.classList.remove('hidden');
    syncGrid();
  } else if (hash.startsWith('#sector-')) {
    const tileId = hash.replace('#sector-', '');
    regionView.classList.remove('hidden');
    openRegion(tileId);
  } else {
    // Default to slideshow/wiki view
    slideshow.classList.remove('hidden');
    
    let slideIdx = 0;
    if (hash.startsWith('#slide-')) {
      const idx = parseInt(hash.replace('#slide-', ''), 10);
      if (!isNaN(idx) && idx >= 0 && idx < slides.length) {
        slideIdx = idx;
      }
    }
    
    if (slides.length > 0 && slideIdx !== currentSlide) {
      goTo(slideIdx, slideIdx > currentSlide ? 'next' : 'prev', false);
    }
  }
}

window.addEventListener('hashchange', handleRouting);

btnPrev.addEventListener('click', () => goTo(currentSlide - 1, 'prev'));
btnNext.addEventListener('click', () => goTo(currentSlide + 1, 'next'));

document.addEventListener('keydown', e => {
  const hash = window.location.hash;
  // Only use arrow keys inside the wiki slideshow view
  if (!hash.startsWith('#map') && !hash.startsWith('#sector-')) {
    if (e.key === 'ArrowRight') goTo(currentSlide + 1, 'next');
    if (e.key === 'ArrowLeft')  goTo(currentSlide - 1, 'prev');
  }
});

// ============================================================
// TOC
// ============================================================
document.getElementById('toc-toggle').addEventListener('click', () => {
  tocSidebar.classList.remove('hidden');
});
document.getElementById('toc-close').addEventListener('click', () => {
  tocSidebar.classList.add('hidden');
});

// ============================================================
// BOOTSTRAP: load manifest and markers
// ============================================================
Promise.all([
  fetch('/data/slides_manifest.json').then(r => r.json()),
  fetch('/data/markers.geojson').then(r => r.json())
])
  .then(([slidesData, geojsonData]) => {
    slides = slidesData;
    allMarkers = geojsonData.features;

    // Build the dynamic Sector -> Slide mapping based on marker names
    allMarkers.forEach(marker => {
      const p = marker.properties;
      const nameClean = p.name.split('—')[0].split(' - ')[0].trim();
      const nameLower = nameClean.toLowerCase();
      
      if (nameLower.length < 5 || ignoreLoreMatchNames.has(nameLower)) return;
      
      const col = Math.floor(p.x / cell_width);
      const row = Math.floor(p.y / cell_height);
      if (row >= 0 && row < 26 && col >= 0 && col < 26) {
        const rowChar = String.fromCharCode(65 + row);
        const colNum = col + 1;
        const tileId = `${rowChar}${colNum}`;
        
        const escaped = nameClean.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        const regex = new RegExp('\\b' + escaped + '\\b', 'i');
        
        slides.forEach((slide, idx) => {
          if (regex.test(slide.body_markdown) || regex.test(slide.section_title)) {
            if (!slidesBySector[tileId]) {
              slidesBySector[tileId] = [];
            }
            if (!slidesBySector[tileId].includes(idx)) {
              slidesBySector[tileId].push(idx);
            }
          }
        });
      }
    });

    // Build TOC grouped by chapter
    let lastChapter = '';
    slides.forEach((slide, idx) => {
      if (slide.chapter_title !== lastChapter) {
        const header = document.createElement('li');
        header.className = 'toc-chapter-header';
        header.textContent = slide.chapter_title;
        tocList.appendChild(header);
        lastChapter = slide.chapter_title;
      }
      const li = document.createElement('li');
      li.className = 'toc-section';
      li.textContent = slide.section_title;
      li.addEventListener('click', () => {
        // Force routing to the slide hash
        window.location.hash = `slide-${idx}`;
        tocSidebar.classList.add('hidden');
      });
      tocList.appendChild(li);
    });

    // Handle initial routing based on URL hash
    handleRouting();
  })
  .catch(err => {
    console.error('Error bootstrapping application:', err);
  });
