<template>
  <div id="map-container" style="width:100%;height:100vh"></div>

  <div class="mode-toggle">
    <button :class="['mode-btn', store.mode==='route' && 'active']" @click="store.mode='route'">路线规划</button>
    <button :class="['mode-btn', store.mode==='explore' && 'active']" @click="store.mode='explore'">周边探索</button>
  </div>

  <div v-if="store.mode==='route'" class="panel">
    <div class="panel-title">路线规划</div>

    <div v-if="store.origin" class="point-item">
      <span class="dot" style="background:#f5222d"></span>起点: {{ fmt(store.origin) }}
    </div>
    <div v-else class="hint-text">点击地图设置起点</div>

    <div v-for="(wp, i) in store.waypoints" :key="i" class="point-item">
      <span class="dot" style="background:#1677ff"></span>途径点{{ i + 1 }}: {{ fmt(wp) }}
    </div>

    <div v-if="store.origin && !store.waypoints.length" class="hint-text">
      继续点击添加途径点
    </div>

    <template v-if="store.origin && store.waypoints.length">
      <select v-model="store.strategy" class="select">
        <option value="distance">最短距离</option>
        <option value="time">最短时间</option>
        <option value="bike">骑行</option>
        <option value="ebike">电动车</option>
      </select>
      <label class="checkbox-label">
        <input type="checkbox" v-model="store.roundTrip"> 返回起点
      </label>
      <button class="btn-plan" @click="planRoute" :disabled="loading">
        {{ loading ? '规划中…' : '开始规划' }}
      </button>
    </template>

    <div v-if="store.routeResult" class="result">
      总距离: {{ (store.routeResult.total_distance / 1000).toFixed(2) }} km<br>
      预计时间: {{ Math.round(store.routeResult.total_time / 60) }} 分钟
    </div>

    <button v-if="store.origin" class="btn-clear" @click="clearAll">清除</button>
  </div>

  <div v-if="store.mode==='explore'" class="explore-panel">
    <div class="panel-title">周边探索</div>
    <div v-if="!store.exploreOrigin" class="hint-text">点击地图选择探索中心</div>
    <div v-else class="hint-text">{{ fmt(store.exploreOrigin) }}</div>

    <template v-if="store.exploreOrigin">
      <div class="cat-btns">
        <button class="cat-btn" @click="queryNearby('toilet')">🚻 洗手间</button>
        <button class="cat-btn" @click="queryNearby('supermarket')">🏪 超市</button>
        <button class="cat-btn" @click="queryNearby('restaurant')">🍽️ 餐厅</button>
        <button class="cat-btn" @click="queryFood">🍔 美食推荐</button>
      </div>
      <div class="search-row">
        <input v-model="foodQuery" class="search-input" placeholder="搜索美食…" @keyup.enter="searchFood" />
        <button class="btn-search" @click="searchFood">搜</button>
      </div>
    </template>

    <div v-if="exploreLoading" class="hint-text">加载中…</div>
    <div v-for="item in store.exploreResults" :key="item.id" class="result-card">
      <div class="card-name">{{ item.name }}</div>
      <div class="card-meta">{{ item.sub_category }} · {{ fmtDist(item.distance) }}</div>
      <div class="card-addr">{{ item.address }}</div>
    </div>

    <button v-if="store.exploreOrigin" class="btn-clear" @click="clearExploreAll">清除</button>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import { useMapStore } from './stores/mapStore'

const store = useMapStore()
const loading = ref(false)
const exploreLoading = ref(false)
const foodQuery = ref('')
let map = null, AMap = null
let markers = [], polyline = null
let exploreMarkers = []

const fmt = (p) => `${p.lat.toFixed(5)}, ${p.lng.toFixed(5)}`
const fmtDist = (d) => d < 1000 ? `${Math.round(d)} m` : `${(d / 1000).toFixed(1)} km`

const EMOJI = { toilet: '🚻', supermarket: '🏪', restaurant: '🍽️', food: '🍔' }

function addMarker(latlng, label, color) {
  const m = new AMap.Marker({
    position: [latlng.lng, latlng.lat],
    content: `<div style="background:${color};color:#fff;padding:2px 7px;border-radius:4px;font-size:12px;white-space:nowrap">${label}</div>`,
    offset: new AMap.Pixel(-20, -14)
  })
  map.add(m)
  markers.push(m)
}

function clearAll() {
  markers.forEach(m => map.remove(m))
  markers = []
  if (polyline) { map.remove(polyline); polyline = null }
  store.clear()
}

function clearExploreMarkers() {
  exploreMarkers.forEach(m => map.remove(m))
  exploreMarkers = []
}

function clearExploreAll() {
  clearExploreMarkers()
  store.clearExplore()
}

function addExploreMarker(item, emoji, label) {
  const tip = label ?? item.name
  const m = new AMap.Marker({
    position: [item.lng, item.lat],
    content: `<div style="font-size:20px;line-height:1;cursor:default;position:relative" title="${tip}">${emoji}<span style="display:none;position:absolute;bottom:110%;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.7);color:#fff;padding:2px 6px;border-radius:3px;font-size:11px;white-space:nowrap;pointer-events:none" class="tip">${tip}</span></div>`,
    offset: new AMap.Pixel(-10, -10)
  })
  map.add(m)
  exploreMarkers.push(m)
}

