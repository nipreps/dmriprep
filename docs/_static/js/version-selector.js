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

  function renderCurrentVersion(container, currentVersion) {
    var slug = null;
    if (currentVersion) {
      slug = currentVersion.slug || currentVersion.version || currentVersion.name || null;
    }
    if (!slug) {
      slug = getCurrentSlug();
    }
    if (!slug) {
      return;
    }

    var target = container.querySelector('.dmriprep-current-version');
    if (!target) {
      target = document.createElement('div');
      target.className = 'version dmriprep-current-version';
      var searchForm = container.querySelector('form');
      if (searchForm && searchForm.parentNode === container) {
        container.insertBefore(target, searchForm);
      } else {
        container.appendChild(target);
      }
    }
    target.textContent = slug;
  }

  function renderSelector(options, currentVersion) {
    var container = document.querySelector('.wy-side-nav-search');
    if (!container) {
      console.warn('dmriprep: unable to locate sidebar container for version selector');
      return;
    }

    renderCurrentVersion(container, currentVersion);

    if (!options.length) {
      return;
    }

    var wrapper = container.querySelector('.dmriprep-version-selector');
    if (!wrapper) {
      wrapper = document.createElement('div');
      wrapper.className = 'dmriprep-version-selector';
    }

    var label = wrapper.querySelector('label');
    if (!label) {
      label = document.createElement('label');
      label.textContent = 'Versions';
      label.setAttribute('for', 'dmriprep-version-select');
      wrapper.appendChild(label);
    }

    var select = wrapper.querySelector('#dmriprep-version-select');
    if (!select) {
      select = document.createElement('select');
      select.id = 'dmriprep-version-select';
      select.addEventListener('change', function (event) {
        var target = event.target;
        if (target && target.value) {
          window.location.href = target.value;
        }
      });
      wrapper.appendChild(select);
    } else {
      while (select.firstChild) {
        select.removeChild(select.firstChild);
      }
    }

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

    if (wrapper.parentNode !== container) {
      container.appendChild(wrapper);
    }
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

  function normaliseVersions(data, options) {
    if (!data) {
      return [];
    }
    if (Array.isArray(data)) {
      return uniqueBySlug(data.map(mapEntry));
    }
    if (data.versions) {
      return normaliseVersions(data.versions.active || data.versions, options);
    }
    var legacyLists = [];
    if (data.heads) {
      legacyLists = legacyLists.concat(data.heads);
    }
    if (data.tags) {
      legacyLists = legacyLists.concat(data.tags);
    }
    if (legacyLists.length && options && options.baseUrl) {
      return uniqueBySlug(
        legacyLists.map(function (entry) {
          if (typeof entry === 'string') {
            return {
              slug: entry,
              version: entry,
              name: entry,
              url: options.baseUrl.replace(/\/?$/, '/') + entry.replace(/^\/+/, '') + '/',
            };
          }
          if (entry && typeof entry === 'object') {
            if (!entry.url && options.baseUrl) {
              var slug = entry.slug || entry.version || entry.name;
              if (slug) {
                entry = Object.assign({}, entry, {
                  url: options.baseUrl.replace(/\/?$/, '/') + slug.replace(/^\/+/, '') + '/',
                });
              }
            }
            return mapEntry(entry);
          }
          return null;
        })
      );
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

  function deriveBaseUrl(manifestUrl, currentVersion) {
    if (!manifestUrl) {
      return null;
    }
    try {
      var resolved = new URL(manifestUrl, window.location.href);
      var href = resolved.href;
      var withoutStatic = href.replace(/_static\/versions\.json[^#?]*$/, '');
      if (currentVersion && currentVersion.slug) {
        var slugPattern = new RegExp(
          currentVersion.slug.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\/?$'
        );
        if (slugPattern.test(withoutStatic)) {
          var trimmed = withoutStatic.replace(slugPattern, '');
          if (trimmed.slice(-1) !== '/') {
            trimmed += '/';
          }
          return trimmed;
        }
      }
      var lastSlash = withoutStatic.lastIndexOf('/', withoutStatic.length - 2);
      if (lastSlash !== -1) {
        return withoutStatic.slice(0, lastSlash + 1);
      }
      if (withoutStatic.slice(-1) !== '/') {
        withoutStatic += '/';
      }
      return withoutStatic;
    } catch (error) {
      console.warn('dmriprep: unable to derive base URL from manifest location', error);
    }
    var slug = (currentVersion && currentVersion.slug) || getCurrentSlug();
    if (slug) {
      var path = window.location.pathname || '';
      var slugIndex = path.indexOf('/' + slug + '/');
      if (slugIndex !== -1) {
        var prefix = path.slice(0, slugIndex + 1);
        var origin = window.location.origin || '';
        if (prefix.slice(-1) !== '/') {
          prefix += '/';
        }
        return origin + prefix;
      }
    }
    return null;
  }

  function bootstrapWithAddon(event) {
    var config = getConfigFromAddon(event);
    if (!config) {
      return false;
    }
    var versions = normaliseVersions({ versions: config.versions });
    var current = mapEntry(config.versions && config.versions.current);
    if (!versions.length) {
      if (current) {
        versions = [current];
      } else {
        return false;
      }
    }
    renderSelector(versions, current);
    return true;
  }

  function bootstrapWithManifest() {
    if (initialised) {
      return;
    }
    var manifestUrl = resolveManifestUrl();
    var currentVersion = null;
    var slug = getCurrentSlug();
    if (slug) {
      currentVersion = { slug: slug };
    }
    fetchManifest(manifestUrl).then(function (manifest) {
      if (!manifest) {
        return;
      }
      var baseUrl = deriveBaseUrl(manifestUrl, currentVersion);
      if (baseUrl) {
        console.debug('dmriprep: derived documentation base URL', baseUrl);
      } else {
        console.warn('dmriprep: unable to determine base URL for legacy manifest entries');
      }
      var versions = normaliseVersions(manifest.versions || manifest, {
        baseUrl: baseUrl,
      });
      var resolvedCurrent = deriveCurrentVersionFromList(versions);
      if (resolvedCurrent) {
        currentVersion = resolvedCurrent;
      }
      if (!versions.length && currentVersion) {
        versions = [currentVersion];
      }
      renderSelector(versions, currentVersion);
      if (versions.length) {
        console.debug('dmriprep: loaded versions manifest', versions);
      } else {
        console.warn('dmriprep: versions manifest did not include any entries');
      }
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
