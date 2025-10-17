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

  function removeFallbackCurrentVersion(container) {
    var existing = container.querySelector('.dmriprep-current-version');
    if (existing && existing.parentNode === container) {
      container.removeChild(existing);
    }
  }

  function renderFallbackCurrentVersion(container, currentVersion) {
    var slug = null;
    if (currentVersion) {
      slug = currentVersion.slug || currentVersion.version || currentVersion.name || null;
    }
    if (!slug) {
      slug = getCurrentSlug();
    }
    if (!slug) {
      removeFallbackCurrentVersion(container);
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

  function renderFlyout(container, versions, currentVersion) {
    var parent = container.parentNode;
    if (!parent) {
      return false;
    }

    var existingFlyoutComponent = parent.querySelector('readthedocs-flyout');
    if (existingFlyoutComponent && existingFlyoutComponent.parentNode === parent) {
      parent.removeChild(existingFlyoutComponent);
    }

    var flyout = parent.querySelector('.dmriprep-version-flyout');
    if (!flyout) {
      flyout = document.createElement('div');
      flyout.className = 'dmriprep-version-flyout rst-versions shift-up';
      flyout.setAttribute('role', 'note');
      flyout.setAttribute('aria-label', 'versions');

      var current = document.createElement('span');
      current.className = 'rst-current-version';
      current.setAttribute('role', 'button');
      current.setAttribute('tabindex', '0');
      current.setAttribute('aria-haspopup', 'true');
      current.setAttribute('aria-expanded', 'false');

      var icon = document.createElement('span');
      icon.className = 'fa fa-book';
      icon.setAttribute('aria-hidden', 'true');
      current.appendChild(icon);

      var title = document.createElement('span');
      title.className = 'rst-current-version__title';
      title.textContent = 'Read the Docs';
      current.appendChild(title);

      var label = document.createElement('span');
      label.className = 'rst-current-version__label';
      current.appendChild(label);

      var toggleIcon = document.createElement('span');
      toggleIcon.className = 'fa fa-chevron-down rst-current-version__toggle';
      toggleIcon.setAttribute('aria-hidden', 'true');
      current.appendChild(toggleIcon);

      var listWrapper = document.createElement('div');
      listWrapper.className = 'rst-other-versions';
      listWrapper.setAttribute('role', 'list');
      listWrapper.setAttribute('aria-label', 'Available versions');
      listWrapper.hidden = true;

      var definitionList = document.createElement('dl');
      definitionList.className = 'rst-other-versions__list';
      definitionList.setAttribute('role', 'presentation');
      listWrapper.appendChild(definitionList);

      flyout.appendChild(current);
      flyout.appendChild(listWrapper);

      var listId = 'dmriprep-version-list';
      var uniqueId = listId;
      var suffix = 1;
      while (document.getElementById(uniqueId)) {
        uniqueId = listId + '-' + suffix;
        suffix += 1;
      }
      listWrapper.id = uniqueId;
      current.setAttribute('aria-controls', uniqueId);

      if (container.nextSibling) {
        parent.insertBefore(flyout, container.nextSibling);
      } else {
        parent.appendChild(flyout);
      }

      var toggleFlyout = function (forceOpen) {
        var shouldOpen = typeof forceOpen === 'boolean' ? forceOpen : !flyout.classList.contains('rst-open');
        flyout.classList.toggle('rst-open', shouldOpen);
        listWrapper.hidden = !shouldOpen;
        current.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
      };

      current.addEventListener('click', function (event) {
        event.preventDefault();
        toggleFlyout();
      });

      current.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          toggleFlyout();
        } else if (event.key === 'Escape') {
          toggleFlyout(false);
          current.focus();
        }
      });

      flyout.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
          toggleFlyout(false);
          current.focus();
        }
      });

      document.addEventListener('click', function (event) {
        if (!flyout.contains(event.target)) {
          toggleFlyout(false);
        }
      });
    }

    var currentControl = flyout.querySelector('.rst-current-version');
    var labelTarget = flyout.querySelector('.rst-current-version__label');
    var listContainer = flyout.querySelector('.rst-other-versions');
    var definitionList = flyout.querySelector('.rst-other-versions__list');

    var slug = null;
    var currentUrl = null;
    if (currentVersion) {
      slug = currentVersion.slug || currentVersion.version || currentVersion.name || null;
      currentUrl = currentVersion.url || null;
    }
    if (!slug) {
      slug = getCurrentSlug();
    }

    var entries = versions
      .map(function (entry) {
        if (!entry || !entry.url) {
          return null;
        }
        var entrySlug = entry.slug || entry.version || entry.name;
        var entryName = entry.name || entry.version || entrySlug;
        if (!entrySlug || !entryName) {
          return null;
        }
        return {
          slug: entrySlug,
          version: entry.version || entrySlug,
          name: entry.name || entryName,
          label: entryName,
          url: entry.url,
          active: false,
        };
      })
      .filter(Boolean);

    if (!entries.length) {
      return false;
    }

    var activeEntry = null;
    entries.forEach(function (entry) {
      var isActive = false;
      if (slug) {
        isActive =
          entry.slug === slug ||
          entry.version === slug ||
          entry.label === slug ||
          (entry.name && entry.name === slug);
      }
      if (!isActive && currentUrl && entry.url === currentUrl) {
        isActive = true;
      }
      if (!isActive && entry.url && window.location.href.indexOf(entry.url) === 0) {
        isActive = true;
      }
      entry.active = isActive;
      if (isActive) {
        activeEntry = entry;
      }
    });

    if (!activeEntry && slug) {
      activeEntry = { slug: slug, label: slug, url: null, active: true };
    }

    var headerLabel = (activeEntry && activeEntry.label) || slug || entries[0].label;
    if (labelTarget) {
      labelTarget.textContent = 'v: ' + headerLabel;
    }

    while (definitionList && definitionList.firstChild) {
      definitionList.removeChild(definitionList.firstChild);
    }

    if (definitionList) {
      var versionsTitle = document.createElement('dt');
      versionsTitle.textContent = 'Versions';
      definitionList.appendChild(versionsTitle);

      entries.forEach(function (entry) {
        var item = document.createElement('dd');
        item.setAttribute('role', 'listitem');
        var target = null;
        if (entry.url) {
          target = document.createElement('a');
          target.href = entry.url;
        } else {
          target = document.createElement('span');
        }
        target.textContent = entry.label;
        if (entry.active) {
          target.classList.add('current');
          if (entry.url) {
            target.setAttribute('aria-current', 'page');
          }
        }
        item.appendChild(target);
        definitionList.appendChild(item);
      });
    }

    var legacyDropdown = container.querySelector('.dmriprep-version-selector');
    if (legacyDropdown && legacyDropdown.parentNode === container) {
      container.removeChild(legacyDropdown);
    }

    if (listContainer) {
      listContainer.hidden = !flyout.classList.contains('rst-open');
    }

    if (currentControl) {
      currentControl.setAttribute('aria-expanded', flyout.classList.contains('rst-open') ? 'true' : 'false');
    }

    return true;
  }

  function renderSelector(options, currentVersion) {
    var container = document.querySelector('.wy-side-nav-search');
    if (!container) {
      console.warn('dmriprep: unable to locate sidebar container for version selector');
      return;
    }

    var rendered = false;
    if (options.length) {
      rendered = renderFlyout(container, options, currentVersion);
    }

    if (rendered) {
      removeFallbackCurrentVersion(container);
    } else {
      renderFallbackCurrentVersion(container, currentVersion);
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
