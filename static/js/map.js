var map;
var markers = [];
var allData = [];
var filteredData = [];
var providerColors = {};
var colorIndex = 0;
var colorPalette = [
    '#e94560', '#0f3460', '#16213e', '#533483', '#00b4d8',
    '#ff6b35', '#06d6a0', '#118ab2', '#ef476f', '#ffd166',
    '#073b4c', '#8338ec', '#3a86ff', '#fb5607', '#ff006e',
    '#8ac926', '#1982c4', '#6a4c93', '#f72585', '#4cc9f0',
    '#7209b7', '#3a0ca3', '#4361ee', '#4895ef', '#b5179e',
    '#560bad', '#480ca8', '#3f37c9'
];
var markerLayer = null;
var clusterGroup = null;
var updateRAF = null;
var pendingData = null;
var cameraConesLayer = null;
var coneDebounceTimer = null;
var coneUpdateRAF = null;
var CONE_DEBOUNCE_MS = 400;
var conesEnabled = true;

function getProviderColor(provider) {
    if (!providerColors[provider]) {
        providerColors[provider] = colorPalette[colorIndex % colorPalette.length];
        colorIndex++;
    }
    return providerColors[provider];
}

function initMap() {
    map = L.map('map').setView([20, 0], 3);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
    }).addTo(map);

    markerLayer = L.layerGroup().addTo(map);

    fetchData();
}

function fetchData() {
    fetch('/api/data')
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(function(result) {
            if (result && result.data !== undefined) {
                allData = result.data;
                filteredData = allData;
                if (result.stale) {
                    showStaleIndicator();
                } else {
                    hideStaleIndicator();
                }
                addMarkers(allData);
                updateSidebarStats(allData);
            } else {
                loadBundledData();
            }
        })
        .catch(function(error) {
            console.error('Error loading data:', error);
            loadBundledData();
        });
}

function loadBundledData() {
    fetch('/static/data/data_centers.json')
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Bundled data not available');
            }
            return response.json();
        })
        .then(function(data) {
            allData = data;
            filteredData = allData;
            showStaleIndicator();
            addMarkers(allData);
            updateSidebarStats(allData);
        })
        .catch(function(error) {
            console.error('Error loading bundled data:', error);
            allData = [];
            filteredData = [];
            addMarkers([]);
            updateSidebarStats([]);
        });
}

function showStaleIndicator() {
    var indicator = document.getElementById('stale-indicator');
    if (indicator) {
        indicator.classList.remove('hidden');
    }
}

function hideStaleIndicator() {
    var indicator = document.getElementById('stale-indicator');
    if (indicator) {
        indicator.classList.add('hidden');
    }
}

function isFlockCamera(dc) {
    if (dc.provider === 'Flock Security') return true;
    if (dc.services && dc.services.indexOf('camera') !== -1) return true;
    return false;
}

function removeCameraCones() {
    if (cameraConesLayer) {
        map.removeLayer(cameraConesLayer);
        cameraConesLayer.clearLayers();
        cameraConesLayer = null;
    }
    if (coneUpdateRAF) {
        cancelAnimationFrame(coneUpdateRAF);
        coneUpdateRAF = null;
    }
}

function debounceAddCameraCones() {
    if (coneDebounceTimer) {
        clearTimeout(coneDebounceTimer);
    }
    if (coneUpdateRAF) {
        cancelAnimationFrame(coneUpdateRAF);
    }
    coneDebounceTimer = setTimeout(function() {
        addCameraCones();
    }, CONE_DEBOUNCE_MS);
}

function addCameraCones() {
    if (!map) return;
    if (!conesEnabled) return;
    if (currentFilters.mode !== 'flockcameras') return;
    if (map.getZoom() < 6) {
        removeCameraCones();
        return;
    }

    requestAnimationFrame(function() {
        cameraConesLayer = L.layerGroup();
        var bounds = map.getBounds();

        for (var i = 0; i < filteredData.length; i++) {
            var dc = filteredData[i];
            if (!isFlockCamera(dc)) continue;
            if (dc.bearing === undefined) continue;

            var lat = dc.latitude;
            var lng = dc.longitude;

            if (!bounds.contains([lat, lng])) continue;

            var coneColor = getProviderColor(dc.provider);
            var fov = dc.field_of_view || 60;
            var bearingRad = (dc.bearing * Math.PI) / 180;
            var leftBearingRad = ((dc.bearing - fov / 2) * Math.PI) / 180;
            var rightBearingRad = ((dc.bearing + fov / 2) * Math.PI) / 180;
            var tipOffset = Math.max(0.001, 0.003 * (18 - map.getZoom()));

            var base1Lat = lat + tipOffset * 2 * Math.cos(leftBearingRad);
            var base1Lng = lng + tipOffset * 2 * Math.sin(leftBearingRad) / Math.cos(lat * Math.PI / 180);

            var base2Lat = lat + tipOffset * 2 * Math.cos(rightBearingRad);
            var base2Lng = lng + tipOffset * 2 * Math.sin(rightBearingRad) / Math.cos(lat * Math.PI / 180);

            var cone = L.polygon([
                [lat, lng],
                [base1Lat, base1Lng],
                [base2Lat, base2Lng]
            ], {
                fillColor: coneColor,
                fillOpacity: 0.25,
                color: coneColor,
                weight: 1,
                opacity: 0.5
            });

            cameraConesLayer.addLayer(cone);
        }

        map.addLayer(cameraConesLayer);
        coneUpdateRAF = null;
    });
}

