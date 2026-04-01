<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { authService } from "@/services/auth";
import AppIcon from "@/components/icons/AppIcon.vue";
import { mockVideos } from "@/services/mock-videos";

const ADMIN_API = "http://localhost:8001";

interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
}

interface ApiMetrics {
  uptime_seconds: number;
  total_requests: number;
  log_entries: number;
  memory_rss_mb: number;
}

interface UserCount {
  total: number;
  active: number;
}

const currentUser = computed(() => authService.getCurrentUser());
const totalViews = computed(() =>
  mockVideos.reduce((sum, video) => sum + video.views, 0),
);

const logs = ref<LogEntry[]>([]);
const apiMetrics = ref<ApiMetrics | null>(null);
const userCount = ref<UserCount | null>(null);
const logsLoading = ref(false);
const logsError = ref<string | null>(null);
const levelFilter = ref("ALL");
const autoRefresh = ref(false);
let refreshTimer: ReturnType<typeof setInterval> | null = null;

const LEVELS = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];

const filteredLogs = computed(() => {
  if (levelFilter.value === "ALL") return logs.value;
  return logs.value.filter((l) => l.level === levelFilter.value);
});

async function fetchLogs() {
  logsLoading.value = true;
  logsError.value = null;
  try {
    const [logsRes, metricsRes, usersRes] = await Promise.all([
      fetch(`${ADMIN_API}/admin/logs`),
      fetch(`${ADMIN_API}/admin/metrics`),
      fetch(`${ADMIN_API}/admin/users/count`),
    ]);
    if (!logsRes.ok) throw new Error(`Logs request failed: ${logsRes.status}`);
    if (!metricsRes.ok) throw new Error(`Metrics request failed: ${metricsRes.status}`);
    const logsData = await logsRes.json();
    apiMetrics.value = await metricsRes.json();
    logs.value = logsData.logs ?? [];
    if (usersRes.ok) userCount.value = await usersRes.json();
  } catch (e: unknown) {
    logsError.value =
      e instanceof Error ? e.message : "Failed to connect to admin service";
  } finally {
    logsLoading.value = false;
  }
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value;
  if (autoRefresh.value) {
    refreshTimer = setInterval(fetchLogs, 5000);
  } else {
    if (refreshTimer !== null) clearInterval(refreshTimer);
  }
}

