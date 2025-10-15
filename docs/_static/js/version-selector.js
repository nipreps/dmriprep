(function () {
  'use strict';

  var initialised = false;

  function getConfigFromAddon(event) {
    if (!event || !event.detail || typeof event.detail.data !== 'function') {
      return null;
    }
    try {
      return event.detail.data();
    } catch (error) {
      console.warn('dmriprep: unable to read Read the Docs addon data', error);
      return null;
    }
  }

  function getCurrentSlugFromLocation() {
    var path = window.location.pathname;
    if (!path) {
      return null;
    }
    var segments = path.split('/').filter(Boolean);
    if (segments.length === 0) {
      return null;
    }
    // When hosted on GitHub Pages the pattern is /<repo>/<version>/...
    // Otherwise fall back to the first segment.
    if (segments.length >= 2 && segments[0] === 'dmriprep') {
      return segments[1];
    }
    return segments[segments.length - 2] || segments[segments.length - 1] || null;
  }

  function getCurrentSlug() {
    var slug = null;
    if (window.READTHEDOCS_DATA && window.READTHEDOCS_DATA.version) {
      slug = window.READTHEDOCS_DATA.version.slug;
    }
    if (!slug && window.DOCUMENTATION_OPTIONS && window.DOCUMENTATION_OPTIONS.VERSION) {
      slug = window.DOCUMENTATION_OPTIONS.VERSION;
    }
    if (!slug) {
      slug = getCurrentSlugFromLocation();
    }
    return slug;
  }

  function buildOption(version) {
    var option = document.createElement('option');
    option.value = version.url;
    option.textContent = version.slug || version.name || version.version;
    return option;
  }

  function renderSelector(options, currentVersion) {
    if (initialised || !options.length) {
      return;
    }
    var container = document.querySelector('.wy-side-nav-search');
    if (!container) {
      console.warn('dmriprep: unable to locate sidebar container for version selector');
      return;
    }

    var wrapper = document.createElement('div');
    wrapper.className = 'dmriprep-version-selector';

    var label = document.createElement('label');
    label.textContent = 'Versions';
    label.setAttribute('for', 'dmriprep-version-select');

    var select = document.createElement('select');
    select.id = 'dmriprep-version-select';
    select.addEventListener('change', function (event) {
      var target = event.target;
      if (target && target.value) {
        window.location.href = target.value;
      }
    });

    options.forEach(function (optionData) {
      var option = buildOption(optionData);
      if (currentVersion) {
        if (currentVersion.url && optionData.url && currentVersion.url === optionData.url) {
          option.selected = true;
        } else {
          var slug = currentVersion.slug || currentVersion.version || currentVersion.name;
          var matchesSlug = slug && (optionData.slug === slug || optionData.version === slug);
          var matchesUrl = currentVersion.url && optionData.url && currentVersion.url.indexOf(optionData.url) === 0;
          var matchesLocation = optionData.url && window.location.href.indexOf(optionData.url) === 0;
          if (matchesSlug || matchesUrl || matchesLocation) {
            option.selected = true;
          }
        }
      }
      select.appendChild(option);
    });

    wrapper.appendChild(label);
    wrapper.appendChild(select);

    container.appendChild(wrapper);
    initialised = true;
  }

  function mapEntry(entry) {
    if (!entry) {
      return null;
    }
    var url = entry.urls ? entry.urls.documentation : entry.url;
    if (!url) {
      return null;
    }
    var slug = entry.slug || entry.version || entry.name;
    return {
      slug: slug,
      url: url,
      version: entry.version || slug,
      name: entry.name || slug || entry.version,
    };
  }

  function uniqueBySlug(entries) {
    var seen = new Set();
    return entries.filter(function (entry) {
      if (!entry) {
        return false;
      }
      var identifier = entry.slug || entry.version || entry.name;
      if (!identifier || seen.has(identifier)) {
        return false;
      }
      seen.add(identifier);
      return true;
    });
  }

  function normaliseVersions(data) {
    if (!data) {
      return [];
    }
    if (Array.isArray(data)) {
      return uniqueBySlug(data.map(mapEntry));
    }
    if (data.versions) {
      return normaliseVersions(data.versions.active || data.versions);
    }
    return [];
  }

  function deriveCurrentVersionFromList(versions) {
    if (!versions || !versions.length) {
      return null;
    }
    var href = window.location.href;
    var slug = getCurrentSlug();
    var bestMatch = null;
    var longestPrefix = -1;
    versions.forEach(function (entry) {
      if (!entry) {
        return;
      }
      if (!bestMatch && slug && (entry.slug === slug || entry.version === slug)) {
        bestMatch = entry;
      }
      if (entry.url && href.indexOf(entry.url) === 0 && entry.url.length > longestPrefix) {
        bestMatch = entry;
        longestPrefix = entry.url.length;
      }
    });
    return bestMatch || (slug ? { slug: slug } : null);
  }

  function fetchManifest(manifestUrl) {
    return fetch(manifestUrl, { cache: 'no-cache' })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Failed to load manifest: ' + response.status);
        }
        return response.json();
      })
      .catch(function (error) {
        console.warn('dmriprep: unable to fetch versions manifest', error);
        return null;
      });
  }

  function resolveManifestUrl() {
    var script = document.querySelector('script[data-url_root]');
    var base = null;
    if (script) {
      base = script.getAttribute('data-url_root');
    }
    if (!base && window.DOCUMENTATION_OPTIONS) {
      base = window.DOCUMENTATION_OPTIONS.URL_ROOT;
    }
    base = base || './';
    if (base.slice(-1) !== '/') {
      base += '/';
    }
    return base + '_static/versions.json';
  }

  function bootstrapWithAddon(event) {
    var config = getConfigFromAddon(event);
    if (!config) {
      return false;
    }
    var versions = normaliseVersions({ versions: config.versions });
    var current = mapEntry(config.versions && config.versions.current);
    if (!versions.length) {
      return false;
    }
    renderSelector(versions, current);
    return true;
  }

  function bootstrapWithManifest() {
    if (initialised) {
      return;
    }
    var manifestUrl = resolveManifestUrl();
    fetchManifest(manifestUrl).then(function (manifest) {
      if (!manifest) {
        return;
      }
      var versions = normaliseVersions(manifest.versions || manifest);
      var current = deriveCurrentVersionFromList(versions);
      renderSelector(versions, current);
    });
  }

  document.addEventListener('readthedocs-addons-data-ready', function (event) {
    if (!bootstrapWithAddon(event)) {
      bootstrapWithManifest();
    }
  });

  // Fallback for environments where the Read the Docs addon event is not fired.
  window.addEventListener('DOMContentLoaded', function () {
    if (!initialised) {
      bootstrapWithManifest();
    }
  });
})();
