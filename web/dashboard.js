(function () {
  "use strict";

  function parseFragment() {
    var raw = window.location.hash.replace(/^#/, "");
    var values = {};
    if (raw === "overview" || raw === "config") {
      values.view = raw;
      return values;
    }
    raw.split("&").forEach(function (part) {
      var pieces = part.split("=");
      if (!pieces[0]) {
        return;
      }
      try {
        values[decodeURIComponent(pieces[0])] = decodeURIComponent(pieces.slice(1).join("="));
      } catch (error) {
        return;
      }
    });
    return values;
  }

  function readSessionToken() {
    try {
      return window.sessionStorage.getItem("ddns-dashboard-token") || "";
    } catch (error) {
      return "";
    }
  }

  function storeSessionToken(value) {
    try {
      window.sessionStorage.setItem("ddns-dashboard-token", value);
      return true;
    } catch (error) {
      return false;
    }
  }

  function fragmentForView(view, accessToken) {
    var encodedView = encodeURIComponent(view);
    return accessToken
      ? "#token=" + encodeURIComponent(accessToken) + "&view=" + encodedView
      : "#" + encodedView;
  }

  var launch = parseFragment();
  var token = launch.token || readSessionToken();
  var initialView = launch.view === "config" ? "config" : "overview";
  if (launch.token) {
    storeSessionToken(launch.token);
  } else if (token) {
    window.history.replaceState(null, "", fragmentForView(initialView, token));
  }
  var app = document.getElementById("app");
  var state = {
    dashboard: null,
    configModel: null,
    config: null,
    originalConfig: null,
    configPath: "",
    configExists: false,
    backupAvailable: false,
    profileIndex: 0,
    dirty: false,
    jsonDirty: false,
    jsonBaseline: "",
    repairRequired: false,
    invalidRawConfig: null,
    saving: false,
    activityFilter: "all",
    recordQuery: "",
    toastTimer: null,
    toastExitTimer: null,
    restoreTimer: null,
    restoreArmed: false,
    deleteTimer: null,
    deleteArmed: false,
    setupOpened: false,
    sectionFingerprints: null,
    dashboardRefreshTimer: null,
    schedulerIntervalDirty: false,
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function make(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined && text !== null) {
      node.textContent = text;
    }
    return node;
  }

  function makeIcon(name) {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    var use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    svg.setAttribute("aria-hidden", "true");
    use.setAttribute("href", "#icon-" + name);
    svg.appendChild(use);
    return svg;
  }

  function clear(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function setText(id, value) {
    byId(id).textContent = value;
  }

  function errorMessage(error) {
    if (error && error.code === "invalid_token") {
      return "访问凭据无效，请使用 ddns web 输出的新链接重新打开。";
    }
    return error && error.message ? error.message : "请求失败，请检查控制台进程后重试。";
  }

  function api(path, options) {
    var request = options || {};
    var method = request.method || "GET";
    var headers = { Accept: "application/json", "X-DDNS-Token": token };
    var init = {
      method: method,
      headers: headers,
      credentials: "same-origin",
    };

    if (method !== "GET" && method !== "HEAD") {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(request.body || {});
    }

    return fetch(path, init).then(function (response) {
      return response.text().then(function (body) {
        var payload = {};
        if (body) {
          try {
            payload = JSON.parse(body);
          } catch (parseError) {
            throw new Error("控制台返回了无法解析的数据。");
          }
        }
        if (!response.ok) {
          var detail = payload.error;
          var requestError = new Error(
            detail && detail.message ? detail.message : "请求失败（" + response.status + "）。",
          );
          requestError.code = detail && detail.code ? detail.code : "request_failed";
          throw requestError;
        }
        return payload;
      });
    });
  }

  function hideToast() {
    var toast = byId("toast");
    clearTimeout(state.toastTimer);
    clearTimeout(state.toastExitTimer);
    toast.classList.remove("visible");
    state.toastExitTimer = setTimeout(function () {
      toast.hidden = true;
    }, 180);
  }

  function showToast(message, tone) {
    var toast = byId("toast");
    clearTimeout(state.toastTimer);
    clearTimeout(state.toastExitTimer);
    toast.className = "toast" + (tone ? " " + tone : "");
    setText("toast-message", message);
    toast.hidden = false;
    void toast.offsetWidth;
    toast.classList.add("visible");
    state.toastTimer = setTimeout(function () {
      hideToast();
    }, 3600);
  }

  function setNotice(message, tone) {
    var notice = byId("config-notice");
    notice.className = "config-notice" + (tone ? " " + tone : "");
    notice.textContent = message || "";
    notice.hidden = !message;
  }

  function hasPendingChanges() {
    return state.dirty || state.jsonDirty;
  }

  function setJsonEditorValue(value) {
    var editor = byId("json-editor");
    editor.value = value;
    state.jsonBaseline = value;
    state.jsonDirty = false;
  }

  function updateJsonDirtyState() {
    state.jsonDirty = byId("json-editor").value !== state.jsonBaseline;
    updateDirtyState();
  }

  function updateStructuredControls() {
    var disabled = state.repairRequired || state.jsonDirty || state.saving;
    var selector = [
      "#profile-select",
      "#add-profile-button",
      "#delete-profile-button",
      "#provider-pane input",
      "#provider-pane select",
      "#provider-pane button",
      "#domains-pane input",
      "#domains-pane button",
      "#network-pane input",
      "#network-pane select",
      "#network-pane textarea",
      "#network-pane button",
      "#scheduler-interval",
      "#automation-button",
    ].join(",");
    document.querySelectorAll(selector).forEach(function (control) {
      control.disabled = disabled;
    });
  }

  function setBusy(isBusy) {
    app.classList.toggle("busy", isBusy);
  }

  function getStoredTheme() {
    try {
      return window.localStorage.getItem("ddns-dashboard-theme");
    } catch (error) {
      return null;
    }
  }

  function applyTheme(theme) {
    var dark = theme === "dark";
    app.classList.toggle("dark", dark);
    document.body.classList.toggle("dark-theme", dark);
    byId("theme-button").setAttribute("aria-label", dark ? "切换浅色模式" : "切换深色模式");
    try {
      window.localStorage.setItem("ddns-dashboard-theme", dark ? "dark" : "light");
    } catch (error) {
      return;
    }
  }

  function initialTheme() {
    var stored = getStoredTheme();
    if (stored) {
      return stored;
    }
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function setActiveNavigation(name) {
    ["overview", "config"].forEach(function (viewName) {
      var button = byId("nav-" + viewName);
      var active = viewName === name;
      button.classList.toggle("active", active);
      if (active) {
        button.setAttribute("aria-current", "page");
      } else {
        button.removeAttribute("aria-current");
      }
    });
    document.querySelector(".command-nav").classList.toggle("config-active", name === "config");
  }

  function setView(name, updateHash, shouldScroll) {
    var target = byId(name);
    if (!target) {
      return;
    }
    if (name === "config") {
      byId("config-shell").open = true;
    }
    setActiveNavigation(name);
    var nextFragment = fragmentForView(name, token);
    if (updateHash && window.location.hash !== nextFragment) {
      window.history.replaceState(null, "", nextFragment);
    }
    if (shouldScroll !== false) {
      var reduceMotion =
        window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      target.scrollIntoView({
        behavior: updateHash && !reduceMotion ? "smooth" : "auto",
        block: "start",
      });
    }
  }

  function isHealthyProductionConfiguration() {
    var dashboard = state.dashboard || {};
    var productionProviders = (dashboard.providers || []).filter(function (provider) {
      return provider.id !== "debug" && Number(provider.records || 0) > 0;
    });
    return (
      dashboard.state === "synced" &&
      productionProviders.length > 0 &&
      productionProviders.every(function (provider) {
        return provider.status === "synced";
      })
    );
  }

  function renderConfigSummary() {
    var dashboard = state.dashboard || {};
    var providers = dashboard.providers || [];
    var productionProviders = providers.filter(function (provider) {
      return provider.id !== "debug";
    });
    var summaryProviders = productionProviders.length ? productionProviders : providers;
    var recordCount = summaryProviders.reduce(function (sum, provider) {
      return sum + Number(provider.records || 0);
    }, 0);
    var providerText =
      summaryProviders.length === 1
        ? summaryProviders[0].label || summaryProviders[0].id
        : summaryProviders.length + " 个 DNS 服务商";
    var title = summaryProviders.length
      ? providerText + " · " + recordCount + " 条解析"
      : "尚未配置 DNS 服务商";
    var configPath = state.configPath || dashboard.config_path || "";
    var configName = configPath ? configPath.split(/[\\/]/).pop() : "本机配置";
    var scheduler = dashboard.scheduler || {};
    var schedulerText = "";
    if (scheduler.conflict) {
      schedulerText = "自动同步存在冲突";
    } else if (scheduler.enabled) {
      schedulerText = "每 " + scheduler.interval + " 分钟自动同步";
    } else if (scheduler.scheduler) {
      schedulerText = "自动同步已暂停";
    }
    setText("config-summary-title", title);
    setText("config-summary-detail", [configName, schedulerText].filter(Boolean).join(" · "));

    var status = byId("config-summary-status");
    var statusText = "读取中";
    var tone = "";
    if (state.repairRequired) {
      statusText = "需要修复";
      tone = "error";
    } else if (hasPendingChanges()) {
      statusText = "有未保存修改";
      tone = "attention";
    } else if (dashboard.state === "error") {
      statusText = "同步异常";
      tone = "error";
    } else if (isHealthyProductionConfiguration()) {
      statusText = "运行正常";
      tone = "success";
    } else if (
      providers.length &&
      providers.every(function (provider) {
        return provider.id === "debug";
      })
    ) {
      statusText = "调试配置";
      tone = "attention";
    } else if (dashboard.state === "ready") {
      statusText = "等待首次同步";
      tone = "attention";
    } else if (dashboard.state === "unconfigured") {
      statusText = "尚未配置";
      tone = "attention";
    }
    status.className = "config-summary-status" + (tone ? " " + tone : "");
    status.querySelector("span").textContent = statusText;
  }

  function initializeConfigSections() {
    if (!window.matchMedia) {
      return;
    }
    var media = window.matchMedia("(max-width: 720px)");
    var applyLayout = function (compact) {
      document.querySelectorAll(".config-pane").forEach(function (pane, index) {
        pane.open = compact ? index === 0 : true;
      });
    };
    applyLayout(media.matches);
    var handleChange = function (event) {
      applyLayout(event.matches);
    };
    if (media.addEventListener) {
      media.addEventListener("change", handleChange);
    } else if (media.addListener) {
      media.addListener(handleChange);
    }
    document.querySelectorAll(".config-pane > summary").forEach(function (summary) {
      summary.addEventListener("click", function (event) {
        if (!media.matches) {
          event.preventDefault();
        }
      });
    });
  }

  function initializeConfigShell() {
    var requestedConfigView = parseFragment().view === "config";
    byId("config-shell").open =
      requestedConfigView || state.repairRequired || !isHealthyProductionConfiguration();
  }

  function formatTime(value) {
    if (!value) {
      return "—";
    }
    var date = typeof value === "number" ? new Date(value * 1000) : new Date(value);
    if (isNaN(date.getTime())) {
      return "—";
    }
    var today = new Date();
    var sameDay =
      today.getFullYear() === date.getFullYear() &&
      today.getMonth() === date.getMonth() &&
      today.getDate() === date.getDate();
    var time = date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", hour12: false });
    if (sameDay) {
      return time;
    }
    return (
      String(date.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(date.getDate()).padStart(2, "0") +
      " " +
      time
    );
  }

  function dashboardStateCopy(dashboard) {
    if (dashboard.state === "error") {
      return {
        title: "最近同步失败",
        summary: dashboard.message || "检查运行记录后重试同步。",
        tone: "error",
        header: "同步失败",
      };
    }
    if (dashboard.state === "synced") {
      return {
        title: "解析状态稳定",
        summary: dashboard.last_sync
          ? "最近同步于 " + formatTime(dashboard.last_sync) + "，本机缓存可用。"
          : "解析记录与本机配置保持一致。",
        tone: "",
        header: "运行正常",
      };
    }
    if (dashboard.state === "ready") {
      return {
        title: "配置已就绪",
        summary: "运行一次同步后，这里会显示地址与解析结果。",
        tone: "attention",
        header: "等待同步",
      };
    }
    return {
      title: "配置这台设备",
      summary: "选择 DNS 服务商并添加域名；保存后再主动运行首次同步。",
      tone: "attention",
      header: "尚未配置",
    };
  }

  function isFirstRun() {
    return Boolean(state.dashboard && state.dashboard.state === "unconfigured");
  }

  function renderSetupMode() {
    var firstRun = isFirstRun();
    var syncButton = byId("sync-button");
    var overviewNav = byId("nav-overview");
    app.classList.toggle("first-run", firstRun);
    byId("overview").hidden = firstRun;
    overviewNav.disabled = firstRun;
    overviewNav.setAttribute("aria-disabled", String(firstRun));
    overviewNav.title = firstRun ? "保存配置后可查看运行状态" : "";
    document.querySelector(".brand").disabled = firstRun;
    byId("runtime-overview").hidden = firstRun;
    byId("runtime-ledger").hidden = firstRun;
    byId("scheduler-button").hidden = firstRun;
    byId("setup-brief").hidden = !firstRun;
    setText("topology-address-label", firstRun ? "步骤 1" : "本机地址");
    setText("topology-provider-label", firstRun ? "步骤 2" : "DNS 服务商");
    setText("topology-record-label", firstRun ? "步骤 3" : "解析记录");
    setText("config-title", firstRun ? (state.configExists ? "完成配置" : "首次配置") : "配置管理");
    setText(
      "config-description",
      firstRun
        ? "完成服务商与域名设置；保存前所有修改只保留在当前页面。"
        : "维护本机正在使用的配置；未填写的字段继续继承环境变量或默认值。",
    );
    setText("setup-title", state.configExists ? "完成这份配置" : "配置这台设备");
    setText("setup-path", state.configPath || (state.dashboard && state.dashboard.config_path) || "config.json");
    syncButton.querySelector("span").textContent = firstRun ? "开始配置" : "立即同步";
    syncButton.querySelector("use").setAttribute("href", firstRun ? "#icon-plus" : "#icon-sync");
  }

  function makeSettingsRow(options) {
    var row = make("div", "settings-row");
    var badge = make("span", "setting-icon " + (options.tone || "blue"));
    if (options.icon) {
      badge.appendChild(makeIcon(options.icon));
    } else {
      badge.textContent = options.badge || "DNS";
    }
    var copyNode = make("span", "setting-copy");
    copyNode.appendChild(make("strong", "", options.title));
    copyNode.appendChild(make("small", "", options.subtitle));
    row.appendChild(badge);
    row.appendChild(copyNode);
    row.appendChild(make("code", "", options.value || "—"));
    var status = make("span", "connected-state" + (options.statusTone ? " " + options.statusTone : ""));
    status.appendChild(make("i"));
    status.appendChild(document.createTextNode(options.status || "可用"));
    row.appendChild(status);
    return row;
  }

  function renderAddresses(dashboard) {
    var list = byId("address-list");
    var addresses = dashboard.addresses || [];
    clear(list);
    setText("address-count", addresses.length + " 个可用");

    if (!addresses.length) {
      var empty = make("div", "native-empty");
      empty.appendChild(make("strong", "", "尚无地址缓存"));
      empty.appendChild(make("span", "", "完成一次同步后显示实际 IPv4 / IPv6 地址"));
      list.appendChild(empty);
      return;
    }

    addresses.forEach(function (address) {
      var isV6 = address.family === "IPv6";
      list.appendChild(
        makeSettingsRow({
          icon: "globe",
          tone: isV6 ? "violet" : "blue",
          title: address.family,
          subtitle: "最近同步缓存",
          value: address.value,
          status: "可用",
        }),
      );
    });
  }

  function cacheDescription() {
    if (!state.config) {
      return "读取中";
    }
    if (state.config.cache === false) {
      return "已关闭";
    }
    if (typeof state.config.cache === "string") {
      return "自定义路径";
    }
    return "已启用";
  }

  function renderRuntime(dashboard) {
    var list = byId("runtime-list");
    var providers = dashboard.providers || [];
    clear(list);
    setText("runtime-count", providers.length ? providers.length + " 个服务商" : "本机");

    providers.forEach(function (provider) {
      var failed = provider.status === "error";
      var synced = provider.status === "synced";
      list.appendChild(
        makeSettingsRow({
          badge: String(provider.label || provider.id).slice(0, 3).toUpperCase(),
          title: provider.label || provider.id,
          subtitle: provider.records + " 条已配置记录",
          value: provider.id,
          status: failed ? "同步失败" : synced ? "已同步" : "已配置",
          statusTone: failed ? "error" : synced ? "" : "attention",
        }),
      );
    });

    list.appendChild(
      makeSettingsRow({
        icon: "shield",
        tone: "blue",
        title: "本地缓存",
        subtitle: "避免地址未变化时重复请求",
        value: state.config && state.config.cache === false ? "OFF" : "ON",
        status: cacheDescription(),
        statusTone: state.config && state.config.cache === false ? "muted" : "",
      }),
    );
  }

  function makeRecordRow(record) {
    var row = make("div", "record-row");
    row.appendChild(make("span", "record-type", record.type || "A"));
    var copyNode = make("span", "setting-copy");
    copyNode.appendChild(make("strong", "", record.domain));
    copyNode.appendChild(make("small", "", record.provider));
    row.appendChild(copyNode);
    row.appendChild(make("code", "", record.value));
    var status = make("span", "connected-state");
    status.appendChild(make("i"));
    status.appendChild(document.createTextNode("已同步"));
    row.appendChild(status);
    return row;
  }

  function renderRecords() {
    var list = byId("record-list");
    var records = (state.dashboard && state.dashboard.records) || [];
    var search = byId("record-search");
    var searchable = records.length > 5;
    byId("record-search-field").hidden = !searchable;
    if (!searchable) {
      state.recordQuery = "";
      search.value = "";
    }
    var query = state.recordQuery.toLowerCase();
    var filtered = records.filter(function (record) {
      return !query || (record.domain + " " + record.value + " " + record.provider).toLowerCase().indexOf(query) >= 0;
    });
    clear(list);
    setText("record-count", records.length + " 条");

    if (!filtered.length) {
      var empty = make("div", "native-empty");
      empty.appendChild(make("strong", "", query ? "没有匹配的解析记录" : "暂无解析记录"));
      empty.appendChild(
        make("span", "", query ? "尝试更短的域名或地址关键词" : "完成一次同步后会显示本机缓存结果"),
      );
      list.appendChild(empty);
      return;
    }
    filtered.forEach(function (record) {
      list.appendChild(makeRecordRow(record));
    });
  }

  function isAttentionActivity(activity) {
    var level = String(activity.level || "").toUpperCase();
    return level === "WARN" || level === "WARNING" || level === "ERROR" || level === "CRITICAL";
  }

  function renderActivities() {
    var list = byId("activity-list");
    var activities = (state.dashboard && state.dashboard.activities) || [];
    var filter = byId("activity-filter");
    filter.hidden = activities.length <= 5;
    if (filter.hidden && state.activityFilter !== "all") {
      state.activityFilter = "all";
      filter.querySelectorAll("button").forEach(function (button) {
        button.classList.toggle("active", button.getAttribute("data-activity-filter") === "all");
      });
    }
    var filtered = activities.filter(function (activity) {
      return state.activityFilter === "all" || isAttentionActivity(activity);
    });
    clear(list);
    setText("activity-count", activities.length + " 项");

    if (!filtered.length) {
      var empty = make("li", "native-empty");
      var copyNode = make("div");
      copyNode.appendChild(make("strong", "", state.activityFilter === "all" ? "暂无活动" : "没有需要关注的活动"));
      copyNode.appendChild(make("small", "", "同步与调度结果会记录在这里"));
      empty.appendChild(copyNode);
      list.appendChild(empty);
      return;
    }

    filtered.slice(0, 20).forEach(function (activity) {
      var attention = isAttentionActivity(activity);
      var item = make("li");
      item.appendChild(make("time", "", formatTime(activity.timestamp)));
      item.appendChild(make("span", "event-badge " + (attention ? "warn" : "info"), attention ? "需关注" : "完成"));
      item.appendChild(make("span", "event-source", activity.source || "DDNS"));
      var copyNode = make("div");
      copyNode.appendChild(make("strong", "", activity.message || "操作完成"));
      copyNode.appendChild(make("small", "", activity.detail || "本机控制台"));
      item.appendChild(copyNode);
      list.appendChild(item);
    });
  }

  function renderScheduler(dashboard) {
    var scheduler = dashboard.scheduler || {};
    var enabled = Boolean(scheduler.enabled);
    var conflict = Boolean(scheduler.conflict);
    var interval = scheduler.interval ? " · 每 " + scheduler.interval + " 分钟" : "";
    var nextRun = scheduler.next_run ? " · 下次 " + formatTime(scheduler.next_run) : "";
    byId("scheduler-button").classList.toggle("attention", conflict);
    byId("automation-button").closest(".automation-card").classList.toggle("attention", conflict);

    if (conflict) {
      setText("scheduler-action", "接管自动同步");
      setText("scheduler-title", (scheduler.external_scheduler || "系统") + " 外部任务仍在运行");
      setText("automation-title", "检测到外部调度冲突");
      setText("automation-detail", "停用外部任务后由当前 Web 进程接管，避免重复更新。");
      setText("automation-button", "接管");
    } else if (enabled) {
      setText("scheduler-action", "暂停自动同步");
      setText("scheduler-title", "Web 内置调度运行中" + interval);
      setText("automation-title", scheduler.running ? "正在执行自动同步" : "Web 自动同步已启用");
      setText(
        "automation-detail",
        scheduler.last_error ? "最近一次失败：" + scheduler.last_error : "当前进程负责周期同步" + nextRun,
      );
      setText("automation-button", "暂停");
    } else {
      setText("scheduler-action", "恢复自动同步");
      setText("scheduler-title", "Web 内置调度已暂停" + interval);
      setText("automation-title", "Web 自动同步已暂停");
      setText("automation-detail", "仅暂停当前进程；重启后按启动间隔恢复。");
      setText("automation-button", "恢复");
    }
    var input = byId("scheduler-interval");
    if (scheduler.interval && document.activeElement !== input && !state.schedulerIntervalDirty) {
      input.value = scheduler.interval;
    }
    updateSchedulerButton();
  }

  function updateSchedulerButton() {
    var scheduler = (state.dashboard && state.dashboard.scheduler) || {};
    var interval = Number(byId("scheduler-interval").value || 0);
    if (scheduler.conflict) {
      setText("automation-button", "接管");
    } else if (state.schedulerIntervalDirty) {
      setText("automation-button", "保存后生效");
    } else if (interval && interval !== Number(scheduler.interval)) {
      setText("automation-button", "应用");
    } else {
      setText("automation-button", scheduler.enabled ? "暂停" : "恢复");
    }
  }

  function dashboardFingerprints(dashboard) {
    var scheduler = dashboard.scheduler || {};
    return {
      addresses: JSON.stringify(dashboard.addresses || []),
      runtime: JSON.stringify([
        dashboard.providers || [],
        {
          enabled: scheduler.enabled,
          interval: scheduler.interval,
          conflict: scheduler.conflict,
          running: scheduler.running,
          last_run: scheduler.last_run,
          last_error: scheduler.last_error,
        },
      ]),
      records: JSON.stringify(dashboard.records || []),
      activities: JSON.stringify((dashboard.activities || []).slice(0, 8)),
    };
  }

  function replayCue(element, className, duration) {
    if (!element) {
      return;
    }
    var timerName = "__" + className + "Timer";
    clearTimeout(element[timerName]);
    element.classList.remove(className);
    void element.offsetWidth;
    element.classList.add(className);
    element[timerName] = setTimeout(function () {
      element.classList.remove(className);
    }, duration);
  }

  function cueDashboardChanges(previous, current) {
    if (!previous) {
      return;
    }
    var targets = {
      addresses: document.querySelector("#runtime-overview .settings-section:first-child"),
      runtime: document.querySelector("#runtime-overview .settings-section:last-child"),
      records: document.querySelector(".records-section"),
      activities: document.querySelector(".activity-section"),
    };
    Object.keys(current).forEach(function (name) {
      if (current[name] !== previous[name]) {
        replayCue(targets[name], "data-updated", 640);
      }
    });
  }

  function cueSyncOutcome(tone) {
    var hero = byId("status-hero");
    hero.classList.remove("syncing");
    replayCue(hero, tone === "error" ? "sync-failed" : "sync-complete", 760);
  }

  function cuePersistedConfig() {
    replayCue(byId("save-state"), "confirmed", 560);
  }

  function setSaveButtonLabels(label) {
    byId("save-button").textContent = label;
    byId("footer-save-button").textContent = label;
  }

  function renderDashboard() {
    var dashboard = state.dashboard;
    if (!dashboard) {
      return;
    }
    var fingerprints = dashboardFingerprints(dashboard);
    var previousFingerprints = state.sectionFingerprints;
    var copy = dashboardStateCopy(dashboard);
    var providers = dashboard.providers || [];
    var addresses = dashboard.addresses || [];
    var configuredRecords = providers.reduce(function (sum, provider) {
      return sum + Number(provider.records || 0);
    }, 0);
    var header = byId("header-health");
    var hero = byId("status-hero");
    var firstRun = dashboard.state === "unconfigured";
    header.className = "header-health" + (copy.tone ? " " + copy.tone : "");
    header.removeAttribute("title");
    hero.className = "status-hero" + (copy.tone ? " " + copy.tone : "");
    header.querySelector("span").textContent = copy.header;
    setText("status-title", copy.title);
    setText("status-summary", copy.summary);
    setText("topology-addresses", firstRun ? "选择服务商" : addresses.length);
    setText("topology-providers", firstRun ? "添加域名" : providers.length);
    setText("topology-records", firstRun ? "保存后同步" : configuredRecords);

    var latest = (dashboard.activities || [])[0];
    setText("latest-time", firstRun ? "未写入" : latest ? formatTime(latest.timestamp) : "—");
    setText("latest-title", firstRun ? "从下方的真实配置表单开始" : latest ? latest.message : "等待首次同步");
    setText(
      "latest-detail",
      firstRun
        ? (state.configPath || dashboard.config_path || "config.json") + " · 保存前不会修改磁盘"
        : latest
          ? latest.detail || latest.source
          : "运行结果会自动汇集在这里",
    );

    renderSetupMode();
    renderAddresses(dashboard);
    renderRuntime(dashboard);
    renderRecords();
    renderActivities();
    renderScheduler(dashboard);
    renderConfigSummary();
    state.sectionFingerprints = fingerprints;
    cueDashboardChanges(previousFingerprints, fingerprints);
  }

  function providerCatalog() {
    return configModel().providers;
  }

  function configModel() {
    if (!state.configModel) {
      throw new Error("配置字段模型尚未加载。");
    }
    return state.configModel;
  }

  function providerMetadata(providerId) {
    return providerCatalog().filter(function (provider) {
      return provider.id === providerId;
    })[0];
  }

  function providerLabel(providerId) {
    var found = providerMetadata(providerId);
    return found ? found.name : providerId || "未命名服务商";
  }

  function newProvider() {
    var defaults = configModel().defaults;
    return {
      provider: defaults.provider,
      index4: clone(defaults.index),
      index6: clone(defaults.index),
    };
  }

  function currentProfile() {
    if (!state.config || !state.config.providers) {
      return null;
    }
    return state.config.providers[state.profileIndex] || null;
  }

  function hasOwn(object, key) {
    return Object.prototype.hasOwnProperty.call(object, key);
  }

  function effectiveProfileValue(profile, key, fallback) {
    if (profile && hasOwn(profile, key)) {
      return profile[key];
    }
    if (state.config && hasOwn(state.config, key)) {
      return state.config[key];
    }
    return fallback;
  }

  function ensureConfigShape() {
    var model = configModel();
    var defaults = model.defaults;
    if (!state.config || typeof state.config !== "object" || Array.isArray(state.config)) {
      state.config = {
        "$schema": model.schema.url,
        ssl: defaults.ssl,
        proxy: defaults.proxy.slice(),
        cache: defaults.cache,
        cache_max_age: defaults.cacheMaxAge,
        log: { level: defaults.logLevel },
        providers: [],
      };
    }
    if (!Array.isArray(state.config.providers)) {
      state.config.providers = [];
    }
    if (!state.config.providers.length && !state.repairRequired) {
      state.config.providers.push(newProvider());
      state.profileIndex = 0;
      setNotice("当前文件尚无 DNS 服务商。已创建一份未保存的初始配置，请按需修改。");
    }
  }

  function sourceText(value) {
    if (value === false) {
      return "false";
    }
    if (Array.isArray(value)) {
      return value.join("\n");
    }
    return value === undefined || value === null ? "" : String(value);
  }

  function parseSources(value) {
    var trimmed = value.trim();
    var rules = configModel().rules;
    if (!trimmed) {
      return null;
    }
    if (rules.falseAliases.indexOf(trimmed.toLowerCase()) >= 0) {
      return false;
    }
    var result = [];
    trimmed.split(/\r?\n/).forEach(function (line) {
      var separator = line.indexOf(",") >= 0 ? "," : line.indexOf(";") >= 0 ? ";" : null;
      var parts = separator ? line.split(separator) : [line];
      for (var index = 0; index < parts.length; index += 1) {
        var part = parts[index].trim();
        if (!part) {
          continue;
        }
        if (
          separator &&
          rules.addressSourcePrefixes.some(function (prefix) {
            return part.indexOf(prefix) === 0;
          })
        ) {
          result.push(parts.slice(index).join(separator).trim());
          break;
        }
        result.push(/^\d+$/.test(part) ? Number(part) : part);
      }
    });
    return result;
  }

  function proxyText(value) {
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    return value || "";
  }

  function parseProxy(value) {
    if (!value.trim()) {
      return null;
    }
    return value
      .split(/[;,]/)
      .map(function (item) {
        return item.trim();
      })
      .filter(Boolean);
  }

  function updateProviderSelect(selectedId) {
    var select = byId("provider-name");
    clear(select);
    var catalog = providerCatalog().slice();
    if (
      selectedId &&
      !catalog.some(function (provider) {
        return provider.id === selectedId;
      })
    ) {
      catalog.push({ id: selectedId, name: selectedId });
    }
    catalog.forEach(function (provider) {
      var option = make("option", "", provider.name + (provider.testOnly ? " · 测试" : ""));
      option.value = provider.id;
      option.selected = provider.id === selectedId;
      select.appendChild(option);
    });
  }

  function profileOptionText(profile) {
    var domainCount =
      effectiveProfileValue(profile, "ipv4", []).length + effectiveProfileValue(profile, "ipv6", []).length;
    return providerLabel(profile.provider) + " · " + domainCount + " 个域名";
  }

  function renderProfileSelect() {
    var select = byId("profile-select");
    clear(select);
    state.config.providers.forEach(function (profile, index) {
      var option = make("option", "", profileOptionText(profile));
      option.value = String(index);
      option.selected = index === state.profileIndex;
      select.appendChild(option);
    });
  }

  function renderDomains(family) {
    var profile = currentProfile();
    var domains = effectiveProfileValue(profile, family, []);
    var list = byId(family + "-domain-list");
    clear(list);
    if (!domains.length) {
      list.appendChild(make("small", "domain-empty", "未配置域名"));
      return;
    }
    domains.forEach(function (domain, index) {
      var item = make("span");
      item.appendChild(document.createTextNode(domain));
      var button = make("button", "", "×");
      button.type = "button";
      button.setAttribute("aria-label", "移除域名 " + domain);
      button.setAttribute("data-remove-domain", family);
      button.setAttribute("data-domain-index", index);
      item.appendChild(button);
      list.appendChild(item);
    });
  }

  function setInput(id, value) {
    byId(id).value = value === undefined || value === null ? "" : value;
  }

  function renderProviderMetadata(providerId) {
    var metadata = providerMetadata(providerId) || {};
    var auth = metadata.auth || "id-token";
    var showId = auth !== "none" && auth !== "token";
    var showToken = auth !== "none";
    setText(
      "provider-description",
      (metadata.description && metadata.description.zh) || "凭据只保存在指定的本机配置文件中。",
    );
    setText("provider-id-label", (metadata.idLabel && metadata.idLabel.zh) || "账号或 ID");
    setText("provider-token-label", (metadata.tokenLabel && metadata.tokenLabel.zh) || "Token 或密钥");
    byId("provider-id-field").hidden = !showId;
    byId("provider-token-field").hidden = !showToken;
  }

  function renderProfile() {
    var profile = currentProfile();
    var defaults = configModel().defaults;
    if (!profile) {
      return;
    }
    updateProviderSelect(profile.provider);
    renderProviderMetadata(profile.provider);
    setInput("provider-id", effectiveProfileValue(profile, "id", ""));
    setInput("provider-token", effectiveProfileValue(profile, "token", ""));
    setInput("record-line", effectiveProfileValue(profile, "line", null));
    setInput("index4", sourceText(effectiveProfileValue(profile, "index4", ["default"])));
    setInput("index6", sourceText(effectiveProfileValue(profile, "index6", ["default"])));
    setInput("ttl", effectiveProfileValue(profile, "ttl", null));
    var proxy = hasOwn(state.config, "proxy") ? state.config.proxy : defaults.proxy;
    var ssl = hasOwn(state.config, "ssl") ? state.config.ssl : defaults.ssl;
    var cache = hasOwn(state.config, "cache") ? state.config.cache : defaults.cache;
    var log = state.config.log && typeof state.config.log === "object" ? state.config.log : {};
    setInput("proxy", proxyText(proxy));
    byId("ssl-enabled").checked = ssl !== false;
    byId("cache-enabled").checked = cache !== false;
    setText("ssl-label", ssl === "auto" ? "自动" : ssl === false ? "关闭" : "开启");
    setText(
      "cache-label",
      typeof cache === "string" ? "自定义路径" : cache === false ? "关闭" : "开启",
    );
    setInput("log-level", log.level || defaults.logLevel);
    setInput("log-file", log.file);
    setText("profile-badge", String(providerLabel(profile.provider)).slice(0, 3).toUpperCase());
    renderDomains("ipv4");
    renderDomains("ipv6");
    byId("delete-profile-button").disabled = state.config.providers.length <= 1;
    if (!state.repairRequired && byId("json-details").open && !state.jsonDirty) {
      setJsonEditorValue(JSON.stringify(state.config, null, 2));
    }
  }

  function configsMatch() {
    return JSON.stringify(state.config) === JSON.stringify(state.originalConfig);
  }

  function updateDirtyState(skipStructuredControls) {
    state.dirty = !configsMatch() || (state.invalidRawConfig !== null && !state.repairRequired);
    var pendingChanges = hasPendingChanges();
    var stateNode = byId("save-state");
    stateNode.className = "save-state" + (pendingChanges || state.repairRequired ? " dirty" : "");
    stateNode.querySelector("span").textContent = state.repairRequired
      ? "配置需要修复"
      : state.jsonDirty
        ? "JSON 尚未应用"
        : state.dirty
          ? "有未保存修改"
          : "已与磁盘同步";
    var editorState = byId("editor-state");
    editorState.className = pendingChanges || state.repairRequired ? "dirty" : "";
    editorState.textContent = state.repairRequired
      ? "请在完整 JSON 中修复配置，验证通过后才能保存。"
      : state.jsonDirty
        ? "完整 JSON 有未应用的修改；应用或放弃后才能保存。"
        : state.dirty
          ? "更改尚未写入 " + (state.configPath || "配置文件")
          : "修改会先保留在当前页面，保存后才写入磁盘。";
    var saveDisabled = !state.dirty || state.jsonDirty || state.repairRequired || state.saving;
    byId("save-button").disabled = saveDisabled;
    byId("footer-save-button").disabled = saveDisabled;
    byId("discard-button").disabled = !pendingChanges || state.saving;
    byId("restore-button").disabled = state.saving || !state.backupAvailable;
    byId("json-editor").disabled = state.saving;
    byId("format-json-button").disabled = state.saving;
    byId("apply-json-button").disabled = state.saving;
    if (!skipStructuredControls) {
      updateStructuredControls();
    }
    renderConfigSummary();
  }

  function markDirty() {
    updateDirtyState(true);
    if (byId("json-details").open && !state.jsonDirty) {
      setJsonEditorValue(JSON.stringify(state.config, null, 2));
    }
  }

  function renderConfig() {
    ensureConfigShape();
    if (state.profileIndex >= state.config.providers.length) {
      state.profileIndex = Math.max(0, state.config.providers.length - 1);
    }
    renderProfileSelect();
    renderProfile();
    var pathLabel = state.configPath ? state.configPath.split(/[\\/]/).pop() + " · 本机" : "当前配置";
    setText("config-path-label", pathLabel);
    byId("config-path-label").title = state.configPath;
    renderSetupMode();
    updateDirtyState();
  }

  function loadDashboard() {
    return api("/api/dashboard").then(function (dashboard) {
      state.dashboard = dashboard;
      renderDashboard();
      if (state.config) {
        renderProfileSelect();
        renderProfile();
      }
      return dashboard;
    });
  }

  function refreshDashboard() {
    if (document.hidden || state.saving || app.classList.contains("busy")) {
      return Promise.resolve();
    }
    return api("/api/dashboard")
      .then(function (dashboard) {
        state.dashboard = dashboard;
        renderDashboard();
      })
      .catch(function (error) {
        var header = byId("header-health");
        header.className = "header-health error";
        header.querySelector("span").textContent = "状态异常";
        header.title = errorMessage(error);
      });
  }

  function startDashboardRefresh() {
    if (state.dashboardRefreshTimer) {
      return;
    }
    state.dashboardRefreshTimer = setInterval(refreshDashboard, 15000);
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden) {
        refreshDashboard();
      }
    });
  }

  function loadConfig() {
    return api("/api/config").then(function (result) {
      state.configModel = result.model;
      state.config = clone(result.config);
      state.originalConfig = clone(result.config);
      state.configPath = result.path || "";
      state.configExists = Boolean(result.exists);
      state.backupAvailable = Boolean(result.backup_available);
      state.profileIndex = 0;
      state.repairRequired = Boolean(result.validation_error);
      state.invalidRawConfig = state.repairRequired ? result.raw || "" : null;
      state.jsonDirty = false;
      state.jsonBaseline = "";
      state.schedulerIntervalDirty = false;
      setNotice("");
      renderConfig();
      if (result.validation_error) {
        setNotice(
          "当前配置无法验证：" + result.validation_error + "。请修复完整 JSON，或恢复上一份备份。",
          "error",
        );
        byId("automation-pane").open = true;
        byId("json-details").open = true;
        setJsonEditorValue(state.invalidRawConfig);
      }
      renderRuntime(state.dashboard || { providers: [] });
      return result;
    });
  }

  function loadAll() {
    return Promise.all([loadDashboard(), loadConfig()])
      .then(function () {
        initializeConfigSections();
        initializeConfigShell();
        if (isFirstRun() && !state.setupOpened) {
          state.setupOpened = true;
          setView("config", false, false);
          window.history.replaceState(null, "", fragmentForView("config", token));
        } else if (parseFragment().view === "config") {
          setView("config", false);
        }
      })
      .catch(function (error) {
        var header = byId("header-health");
        header.className = "header-health error";
        header.querySelector("span").textContent = "连接失败";
        byId("status-hero").className = "status-hero error";
        setText("status-title", "无法读取本机控制台");
        setText("status-summary", errorMessage(error));
        showToast(errorMessage(error), "error");
      });
  }

  function acceptPersistedConfig(result) {
    state.config = clone(result.config);
    state.originalConfig = clone(result.config);
    state.configPath = result.path || state.configPath;
    state.configExists = Boolean(result.exists);
    state.backupAvailable = Boolean(result.backup_available);
    state.invalidRawConfig = null;
    state.repairRequired = false;
    state.jsonDirty = false;
    state.schedulerIntervalDirty = false;
    setNotice("");
    renderConfig();
  }

  function saveConfig() {
    if (state.saving) {
      return Promise.resolve();
    }
    if (state.repairRequired || state.jsonDirty) {
      byId("automation-pane").open = true;
      byId("json-details").open = true;
      setNotice("请先应用完整 JSON 中的修改，验证通过后再保存。", "error");
      showToast("完整 JSON 尚未应用", "warning");
      return Promise.resolve();
    }
    if (!state.dirty) {
      return Promise.resolve();
    }
    var completingSetup = isFirstRun();
    state.saving = true;
    setSaveButtonLabels("保存中");
    updateDirtyState();
    setBusy(true);
    setNotice("");
    return api("/api/config", { method: "PUT", body: { config: state.config } })
      .then(function (result) {
        acceptPersistedConfig(result);
        return loadDashboard().then(function () {
          cuePersistedConfig();
          if (completingSetup && !isFirstRun()) {
            setView("overview", true);
            showToast("配置已保存，现在可以运行首次同步");
          } else if (completingSetup) {
            setView("config", false, false);
            showToast("配置已保存；请至少添加一个需要更新的域名", "warning");
          } else {
            showToast("配置已安全写入本机");
          }
        });
      })
      .catch(function (error) {
        setNotice(errorMessage(error), "error");
        showToast(errorMessage(error), "error");
      })
      .finally(function () {
        state.saving = false;
        setSaveButtonLabels("保存更改");
        setBusy(false);
        updateDirtyState();
      });
  }

  function discardChanges() {
    state.config = clone(state.originalConfig);
    state.profileIndex = 0;
    state.jsonDirty = false;
    state.schedulerIntervalDirty = false;
    if (state.invalidRawConfig !== null) {
      state.repairRequired = true;
      setNotice("当前配置仍需通过完整 JSON 修复，或恢复上一份备份。", "error");
    } else {
      state.repairRequired = false;
      setNotice("");
    }
    renderConfig();
    if (state.dashboard) {
      renderScheduler(state.dashboard);
    }
    if (state.invalidRawConfig !== null) {
      byId("automation-pane").open = true;
      byId("json-details").open = true;
      setJsonEditorValue(state.invalidRawConfig);
    } else if (byId("json-details").open) {
      setJsonEditorValue(JSON.stringify(state.config, null, 2));
    }
    showToast("未保存的更改已放弃", "warning");
  }

  function armRestore() {
    if (state.saving) {
      return;
    }
    var button = byId("restore-button");
    if (!state.restoreArmed) {
      state.restoreArmed = true;
      button.textContent = "再次点击确认";
      showToast("再次点击将切换到上一份配置", "warning");
      clearTimeout(state.restoreTimer);
      state.restoreTimer = setTimeout(function () {
        state.restoreArmed = false;
        button.textContent = "恢复备份";
      }, 4200);
      return;
    }

    state.restoreArmed = false;
    clearTimeout(state.restoreTimer);
    state.saving = true;
    button.textContent = "恢复中";
    setBusy(true);
    updateDirtyState();
    api("/api/config/restore", { method: "POST", body: {} })
      .then(function (result) {
        state.profileIndex = 0;
        acceptPersistedConfig(result);
        showToast("已恢复上一份配置");
        return loadDashboard();
      })
      .then(function () {
        cuePersistedConfig();
      })
      .catch(function (error) {
        setNotice(errorMessage(error), "error");
        showToast(errorMessage(error), "error");
      })
      .finally(function () {
        state.saving = false;
        setBusy(false);
        button.textContent = "恢复备份";
        updateDirtyState();
      });
  }

  function addProfile() {
    var providerLimit = configModel().limits.providers;
    if (state.config.providers.length >= providerLimit) {
      showToast("服务商配置最多为 " + providerLimit + " 组", "warning");
      return;
    }
    state.config.providers.push(newProvider());
    state.profileIndex = state.config.providers.length - 1;
    byId("provider-pane").open = true;
    setNotice("");
    renderConfig();
    markDirty();
    byId("provider-name").focus();
  }

  function armDeleteProfile() {
    var button = byId("delete-profile-button");
    if (state.config.providers.length <= 1) {
      return;
    }
    if (!state.deleteArmed) {
      state.deleteArmed = true;
      button.textContent = "确认删除";
      showToast("再次点击将从草稿中移除此配置", "warning");
      clearTimeout(state.deleteTimer);
      state.deleteTimer = setTimeout(function () {
        state.deleteArmed = false;
        button.textContent = "删除";
      }, 4200);
      return;
    }
    state.deleteArmed = false;
    clearTimeout(state.deleteTimer);
    state.config.providers.splice(state.profileIndex, 1);
    state.profileIndex = Math.max(0, state.profileIndex - 1);
    button.textContent = "删除";
    renderConfig();
    markDirty();
  }

  function addDomain(family) {
    var input = byId(family + "-domain-input");
    var domain = input.value.trim().toLowerCase();
    var profile = currentProfile();
    if (!domain) {
      input.focus();
      return;
    }
    if (domain.length > 253 || /\s/.test(domain)) {
      showToast("请输入不含空格的有效域名", "error");
      input.focus();
      return;
    }
    if (!hasOwn(profile, family)) {
      profile[family] = effectiveProfileValue(profile, family, []).slice();
    }
    if (profile[family].indexOf(domain) >= 0) {
      showToast("这个域名已经在当前列表中", "warning");
      input.select();
      return;
    }
    profile[family].push(domain);
    input.value = "";
    renderDomains(family);
    renderProfileSelect();
    markDirty();
    input.focus();
  }

  function removeDomain(family, index) {
    var profile = currentProfile();
    if (!profile) {
      return;
    }
    if (!hasOwn(profile, family)) {
      profile[family] = effectiveProfileValue(profile, family, []).slice();
    }
    profile[family].splice(index, 1);
    renderDomains(family);
    renderProfileSelect();
    markDirty();
  }

  function runSync() {
    if (isFirstRun()) {
      setView("config", true);
      showToast("先选择 DNS 服务商并添加需要更新的域名", "warning");
      return;
    }
    if (hasPendingChanges() || state.repairRequired) {
      setView("config", true);
      showToast("请先保存配置，再运行同步", "warning");
      return;
    }
    if (!state.dashboard || !(state.dashboard.providers || []).length) {
      setView("config", true);
      showToast("请先添加 DNS 服务商与域名", "warning");
      return;
    }
    var button = byId("sync-button");
    var label = button.querySelector("span");
    var hero = byId("status-hero");
    var header = byId("header-health");
    button.disabled = true;
    label.textContent = "同步中";
    button.querySelector("svg").classList.add("spinning");
    header.className = "header-health syncing";
    header.querySelector("span").textContent = "同步中";
    setText("status-title", "正在同步解析");
    setText("status-summary", "正在检查本机地址、DNS 服务商与解析记录。");
    hero.classList.remove("sync-complete", "sync-failed");
    hero.classList.add("syncing");
    hero.setAttribute("aria-busy", "true");
    setBusy(true);
    var syncResult = api("/api/sync", { method: "POST", body: {} }).then(
      function (dashboard) {
        return { dashboard: dashboard };
      },
      function (error) {
        return { error: error };
      },
    );
    Promise.all([
      syncResult,
      new Promise(function (resolve) {
        setTimeout(resolve, 680);
      }),
    ])
      .then(function (results) {
        if (results[0].error) {
          throw results[0].error;
        }
        var dashboard = results[0].dashboard;
        state.dashboard = dashboard;
        renderDashboard();
        var failed = dashboard.state === "error";
        cueSyncOutcome(failed ? "error" : "success");
        showToast(
          failed ? dashboard.message || "同步完成，但部分记录更新失败" : "同步已完成",
          failed ? "error" : "",
        );
      })
      .catch(function (error) {
        showToast(errorMessage(error), "error");
        return loadDashboard()
          .catch(function (dashboardError) {
            setNotice(errorMessage(dashboardError), "error");
            renderDashboard();
          })
          .then(function () {
            cueSyncOutcome("error");
          });
      })
      .finally(function () {
        setBusy(false);
        button.disabled = false;
        label.textContent = "立即同步";
        button.querySelector("svg").classList.remove("spinning");
        hero.classList.remove("syncing");
        hero.removeAttribute("aria-busy");
      });
  }

  function schedulerAction(fromEditor) {
    if (hasPendingChanges() || state.repairRequired) {
      setView("config", true);
      showToast("请先保存配置，再启用自动同步", "warning");
      return;
    }
    var scheduler = (state.dashboard && state.dashboard.scheduler) || {};
    var interval = Number(byId("scheduler-interval").value || 5);
    var intervalChanged = interval !== Number(scheduler.interval);
    var action = scheduler.conflict
      ? "takeover"
      : fromEditor && intervalChanged
        ? "configure"
        : scheduler.enabled
          ? "disable"
          : "enable";
    var buttons = [byId("scheduler-button"), byId("automation-button")];
    buttons.forEach(function (button) {
      button.disabled = true;
    });
    setText("scheduler-action", "正在更新");
    setText("automation-button", "处理中");
    byId("scheduler-button").setAttribute("aria-busy", "true");
    setBusy(true);
    api("/api/scheduler", {
      method: "POST",
      body: { action: action, scheduler: "web", interval: interval },
    })
      .then(function () {
        showToast(
          {
            configure: "自动同步间隔已更新",
            disable: "Web 自动同步已暂停",
            enable: "Web 自动同步已启用",
            takeover: "Web 进程已接管自动同步",
          }[action],
        );
        return loadDashboard();
      })
      .catch(function (error) {
        showToast(errorMessage(error), "error");
        setNotice(errorMessage(error), "error");
      })
      .finally(function () {
        setBusy(false);
        buttons.forEach(function (button) {
          button.disabled = false;
        });
        byId("scheduler-button").removeAttribute("aria-busy");
        if (state.dashboard) {
          renderScheduler(state.dashboard);
        }
      });
  }

  function formatJson() {
    var editor = byId("json-editor");
    try {
      editor.value = JSON.stringify(JSON.parse(editor.value), null, 2);
      updateJsonDirtyState();
      setNotice("");
      showToast("JSON 格式已整理");
    } catch (error) {
      setNotice("JSON 无法解析：" + error.message, "error");
      showToast("JSON 格式有误", "error");
    }
  }

  function applyJson() {
    if (state.saving) {
      return;
    }
    var editor = byId("json-editor");
    var parsed;
    try {
      parsed = JSON.parse(editor.value);
    } catch (error) {
      setNotice("JSON 无法解析：" + error.message, "error");
      showToast("JSON 格式有误", "error");
      return;
    }
    state.saving = true;
    setBusy(true);
    updateDirtyState();
    api("/api/config/validate", { method: "POST", body: { config: parsed } })
      .then(function (result) {
        state.config = clone(result.config);
        state.profileIndex = 0;
        state.repairRequired = false;
        state.jsonDirty = false;
        state.schedulerIntervalDirty = state.config.interval !== state.originalConfig.interval;
        if (state.schedulerIntervalDirty) {
          setInput("scheduler-interval", hasOwn(state.config, "interval") ? state.config.interval : "");
        }
        setNotice("");
        renderConfig();
        showToast("JSON 已应用到当前草稿");
      })
      .catch(function (error) {
        setNotice(errorMessage(error), "error");
        showToast(errorMessage(error), "error");
      })
      .finally(function () {
        state.saving = false;
        setBusy(false);
        updateDirtyState();
      });
  }

  function setDraftValue(target, key, value, sparse) {
    if (sparse && (value === null || value === undefined || value === "")) {
      delete target[key];
    } else {
      target[key] = value;
    }
  }

  function bindProfileField(id, key, parser, eventName, sparse) {
    byId(id).addEventListener(eventName || "input", function (event) {
      var profile = currentProfile();
      var value = parser ? parser(event.target.value) : event.target.value;
      setDraftValue(profile, key, value, sparse);
      markDirty();
    });
  }

  function bindGlobalField(id, key, parser, eventName, sparse) {
    byId(id).addEventListener(eventName || "input", function (event) {
      var value = parser ? parser(event.target.value) : event.target.value;
      setDraftValue(state.config, key, value, sparse);
      markDirty();
    });
  }

  function switchProvider(providerName) {
    var profile = currentProfile();
    var replacement = { provider: providerName };
    ["ipv4", "ipv6", "index4", "index6", "ttl"].forEach(function (key) {
      if (hasOwn(profile, key)) {
        replacement[key] = clone(profile[key]);
      }
    });
    state.config.providers[state.profileIndex] = replacement;
    renderProfile();
    renderProfileSelect();
    markDirty();
    showToast("已清除旧服务商的凭据、端点与专用设置");
  }

  function bindEvents() {
    document.querySelectorAll("[data-view]").forEach(function (button) {
      button.addEventListener("click", function () {
        setView(button.getAttribute("data-view"), true);
      });
    });
    document.querySelector(".command-nav").addEventListener("keydown", function (event) {
      if (["ArrowLeft", "ArrowRight", "Home", "End"].indexOf(event.key) < 0) {
        return;
      }
      event.preventDefault();
      var buttons = Array.prototype.slice
        .call(document.querySelectorAll(".command-nav [data-view]"))
        .filter(function (button) {
          return !button.disabled;
        });
      var current = buttons.indexOf(document.activeElement);
      var next = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : current;
      if (event.key === "ArrowLeft") {
        next = (current - 1 + buttons.length) % buttons.length;
      } else if (event.key === "ArrowRight") {
        next = (current + 1) % buttons.length;
      }
      setView(buttons[next].getAttribute("data-view"), true);
      buttons[next].focus();
    });

    byId("theme-button").addEventListener("click", function () {
      applyTheme(app.classList.contains("dark") ? "light" : "dark");
    });
    byId("sync-button").addEventListener("click", runSync);
    byId("scheduler-button").addEventListener("click", function () {
      schedulerAction(false);
    });
    byId("automation-button").addEventListener("click", function () {
      schedulerAction(true);
    });
    byId("scheduler-interval").addEventListener("input", function (event) {
      if (state.config) {
        if (event.target.value === "") {
          delete state.config.interval;
        } else {
          state.config.interval = Number(event.target.value);
        }
        state.schedulerIntervalDirty =
          hasOwn(state.config, "interval") !== hasOwn(state.originalConfig, "interval") ||
          state.config.interval !== state.originalConfig.interval;
        markDirty();
      }
      updateSchedulerButton();
    });
    byId("save-button").addEventListener("click", saveConfig);
    byId("footer-save-button").addEventListener("click", saveConfig);
    byId("discard-button").addEventListener("click", discardChanges);
    byId("restore-button").addEventListener("click", armRestore);
    byId("add-profile-button").addEventListener("click", addProfile);
    byId("delete-profile-button").addEventListener("click", armDeleteProfile);
    byId("format-json-button").addEventListener("click", formatJson);
    byId("apply-json-button").addEventListener("click", applyJson);
    byId("json-editor").addEventListener("input", updateJsonDirtyState);

    byId("profile-select").addEventListener("change", function (event) {
      state.profileIndex = Number(event.target.value);
      state.deleteArmed = false;
      byId("delete-profile-button").textContent = "删除";
      renderProfile();
    });

    byId("provider-name").addEventListener("change", function (event) {
      switchProvider(event.target.value);
    });
    bindProfileField("record-line", "line", function (value) {
      return value.trim() || null;
    }, "input", true);
    bindProfileField("provider-id", "id", function (value) {
      return value.trim() || null;
    }, "input", true);
    bindProfileField("provider-token", "token", function (value) {
      return value.trim() || null;
    }, "input", true);
    bindProfileField("index4", "index4", parseSources, "input", true);
    bindProfileField("index6", "index6", parseSources, "input", true);
    bindProfileField("ttl", "ttl", function (value) {
      return value === "" ? null : Number(value);
    }, "input", true);
    bindGlobalField("proxy", "proxy", parseProxy, "input", true);

    byId("ssl-enabled").addEventListener("change", function (event) {
      state.config.ssl = event.target.checked;
      setText("ssl-label", event.target.checked ? "开启" : "关闭");
      markDirty();
    });
    byId("cache-enabled").addEventListener("change", function (event) {
      state.config.cache = event.target.checked;
      setText("cache-label", event.target.checked ? "开启" : "关闭");
      markDirty();
      renderRuntime(state.dashboard || { providers: [] });
    });
    byId("log-level").addEventListener("change", function (event) {
      if (!state.config.log || typeof state.config.log !== "object") {
        state.config.log = {};
      }
      state.config.log.level = event.target.value;
      markDirty();
    });
    byId("log-file").addEventListener("input", function (event) {
      if (!state.config.log || typeof state.config.log !== "object") {
        state.config.log = {};
      }
      setDraftValue(state.config.log, "file", event.target.value.trim() || null, true);
      markDirty();
    });

    document.querySelectorAll("[data-add-domain]").forEach(function (button) {
      button.addEventListener("click", function () {
        addDomain(button.getAttribute("data-add-domain"));
      });
    });
    ["ipv4", "ipv6"].forEach(function (family) {
      byId(family + "-domain-input").addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
          event.preventDefault();
          addDomain(family);
        }
      });
      byId(family + "-domain-list").addEventListener("click", function (event) {
        var button = event.target.closest("[data-remove-domain]");
        if (button) {
          removeDomain(button.getAttribute("data-remove-domain"), Number(button.getAttribute("data-domain-index")));
        }
      });
    });

    byId("record-search").addEventListener("input", function (event) {
      state.recordQuery = event.target.value.trim();
      renderRecords();
    });
    document.querySelectorAll("[data-activity-filter]").forEach(function (button) {
      button.addEventListener("click", function () {
        state.activityFilter = button.getAttribute("data-activity-filter");
        document.querySelectorAll("[data-activity-filter]").forEach(function (other) {
          other.classList.toggle("active", other === button);
        });
        renderActivities();
      });
    });
    byId("json-details").addEventListener("toggle", function () {
      if (byId("json-details").open && !state.jsonDirty) {
        setJsonEditorValue(
          state.repairRequired ? state.invalidRawConfig : JSON.stringify(state.config, null, 2),
        );
      }
    });

    window.addEventListener("hashchange", function () {
      var fragment = parseFragment();
      setView(fragment.view === "config" ? "config" : "overview", false);
    });
    window.addEventListener("beforeunload", function (event) {
      if (hasPendingChanges()) {
        event.preventDefault();
        event.returnValue = "";
      }
    });
    document.addEventListener("keydown", function (event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        saveConfig();
      }
    });
  }
  applyTheme(initialTheme());
  applyTheme(initialTheme());
  bindEvents();
  setView(initialView, false);
  loadAll().then(startDashboardRefresh);
})();