function getFilteredData(data, mode) {
    if (mode === 'flockcameras') {
        return data.filter(function(dc) { return isFlockCamera(dc); });
    }
    return data.filter(function(dc) { return !isFlockCamera(dc); });
}

function addMarkers(data) {
    pendingData = data;
    if (updateRAF) {
        cancelAnimationFrame(updateRAF);
    }
    updateRAF = requestAnimationFrame(function() {
        _addMarkersInternal(pendingData);
        pendingData = null;
        updateRAF = null;
    });
}

function _addMarkersInternal(data) {
      if (markerLayer) {
          map.removeLayer(markerLayer);
          markerLayer.clearLayers();
      }
      if (clusterGroup) {
          map.removeLayer(clusterGroup);
          clusterGroup.clearLayers();
      }

      markerLayer = L.layerGroup();

      var filtered = getFilteredData(data, currentFilters.mode);
      clusterGroup = L.markerClusterGroup({
          maxClusterRadius: 80,
          spiderfyOnMaxZoom: true,
          showCoverageOnHover: false,
          zoomToBoundsOnClick: true,
          disableClusteringAtZoom: 14
      });

      for (var j = 0; j < filtered.length; j++) {
         var dc = filtered[j];
         var lat = dc.latitude;
         var lng = dc.longitude;

          var color = getProviderColor(dc.provider);
          var isCamera = isFlockCamera(dc);
          var radius = isCamera ? 6 : 3;
          var borderColor = isCamera ? 'rgba(255, 200, 0, 1.0)' : 'rgba(255, 255, 255, 0.3)';
          var borderWidth = isCamera ? 2 : 1;

         var marker = L.circleMarker([lat, lng], {
             radius: radius,
             fillColor: color,
             fillOpacity: 1,
             color: borderColor,
             weight: borderWidth,
             opacity: 1
         });

         var popupContent = '<strong>' + dc.name + '</strong><br>';
         popupContent += dc.provider + ' &middot; ' + dc.city + ', ' + dc.country + '<br>';
         popupContent += dc.region;
         if (isCamera) {
             popupContent += ' &middot; ' + (dc.camera_model || 'N/A') + ' &middot; ' + (dc.resolution || 'N/A');
             popupContent += '<br>Bearing: ' + (dc.bearing !== undefined ? dc.bearing + '&deg;' : 'N/A');
             popupContent += ' &middot; FOV: ' + (dc.field_of_view || 'N/A') + '&deg;';
         } else {
             popupContent += ' &middot; ' + (dc.capacity_mw || 0) + ' MW';
         }
         marker.bindPopup(popupContent);

         marker.on('click', (function(dcData) {
             return function() {
                 showDetailPanel(dcData);
             };
         })(dc));

          if (isCamera) {
              clusterGroup.addLayer(marker);
          } else {
              markerLayer.addLayer(marker);
          }
      }

      map.addLayer(markerLayer);
      map.addLayer(clusterGroup);
      debounceAddCameraCones();
      populateLegend();
      updateSidebarStats(data);
 }