function formatUptime(seconds: number) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${h}h ${m}m ${s}s`;
}

function formatTimestamp(iso: string) {
  return new Date(iso).toLocaleString();
}

onMounted(fetchLogs);
onUnmounted(() => {
  if (refreshTimer !== null) clearInterval(refreshTimer);
});
</script>

<template>
  <main class="admin-page">
    <section v-if="!currentUser?.isAdmin" class="admin-card">
      <h1><AppIcon name="admin" :size="18" /> Admin access required</h1>
      <p>This area is available for admin accounts only.</p>
    </section>

    <template v-else>
      <!-- Content metrics (local mock data) -->
      <section class="admin-grid">
        <article class="metric">
          <p class="label"><AppIcon name="video" :size="14" /> Total videos</p>
          <p class="value">{{ mockVideos.length }}</p>
        </article>
        <article class="metric">
          <p class="label"><AppIcon name="views" :size="14" /> Total views</p>
          <p class="value">{{ totalViews.toLocaleString() }}</p>
        </article>
        <article class="metric">
          <p class="label"><AppIcon name="users" :size="14" /> Total users</p>
          <p class="value">{{ userCount?.total ?? "—" }}</p>
        </article>
        <article class="metric">
          <p class="label"><AppIcon name="users" :size="14" /> Active users</p>
          <p class="value">{{ userCount?.active ?? "—" }}</p>
        </article>
      </section>

      <!-- Service metrics from admin API -->
      <section v-if="apiMetrics" class="admin-grid api-metrics">
        <article class="metric metric--api">
          <p class="label">Service uptime</p>
          <p class="value">{{ formatUptime(apiMetrics.uptime_seconds) }}</p>
        </article>
        <article class="metric metric--api">
          <p class="label">Total requests</p>
          <p class="value">{{ apiMetrics.total_requests }}</p>
        </article>
        <article class="metric metric--api">
          <p class="label">Memory (RSS)</p>
          <p class="value">{{ apiMetrics.memory_rss_mb }} MB</p>
        </article>
        <article class="metric metric--api">
          <p class="label">Log entries</p>
          <p class="value">{{ apiMetrics.log_entries }}</p>
        </article>
      </section>

      <!-- System logs -->
      <section class="logs-section">
        <div class="logs-toolbar">
          <h2 class="section-title">System Logs</h2>
          <div class="toolbar-actions">
            <button
              class="action-btn"
              :class="{ 'action-btn--active': autoRefresh }"
              @click="toggleAutoRefresh"
            >
              {{ autoRefresh ? "Auto: ON" : "Auto: OFF" }}
            </button>
            <button class="action-btn" :disabled="logsLoading" @click="fetchLogs">
              Refresh
            </button>
          </div>
        </div>

        <!-- Level filter chips -->
        <div class="level-filters">
          <button
            v-for="lvl in LEVELS"
            :key="lvl"
            class="chip"
            :class="[`chip--${lvl.toLowerCase()}`, { active: levelFilter === lvl }]"
            @click="levelFilter = lvl"
          >
            {{ lvl }}
          </button>
        </div>

        <!-- Error state -->
        <div v-if="logsError" class="error-banner">{{ logsError }}</div>

        <!-- Loading placeholder -->
        <div v-else-if="logsLoading && logs.length === 0" class="empty-state">
          Loading logs…
        </div>

        <!-- Empty state -->
        <div v-else-if="filteredLogs.length === 0" class="empty-state">
          No log entries found.
        </div>

        <!-- Log table -->
        <div v-else class="log-table-wrapper">
          <table class="log-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Level</th>
                <th>Logger</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(entry, idx) in filteredLogs"
                :key="idx"
                :class="`row--${entry.level.toLowerCase()}`"
              >
                <td class="col-time">{{ formatTimestamp(entry.timestamp) }}</td>
                <td class="col-level">
                  <span :class="`badge badge--${entry.level.toLowerCase()}`">{{
                    entry.level
                  }}</span>
                </td>
                <td class="col-logger">{{ entry.logger }}</td>
                <td class="col-message">{{ entry.message }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="logs.length > 0" class="log-count">
          Showing {{ filteredLogs.length }} of {{ logs.length }} entries
        </p>
      </section>
    </template>
  </main>
</template>

<style scoped>
.admin-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 22px 16px 34px;
  display: grid;
  gap: 20px;
}

.admin-card,
.metric {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  background: #1a1a1a;
  padding: 16px;
}

.admin-card h1 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #fff;
}

.admin-card p {
  color: #a8aeba;
}

.admin-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric--api {
  background: #111;
  border-color: rgba(59, 130, 246, 0.2);
}

.api-metrics {
  margin-top: -8px;
}

.label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #9ca3af;
  font-size: 13px;
}

.value {
  color: #fff;
  font-size: 28px;
  font-weight: 700;
}

/* Logs section */
.logs-section {
  background: #0f0f0f;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 18px;
  display: grid;
  gap: 14px;
}

.logs-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #f2f4f8;
  margin: 0;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: #1a1a1a;
  color: #d4d7de;
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 13px;
  cursor: pointer;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.action-btn--active {
  border-color: rgba(239, 68, 68, 0.7);
  background: rgba(220, 38, 38, 0.18);
  color: #fca5a5;
}

/* Level filter chips */
.level-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: #1a1a1a;
  color: #d2d6df;
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}

.chip.active { color: #fff; }
.chip--all.active      { border-color: rgba(255,255,255,0.4); background: rgba(255,255,255,0.08); }
.chip--debug.active    { border-color: #6b7280; background: rgba(107,114,128,0.2); }
.chip--info.active     { border-color: #3b82f6; background: rgba(59,130,246,0.18); }
.chip--warning.active  { border-color: #f59e0b; background: rgba(245,158,11,0.18); }
.chip--error.active    { border-color: #ef4444; background: rgba(239,68,68,0.18); }
.chip--critical.active { border-color: #a855f7; background: rgba(168,85,247,0.18); }

/* Log table */
.log-table-wrapper {
  overflow-x: auto;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.log-table thead th {
  background: #1a1a1a;
  color: #9ca3af;
  font-weight: 600;
  text-align: left;
  padding: 10px 12px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  white-space: nowrap;
}

.log-table tbody tr {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.log-table tbody tr:last-child { border-bottom: none; }
.log-table tbody tr:hover { background: rgba(255, 255, 255, 0.03); }

.log-table td {
  padding: 9px 12px;
  color: #d4d7de;
  vertical-align: top;
}

.col-time    { white-space: nowrap; color: #6b7280; font-size: 12px; }
.col-level   { white-space: nowrap; }
.col-logger  { white-space: nowrap; color: #9ca3af; font-size: 12px; }
.col-message { word-break: break-word; }

.row--error td    { color: #fca5a5; }
.row--critical td { color: #d8b4fe; }
.row--warning td  { color: #fde68a; }

/* Badges */
.badge {
  display: inline-block;
  border-radius: 4px;
  padding: 2px 7px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.badge--debug    { background: rgba(107,114,128,0.25); color: #9ca3af; }
.badge--info     { background: rgba(59,130,246,0.2);   color: #93c5fd; }
.badge--warning  { background: rgba(245,158,11,0.2);   color: #fcd34d; }
.badge--error    { background: rgba(239,68,68,0.2);    color: #fca5a5; }
.badge--critical { background: rgba(168,85,247,0.22);  color: #d8b4fe; }

.error-banner {
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
}

.empty-state {
  text-align: center;
  color: #6b7280;
  padding: 40px 0;
  font-size: 14px;
}

.log-count {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
  text-align: right;
}

@media (max-width: 860px) {
  .admin-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 520px) {
  .admin-grid {
    grid-template-columns: 1fr;
  }
}
</style>
