(function () {
  'use strict';

  var initialised = false;
  var versionBannerId = 'dmriprep-version-banner';

  function parseVersionString(value) {
    if (value === null || value === undefined) {
      return null;
    }
    var raw = String(value).trim();
    if (!raw) {
      return null;
    }
    var normalized = raw.replace(/^v/i, '');
    var main = normalized;
    var suffix = '';
    var hyphenIndex = normalized.indexOf('-');
    if (hyphenIndex !== -1) {
      main = normalized.slice(0, hyphenIndex);
      suffix = normalized.slice(hyphenIndex + 1);
    }
    var directSuffix = main.match(/^(\d+(?:\.\d+)*)([a-z]+)(\d*)$/i);
    if (directSuffix) {
      main = directSuffix[1];
      suffix = directSuffix[2] + (directSuffix[3] || '');
    } else if (!suffix) {
      var trailingSuffix = normalized.match(/^(\d+(?:\.\d+)*)([a-z]+)(\d*)$/i);
      if (trailingSuffix) {
        main = trailingSuffix[1];
        suffix = trailingSuffix[2] + (trailingSuffix[3] || '');
      }
    }
    if (!/^\d+(?:\.\d+)*$/.test(main)) {
      return null;
    }
    var segments = main.split('.').map(function (part) {
      var parsed = parseInt(part, 10);
      return isNaN(parsed) ? 0 : parsed;
    });
    var prereleaseLabel = null;
    var prereleaseNumber = null;
    if (suffix) {
      var suffixMatch = suffix.match(/^([a-z]+)(\d*)$/i);
      if (suffixMatch) {
        prereleaseLabel = suffixMatch[1].toLowerCase();
        prereleaseNumber = suffixMatch[2] ? parseInt(suffixMatch[2], 10) : 0;
      } else {
        prereleaseLabel = suffix.toLowerCase();
      }
    }
    return {
      segments: segments,
      prerelease: prereleaseLabel,
      prereleaseNumber: prereleaseNumber,
      original: raw,
    };
  }

  function prereleaseWeight(label) {
    if (!label) {
      return 6;
    }
    var normalized = label.toLowerCase();
    if (normalized === 'post' || normalized === 'rev') {
      return 7;
    }
    if (normalized === 'dev') {
      return 0;
    }
    if (normalized === 'a' || normalized === 'alpha') {
      return 1;
    }
    if (normalized === 'b' || normalized === 'beta') {
      return 2;
    }
    if (normalized === 'rc' || normalized === 'c' || normalized === 'candidate') {
      return 3;
    }
    if (normalized === 'final') {
      return 5;
    }
    return 4;
  }

  function compareParsedVersions(a, b) {
    if (!a && !b) {
      return 0;
    }
    if (!a) {
      return -1;
    }
    if (!b) {
      return 1;
    }
    var maxLength = Math.max(a.segments.length, b.segments.length);
    for (var index = 0; index < maxLength; index += 1) {
      var aSegment = index < a.segments.length ? a.segments[index] : 0;
      var bSegment = index < b.segments.length ? b.segments[index] : 0;
      if (aSegment !== bSegment) {
        return aSegment - bSegment;
      }
    }
    var aWeight = prereleaseWeight(a.prerelease);
    var bWeight = prereleaseWeight(b.prerelease);
    if (aWeight !== bWeight) {
      return aWeight - bWeight;
    }
    var aNumber = a.prereleaseNumber || 0;
    var bNumber = b.prereleaseNumber || 0;
    if (aNumber !== bNumber) {
      return aNumber - bNumber;
    }
    return 0;
  }

  function compareVersionStrings(a, b) {
    if (a === b) {
      return 0;
    }
    var parsedA = parseVersionString(a);
    var parsedB = parseVersionString(b);
    if (!parsedA || !parsedB) {
      if (a === undefined || a === null) {
        return -1;
      }
      if (b === undefined || b === null) {
        return 1;
      }
      if (a > b) {
        return 1;
      }
      if (a < b) {
        return -1;
      }
      return 0;
    }
    var comparison = compareParsedVersions(parsedA, parsedB);
    if (comparison !== 0) {
      return comparison;
    }
    return 0;
  }

  function isLikelyVersionSlug(value) {
    if (!value && value !== 0) {
      return false;
    }
    var stringValue = String(value).trim();
    if (!stringValue) {
      return false;
    }
    if (/latest/i.test(stringValue)) {
      return false;
    }
    return /^(?:\d+\.)*\d+(?:[a-z]+\d*)?$/i.test(stringValue.replace(/^v/i, ''));
  }

  function isTaggedEntry(entry) {
    if (!entry) {
      return false;
    }
    if (entry.kind === 'tag' || entry.kind === 'release') {
      return true;
    }
    if (entry.kind === 'branch' || entry.kind === 'head') {
      return false;
    }
    var candidate = entry.slug || entry.version || entry.label || entry.name;
    return isLikelyVersionSlug(candidate);
  }

  function normaliseSlug(slug) {
    if (!slug && slug !== 0) {
      return null;
    }
    var value = String(slug).trim();
    if (!value) {
      return null;
    }
    if (/\.html?$/i.test(value)) {
      return null;
    }
    return value;
  }

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
    var isGitHubPages = segments[0] === 'dmriprep';
    var candidates = segments.filter(function (segment, index) {
      if (/\.html?$/i.test(segment)) {
        return false;
      }
      if (isGitHubPages && index === 0) {
        return false;
      }
      return true;
    });
    if (isGitHubPages && candidates.length) {
      return candidates[0] || null;
    }
    if (candidates.length >= 2) {
      return candidates[candidates.length - 2];
    }
    return candidates[candidates.length - 1] || null;
  }

  function getCurrentSlug() {
    var slug = null;
    if (window.READTHEDOCS_DATA && window.READTHEDOCS_DATA.version) {
      slug =
        window.READTHEDOCS_DATA.version.slug ||
        window.READTHEDOCS_DATA.version.identifier ||
        window.READTHEDOCS_DATA.version.version;
    }
    if (!slug && window.DOCUMENTATION_OPTIONS && window.DOCUMENTATION_OPTIONS.VERSION) {
      slug = window.DOCUMENTATION_OPTIONS.VERSION;
    }
    if (!slug && window.DOCUMENTATION_OPTIONS && window.DOCUMENTATION_OPTIONS.RELEASE) {
      slug = window.DOCUMENTATION_OPTIONS.RELEASE;
    }
    if (!slug) {
      slug = getCurrentSlugFromLocation();
    }
    return normaliseSlug(slug);
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
      slug =
        normaliseSlug(currentVersion.slug) ||
        normaliseSlug(currentVersion.version) ||
        normaliseSlug(currentVersion.name) ||
        null;
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

  function findLatestTaggedEntry(entries) {
    if (!entries || !entries.length) {
      return null;
    }
    var latest = null;
    entries.forEach(function (entry) {
      if (!entry || !isTaggedEntry(entry)) {
        return;
      }
      var slug = entry.slug || entry.version || entry.label || entry.name;
      if (slug && String(slug).toLowerCase() === 'latest') {
        return;
      }
      if (!latest) {
        latest = entry;
        return;
      }
      var entryKey = entry.version || entry.slug || entry.label || entry.name;
      var latestKey = latest.version || latest.slug || latest.label || latest.name;
      if (compareVersionStrings(entryKey, latestKey) > 0) {
        latest = entry;
      }
    });
    return latest;
  }

  function findLatestAlias(entries, latestTagged) {
    if (!entries || !entries.length) {
      return null;
    }
    var alias = null;
    entries.forEach(function (entry) {
      if (!entry) {
        return;
      }
      var slug = entry.slug || entry.version || entry.label || entry.name;
      if (!slug || String(slug).toLowerCase() !== 'latest') {
        return;
      }
      if (!alias) {
        alias = entry;
        return;
      }
      if (latestTagged && entry.url && latestTagged.url && entry.url === latestTagged.url) {
        alias = entry;
      }
    });
    return alias;
  }

  function removeVersionBanner() {
    var existing = document.getElementById(versionBannerId);
    if (existing && existing.parentNode) {
      existing.parentNode.removeChild(existing);
    }
  }

  function updateVersionBanner(latestTagged, currentEntry, aliasEntry) {
    if (!latestTagged || !currentEntry) {
      removeVersionBanner();
      return;
    }
    var currentSlug = currentEntry.slug || currentEntry.version || currentEntry.label || currentEntry.name;
    if (!currentSlug) {
      removeVersionBanner();
      return;
    }
    var normalizedSlug = String(currentSlug).toLowerCase();
    if (normalizedSlug === 'latest') {
      removeVersionBanner();
      return;
    }
    if (!isTaggedEntry(currentEntry)) {
      removeVersionBanner();
      return;
    }
    var currentKey = currentEntry.version || currentEntry.slug || currentEntry.label || currentEntry.name;
    var latestKey = latestTagged.version || latestTagged.slug || latestTagged.label || latestTagged.name;
    if (compareVersionStrings(currentKey, latestKey) >= 0) {
      removeVersionBanner();
      return;
    }
    var container =
      document.querySelector('.wy-nav-content .rst-content') ||
      document.querySelector('.wy-nav-content');
    if (!container) {
      removeVersionBanner();
      return;
    }
    var banner = document.getElementById(versionBannerId);
    if (!banner) {
      banner = document.createElement('div');
      banner.id = versionBannerId;
      banner.className = 'dmriprep-version-banner';
      banner.setAttribute('role', 'region');
      banner.setAttribute('aria-live', 'polite');
    }
    if (banner.parentNode !== container) {
      container.insertBefore(banner, container.firstChild || null);
    } else if (banner !== container.firstChild) {
      container.insertBefore(banner, container.firstChild);
    }
    while (banner.firstChild) {
      banner.removeChild(banner.firstChild);
    }
    var title = document.createElement('span');
    title.className = 'dmriprep-version-banner__title';
    title.textContent = 'Note';
    banner.appendChild(title);
    banner.appendChild(document.createTextNode(': You are viewing the documentation for '));

    var currentLabel = currentEntry.label || currentEntry.name || currentEntry.version || currentEntry.slug;
    var currentStrong = document.createElement('strong');
    currentStrong.textContent = currentLabel;
    banner.appendChild(currentStrong);
    banner.appendChild(document.createTextNode(', which is not the latest release. '));

    var latestLabel = latestTagged.label || latestTagged.name || latestTagged.version || latestTagged.slug;
    var latestLink = (aliasEntry && aliasEntry.url) || latestTagged.url || null;
    if (latestLink) {
      var link = document.createElement('a');
      link.href = latestLink;
      link.textContent = 'View the latest (' + latestLabel + ')';
      banner.appendChild(link);
    } else {
      var latestText = document.createElement('strong');
      latestText.textContent = 'Latest: ' + latestLabel;
      banner.appendChild(latestText);
    }
    banner.appendChild(document.createTextNode('.'));
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

      var label = document.createElement('span');
      label.className = 'rst-current-version__label';
      label.textContent = 'Other versions';
      current.appendChild(label);

      var value = document.createElement('span');
      value.className = 'rst-current-version__value';
      current.appendChild(value);

      var toggleIcon = document.createElement('span');
      toggleIcon.className = 'fa fa-chevron-down rst-current-version__toggle';
      toggleIcon.setAttribute('aria-hidden', 'true');
      current.appendChild(toggleIcon);

      var listWrapper = document.createElement('div');
      listWrapper.className = 'rst-other-versions';
      listWrapper.setAttribute('role', 'list');
      listWrapper.setAttribute('aria-label', 'Available versions');
      listWrapper.hidden = true;
      listWrapper.setAttribute('aria-hidden', 'true');
      listWrapper.style.display = 'none';

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
        if (!shouldOpen && listWrapper.contains(document.activeElement)) {
          current.focus();
        }
        flyout.classList.toggle('rst-open', shouldOpen);
        if (shouldOpen) {
          listWrapper.hidden = false;
          listWrapper.style.display = 'block';
          listWrapper.removeAttribute('aria-hidden');
        } else {
          listWrapper.hidden = true;
          listWrapper.style.display = 'none';
          listWrapper.setAttribute('aria-hidden', 'true');
        }
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
    var valueTarget = flyout.querySelector('.rst-current-version__value');
    var listContainer = flyout.querySelector('.rst-other-versions');
    var definitionList = flyout.querySelector('.rst-other-versions__list');

    var slug = null;
    var currentUrl = null;
    if (currentVersion) {
      slug =
        normaliseSlug(currentVersion.slug) ||
        normaliseSlug(currentVersion.version) ||
        normaliseSlug(currentVersion.name) ||
        null;
      currentUrl = currentVersion.url || null;
    }
    if (!slug) {
      slug = getCurrentSlug();
    }

    var entries = versions
      .map(function (entry) {
        if (!entry) {
          return null;
        }
        var entrySlug =
          normaliseSlug(entry.slug) ||
          normaliseSlug(entry.version) ||
          normaliseSlug(entry.name);
        if (!entrySlug) {
          return null;
        }
        var entryLabel = entry.label || entry.name || entry.version || entrySlug;
        if (!entryLabel) {
          return null;
        }
        var entryUrl = null;
        if (entry.urls && entry.urls.documentation) {
          entryUrl = entry.urls.documentation;
        } else if (entry.url) {
          entryUrl = entry.url;
        }
        var kind = entry.kind || entry.type || entry.category || null;
        if (kind === 'branch') {
          kind = 'head';
        }
        return {
          slug: entrySlug,
          version: entry.version || entrySlug,
          name: entry.name || entryLabel,
          label: entryLabel,
          url: entryUrl || null,
          kind: kind,
          active: false,
        };
      })
      .filter(Boolean);

    if (!entries.length) {
      removeVersionBanner();
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
      var fallbackKind = (currentVersion && currentVersion.kind) || null;
      if (!fallbackKind && currentVersion && isTaggedEntry(currentVersion)) {
        fallbackKind = 'tag';
      }
      activeEntry = {
        slug: slug,
        version: slug,
        name: slug,
        label: slug,
        url: null,
        kind: fallbackKind,
        active: true,
      };
    }

    var headerLabel = null;
    if (activeEntry) {
      headerLabel = activeEntry.label || activeEntry.name || activeEntry.version || activeEntry.slug;
    }
    if (!headerLabel && currentVersion) {
      headerLabel =
        currentVersion.label ||
        currentVersion.name ||
        currentVersion.version ||
        currentVersion.slug ||
        null;
    }
    if (!headerLabel && slug) {
      headerLabel = slug;
    }
    if (!headerLabel && entries.length) {
      headerLabel = entries[0].label;
    }
    if (labelTarget) {
      labelTarget.textContent = 'Other versions';
    }
    if (valueTarget) {
      valueTarget.textContent = headerLabel ? 'v: ' + headerLabel : '';
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
      var expanded = flyout.classList.contains('rst-open');
      if (!expanded && listContainer.contains(document.activeElement)) {
        if (currentControl) {
          currentControl.focus();
        }
      }
      if (expanded) {
        listContainer.hidden = false;
        listContainer.style.display = 'block';
        listContainer.removeAttribute('aria-hidden');
      } else {
        listContainer.hidden = true;
        listContainer.style.display = 'none';
        listContainer.setAttribute('aria-hidden', 'true');
      }
    }

    var bannerCurrent = activeEntry;
    if (!bannerCurrent && currentVersion) {
      bannerCurrent = {
        slug: currentVersion.slug || slug || null,
        version: currentVersion.version || currentVersion.slug || slug || null,
        name:
          currentVersion.name ||
          currentVersion.label ||
          currentVersion.version ||
          currentVersion.slug ||
          slug ||
          null,
        label:
          currentVersion.label ||
          currentVersion.name ||
          currentVersion.version ||
          currentVersion.slug ||
          slug ||
          null,
        url: currentVersion.url || null,
        kind: currentVersion.kind || null,
      };
    }

    var latestTagged = findLatestTaggedEntry(entries);
    var latestAlias = findLatestAlias(entries, latestTagged);
    updateVersionBanner(latestTagged, bannerCurrent, latestAlias);

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
      removeVersionBanner();
    }

    initialised = true;
  }

  function mapEntry(entry, fallbackKind, options) {
    if (entry === null || entry === undefined) {
      return null;
    }
    options = options || {};
    if (typeof entry === 'string') {
      var stringSlug = normaliseSlug(entry) || entry;
      if (!stringSlug) {
        return null;
      }
      var derivedUrl = null;
      if (options.baseUrl) {
        derivedUrl = options.baseUrl.replace(/\/?$/, '/') + stringSlug.replace(/^\/+/, '') + '/';
      }
      return {
        slug: stringSlug,
        version: stringSlug,
        name: entry,
        label: entry,
        url: derivedUrl,
        kind: fallbackKind || null,
      };
    }
    if (typeof entry !== 'object') {
      return null;
    }
    var entryUrl = null;
    if (entry.urls && entry.urls.documentation) {
      entryUrl = entry.urls.documentation;
    } else if (entry.url) {
      entryUrl = entry.url;
    }
    var rawSlug = entry.slug || entry.version || entry.name || entry.identifier;
    var slug = normaliseSlug(rawSlug) || rawSlug;
    if (!slug) {
      return null;
    }
    if (!entryUrl && options.baseUrl) {
      entryUrl = options.baseUrl.replace(/\/?$/, '/') + slug.replace(/^\/+/, '') + '/';
    }
    var label = entry.label || entry.name || entry.version || slug;
    var kind = entry.kind || entry.type || entry.category || fallbackKind || null;
    if (kind === 'branch') {
      kind = 'head';
    }
    return {
      slug: slug,
      version: entry.version || slug,
      name: entry.name || label,
      label: label,
      url: entryUrl || null,
      kind: kind,
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
    options = options || {};
    var collected = [];

    function addList(list, assumedKind) {
      if (!Array.isArray(list) || !list.length) {
        return;
      }
      list.forEach(function (entry) {
        var inferredKind = assumedKind;
        if (entry && typeof entry === 'object') {
          inferredKind = entry.kind || entry.type || entry.category || inferredKind;
        }
        var mapped = mapEntry(entry, inferredKind, options);
        if (mapped) {
          collected.push(mapped);
        }
      });
    }

    if (Array.isArray(data)) {
      addList(data, null);
    } else if (typeof data === 'object') {
      if (Array.isArray(data.versions)) {
        addList(data.versions, null);
      } else if (data.versions && typeof data.versions === 'object') {
        addList(data.versions.active, null);
        addList(data.versions.tags, 'tag');
        addList(data.versions.releases, 'tag');
        addList(data.versions.branches, 'head');
      }
      addList(data.active, null);
      addList(data.inactive, null);
      addList(data.tags, 'tag');
      addList(data.releases, 'tag');
      addList(data.branches, 'head');
      addList(data.heads, 'head');
    }

    if (!collected.length) {
      return [];
    }
    return uniqueBySlug(collected);
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
      var versions = normaliseVersions(manifest, {
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