function showDetailPanel(dc) {
    var panel = document.getElementById('detail-panel');
    var title = document.getElementById('detail-title');
    var body = document.getElementById('detail-body');

    title.textContent = dc.name;

    var html = '';
    html += '<div class="detail-row"><span class="detail-label">Provider</span><span class="detail-value">' + dc.provider + '</span></div>';
    html += '<div class="detail-row"><span class="detail-label">Region</span><span class="detail-value">' + dc.region + '</span></div>';
    html += '<div class="detail-row"><span class="detail-label">City</span><span class="detail-value">' + dc.city + ', ' + dc.country + '</span></div>';
    html += '<div class="detail-row"><span class="detail-label">Coordinates</span><span class="detail-value">' + dc.latitude.toFixed(4) + ', ' + dc.longitude.toFixed(4) + '</span></div>';

    if (isFlockCamera(dc)) {
        html += '<div class="metric-row">';
        html += '<div class="metric-box"><div class="metric-label">Camera Model</div><div class="metric-value">' + (dc.camera_model || 'N/A') + '</div></div>';
        html += '<div class="metric-box"><div class="metric-label">Resolution</div><div class="metric-value">' + (dc.resolution || 'N/A') + '</div></div>';
        html += '</div>';
        html += '<div class="metric-row">';
        html += '<div class="metric-box"><div class="metric-label">Bearing</div><div class="metric-value">' + (dc.bearing !== undefined ? dc.bearing + '&deg;' : 'N/A') + '</div></div>';
        html += '<div class="metric-box"><div class="metric-label">Field of View</div><div class="metric-value">' + (dc.field_of_view || 'N/A') + '&deg;</div></div>';
        html += '</div>';
    } else {
        html += '<div class="metric-row">';
        html += '<div class="metric-box"><div class="metric-label">Capacity</div><div class="metric-value">' + dc.capacity_mw + ' MW</div></div>';
        html += '<div class="metric-box"><div class="metric-label">Uptime SLA</div><div class="metric-value">' + (dc.uptime_sla || 'N/A') + '</div></div>';
        html += '<div class="metric-box"><div class="metric-label">PUE</div><div class="metric-value">' + (dc.pue || 'N/A') + '</div></div>';
        html += '</div>';
    }

    html += '<div class="detail-row"><span class="detail-label">Launch Year</span><span class="detail-value">' + (dc.launch_year !== undefined ? dc.launch_year : 'N/A') + '</span></div>';
    html += '<div class="detail-row"><span class="detail-label">Services</span><span class="detail-value"><div class="services-list">';
    for (var i = 0; i < dc.services.length; i++) {
        var tagClass = dc.services[i] === 'camera' ? 'service-tag camera-tag' : 'service-tag';
        html += '<span class="' + tagClass + '">' + dc.services[i] + '</span>';
    }
    html += '</div></span></div>';

    body.innerHTML = html;
    panel.classList.remove('hidden');
}

function populateLegend() {
    var legendItems = document.getElementById('legend-items');
    if (!legendItems) return;
    legendItems.innerHTML = '';
    var providers = Object.keys(providerColors);
    for (var i = 0; i < providers.length; i++) {
        var item = document.createElement('div');
        item.className = 'legend-item';
        item.innerHTML = '<div class="legend-marker" style="background-color:' + providerColors[providers[i]] + ';"></div><span>' + providers[i] + '</span>';
        legendItems.appendChild(item);
    }
}

function updateSidebarStats(data) {
    var totalEl = document.getElementById('stat-total');
    var capacityEl = document.getElementById('stat-capacity');
    var camerasEl = document.getElementById('stat-cameras');
    var providersEl = document.getElementById('stat-providers');

    if (totalEl) {
        var dataCenterCount = 0;
        for (var i = 0; i < data.length; i++) {
            if (!isFlockCamera(data[i])) dataCenterCount++;
        }
        totalEl.textContent = dataCenterCount.toLocaleString();
    }
    if (capacityEl) {
        var total = 0;
        for (var j = 0; j < data.length; j++) {
            total += (data[j].capacity_mw || 0);
        }
        capacityEl.textContent = total.toLocaleString() + ' MW';
    }
    if (camerasEl) {
        var cameraCount = 0;
        for (var k = 0; k < data.length; k++) {
            if (isFlockCamera(data[k])) cameraCount++;
        }
        camerasEl.textContent = cameraCount.toLocaleString();
    }
    if (providersEl) {
        var providers = {};
        for (var m = 0; m < data.length; m++) {
            providers[data[m].provider] = true;
        }
        providersEl.textContent = Object.keys(providers).length.toLocaleString();
    }
}

function resetDetailPanel() {
    var panel = document.getElementById('detail-panel');
    if (panel) {
        panel.classList.add('hidden');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initMap();

    map.on('zoomend', function() {
        debounceAddCameraCones();
    });



    var resetBtn = document.getElementById('reset-view-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            map.setView([20, 0], 3);
        });
    }

    var coneToggleCheckbox = document.getElementById('cone-toggle-checkbox');
    if (coneToggleCheckbox) {
        coneToggleCheckbox.addEventListener('change', function() {
            conesEnabled = coneToggleCheckbox.checked;
            if (conesEnabled && currentFilters.mode === 'flockcameras') {
                debounceAddCameraCones();
            } else {
                removeCameraCones();
            }
        });
    }
});