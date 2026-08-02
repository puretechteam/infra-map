var currentFilters = {
    provider: '',
    region: '',
    search: '',
    mode: 'datacenters'
};

function initFilters() {
    fetch('/api/providers')
        .then(function(response) { return response.json(); })
        .then(function(result) {
            var providers = result.providers || [];
            var select = document.getElementById('provider-filter');
            if (!select) return;
            select.innerHTML = '<option value="">All Providers</option>';
            for (var i = 0; i < providers.length; i++) {
                var option = document.createElement('option');
                option.value = providers[i];
                option.textContent = providers[i];
                select.appendChild(option);
            }
            addSearchToDropdown(select);
        })
        .catch(function() {
            loadBundledProviders();
        });

    fetch('/api/regions')
        .then(function(response) { return response.json(); })
        .then(function(result) {
            var regions = result.regions || [];
            var select = document.getElementById('region-filter');
            if (!select) return;
            select.innerHTML = '<option value="">All Regions</option>';
            for (var i = 0; i < regions.length; i++) {
                var option = document.createElement('option');
                option.value = regions[i];
                option.textContent = regions[i];
                select.appendChild(option);
            }
            addSearchToDropdown(select);
        })
        .catch(function() {
            loadBundledRegions();
        });

    document.getElementById('provider-filter').addEventListener('change', applyFilters);
    document.getElementById('region-filter').addEventListener('change', applyFilters);
    document.getElementById('search-btn').addEventListener('click', applyFilters);
    document.getElementById('search-input').addEventListener('keyup', function(e) {
        if (e.key === 'Enter') {
            applyFilters();
        }
    });
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    document.getElementById('export-btn').addEventListener('click', exportFilteredData);
    document.getElementById('detail-close').addEventListener('click', resetDetailPanel);

    var mobileBtn = document.getElementById('mobile-menu-btn');
    if (mobileBtn) {
        mobileBtn.addEventListener('click', toggleSidebar);
    }

    var sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    var modeBtns = document.querySelectorAll('.mode-btn');
    for (var j = 0; j < modeBtns.length; j++) {
        modeBtns[j].addEventListener('click', function() {
            setMode(this.getAttribute('data-mode'));
        });
    }
}

function setMode(mode) {
    currentFilters.mode = mode;
    var modeBtns = document.querySelectorAll('.mode-btn');
    for (var i = 0; i < modeBtns.length; i++) {
        if (modeBtns[i].getAttribute('data-mode') === mode) {
            modeBtns[i].classList.add('active');
        } else {
            modeBtns[i].classList.remove('active');
        }
    }
    applyFilters();
}

function addSearchToDropdown(select) {
    if (!select) return;
    select.setAttribute('list', select.id + '-datalist');

    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'dropdown-search';
    input.placeholder = 'Filter...';
    input.style.cssText = 'padding:4px 8px;border:1px solid #0f3460;border-radius:4px;background-color:#1a1a2e;color:#e0e0e0;font-size:0.8rem;width:100%;margin-bottom:4px;';

    select.parentNode.insertBefore(input, select);

    input.addEventListener('input', function() {
        var filter = input.value.toLowerCase();
        var options = select.options;
        for (var i = 0; i < options.length; i++) {
            var text = options[i].textContent.toLowerCase();
            options[i].style.display = text.indexOf(filter) !== -1 ? '' : 'none';
        }
    });

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            input.value = '';
            var filter = '';
            var options = select.options;
            for (var i = 0; i < options.length; i++) {
                options[i].style.display = '';
            }
            input.blur();
        }
    });
}

function loadBundledProviders() {
    fetch('/static/data/data_centers.json')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            var providers = sortedUnique(data.map(function(d) { return d.provider; }));
            var select = document.getElementById('provider-filter');
            if (!select) return;
            select.innerHTML = '<option value="">All Providers</option>';
            for (var i = 0; i < providers.length; i++) {
                var option = document.createElement('option');
                option.value = providers[i];
                option.textContent = providers[i];
                select.appendChild(option);
            }
        });
}

function loadBundledRegions() {
    fetch('/static/data/data_centers.json')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            var regions = sortedUnique(data.map(function(d) { return d.region; }));
            var select = document.getElementById('region-filter');
            if (!select) return;
            select.innerHTML = '<option value="">All Regions</option>';
            for (var i = 0; i < regions.length; i++) {
                var option = document.createElement('option');
                option.value = regions[i];
                option.textContent = regions[i];
                select.appendChild(option);
            }
        });
}

function sortedUnique(arr) {
    return arr.filter(function(v, i, a) { return a.indexOf(v) === i; }).sort();
}

function filterEntries(entries, filters) {
    var filtered = entries;

    if (filters.provider) {
        filtered = filtered.filter(function(dc) {
            return dc.provider === filters.provider;
        });
    }

    if (filters.region) {
        filtered = filtered.filter(function(dc) {
            return dc.region === filters.region;
        });
    }

    if (filters.search) {
        filtered = filtered.filter(function(dc) {
            return dc.name.toLowerCase().indexOf(filters.search) !== -1 ||
                   dc.city.toLowerCase().indexOf(filters.search) !== -1;
        });
    }

    return filtered;
}

function applyFilters() {
    currentFilters.provider = document.getElementById('provider-filter').value;
    currentFilters.region = document.getElementById('region-filter').value;
    currentFilters.search = document.getElementById('search-input').value.toLowerCase().trim();

    filteredData = filterEntries(allData, currentFilters);

    addMarkers(filteredData);
}

function resetFilters() {
    document.getElementById('provider-filter').value = '';
    document.getElementById('region-filter').value = '';
    document.getElementById('search-input').value = '';
    currentFilters.provider = '';
    currentFilters.region = '';
    currentFilters.search = '';
    filteredData = allData;
    addMarkers(allData);
}

function exportFilteredData() {
    var filtered = filterEntries(allData, currentFilters);

    var blob = new Blob([JSON.stringify(filtered, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'infra-map-export.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initFilters();
});