async function queryNearby(category) {
  exploreLoading.value = true
  clearExploreMarkers()
  try {
    const { lat, lng } = store.exploreOrigin
    const res = await fetch('/api/nearby', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin_lat: lat, origin_lng: lng, category, limit: 10 })
    })
    if (!res.ok) return
    const data = await res.json()
    store.setExploreResults(data)
    data.forEach(item => addExploreMarker(item, EMOJI[category] ?? '📍', category === 'toilet' ? '卫生间' : item.name))
  } finally {
    exploreLoading.value = false
  }
}

async function queryFood() {
  exploreLoading.value = true
  clearExploreMarkers()
  try {
    const { lat, lng } = store.exploreOrigin
    const res = await fetch('/api/food/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin_lat: lat, origin_lng: lng, cuisine: '', n: 10 })
    })
    if (!res.ok) return
    const data = await res.json()
    store.setExploreResults(data)
    data.forEach(item => addExploreMarker(item, EMOJI.food))
  } finally {
    exploreLoading.value = false
  }
}

async function searchFood() {
  if (!foodQuery.value.trim()) return
  exploreLoading.value = true
  clearExploreMarkers()
  try {
    const { lat, lng } = store.exploreOrigin
    const res = await fetch('/api/food/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ q: foodQuery.value.trim(), origin_lat: lat, origin_lng: lng, n: 10 })
    })
    if (!res.ok) return
    const data = await res.json()
    store.setExploreResults(data)
    data.forEach(item => addExploreMarker(item, EMOJI.food))
  } finally {
    exploreLoading.value = false
  }
}

async function planRoute() {
  loading.value = true
  try {
    const isSingle = store.waypoints.length === 1
    const url = isSingle ? '/api/route/shortest' : '/api/route/tsp'
    const body = isSingle
      ? { origin: store.origin, destination: store.waypoints[0], strategy: store.strategy }
      : { origin: store.origin, waypoints: store.waypoints, strategy: store.strategy, round_trip: store.roundTrip }

    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    if (!res.ok) return
    const data = await res.json()
    store.setRouteResult(data)

    if (polyline) map.remove(polyline)
    polyline = new AMap.Polyline({
      path: data.path.map(p => [p.lng, p.lat]),
      strokeColor: '#1677ff',
      strokeWeight: 5,
      strokeOpacity: 0.9
    })
    map.add(polyline)
    map.setFitView([polyline])
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  window._AMapSecurityConfig = { securityJsCode: import.meta.env.VITE_AMAP_SECURITY_KEY }
  AMap = await AMapLoader.load({ key: import.meta.env.VITE_AMAP_KEY, version: '2.0' })
  map = new AMap.Map('map-container', { center: [116.4074, 39.9042], zoom: 15 })

  map.on('click', (e) => {
    const { lng, lat } = e.lnglat
    if (store.mode === 'explore') {
      clearExploreMarkers()
      store.setExploreOrigin({ lat, lng })
      store.setExploreResults([])
    } else {
      if (!store.origin) {
        store.setOrigin({ lat, lng })
        addMarker({ lat, lng }, '起点', '#f5222d')
      } else {
        const idx = store.waypoints.length + 1
        store.addWaypoint({ lat, lng })
        addMarker({ lat, lng }, `途径${idx}`, '#1677ff')
      }
    }
  })
})

onUnmounted(() => map?.destroy())
</script>

<style scoped>
.panel {
  position: fixed;
  top: 20px;
  left: 20px;
  width: 240px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.25);
  padding: 14px;
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.panel-title { font-weight: bold; font-size: 15px; }
.point-item { display: flex; align-items: center; gap: 6px; word-break: break-all; }
.dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.hint-text { color: #888; }
.select { width: 100%; padding: 4px; border-radius: 4px; border: 1px solid #d9d9d9; }
.checkbox-label { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.btn-plan {
  width: 100%; padding: 6px; background: #1677ff; color: white;
  border: none; border-radius: 4px; cursor: pointer; font-size: 13px;
}
.btn-plan:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-clear {
  width: 100%; padding: 5px; background: #fff; color: #f5222d;
  border: 1px solid #f5222d; border-radius: 4px; cursor: pointer; font-size: 13px;
}
.result { background: #f0f7ff; border-radius: 4px; padding: 8px; line-height: 1.8; }
.mode-toggle {
  position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
  display: flex; background: white; border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2); overflow: hidden; z-index: 10;
}
.mode-btn { padding: 6px 18px; border: none; background: transparent; cursor: pointer; font-size: 13px; }
.mode-btn.active { background: #1677ff; color: white; }
.explore-panel {
  position: fixed; top: 20px; right: 20px; width: 260px;
  max-height: calc(100vh - 40px); overflow-y: auto;
  background: white; border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.25); padding: 14px;
  font-size: 13px; display: flex; flex-direction: column; gap: 8px;
}
.cat-btns { display: flex; flex-wrap: wrap; gap: 6px; }
.cat-btn { padding: 4px 10px; border: 1px solid #d9d9d9; border-radius: 4px; background: #fafafa; cursor: pointer; font-size: 12px; }
.cat-btn:hover { border-color: #1677ff; color: #1677ff; }
.search-row { display: flex; gap: 6px; }
.search-input { flex: 1; padding: 4px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; }
.btn-search { padding: 4px 10px; background: #1677ff; color: white; border: none; border-radius: 4px; cursor: pointer; }
.result-card { border: 1px solid #e8e8e8; border-radius: 6px; padding: 8px; display: flex; flex-direction: column; gap: 3px; }
.card-name { font-weight: 600; }
.card-meta { color: #1677ff; font-size: 12px; }
.card-addr { color: #888; font-size: 12px; word-break: break-all; }
</style>

<style>
div:hover > .tip { display: block !important; }
</style>
