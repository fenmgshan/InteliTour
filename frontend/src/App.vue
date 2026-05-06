<template>
  <div id="map-container" style="width:100%;height:100vh"></div>

  <div class="panel">
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
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import { useMapStore } from './stores/mapStore'

const store = useMapStore()
const loading = ref(false)
let map = null, AMap = null
let markers = [], polyline = null

const fmt = (p) => `${p.lat.toFixed(5)}, ${p.lng.toFixed(5)}`

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
    if (!store.origin) {
      store.setOrigin({ lat, lng })
      addMarker({ lat, lng }, '起点', '#f5222d')
    } else {
      const idx = store.waypoints.length + 1
      store.addWaypoint({ lat, lng })
      addMarker({ lat, lng }, `途径${idx}`, '#1677ff')
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
</style>
