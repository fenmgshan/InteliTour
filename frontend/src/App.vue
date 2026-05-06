<template>
  <div id="map-container" style="width:100%;height:100vh"></div>
  <div class="info-panel" v-if="store.snappedNode">
    <p>Node ID: <b>{{ store.snappedNode.node_id }}</b></p>
    <p>坐标: {{ store.snappedNode.lat.toFixed(6) }}, {{ store.snappedNode.lng.toFixed(6) }}</p>
    <p>吸附距离: {{ store.snappedNode.distance }} m</p>
  </div>
  <div class="hint" v-else>点击地图以吸附到最近路网节点</div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import { useMapStore } from './stores/mapStore'

const store = useMapStore()
let map = null
let marker = null

onMounted(async () => {
  window._AMapSecurityConfig = { securityJsCode: import.meta.env.VITE_AMAP_SECURITY_KEY }
  const AMap = await AMapLoader.load({
    key: import.meta.env.VITE_AMAP_KEY,
    version: '2.0'
  })

  map = new AMap.Map('map-container', {
    center: [116.4074, 39.9042],
    zoom: 15
  })

  map.on('click', async (e) => {
    const { lng, lat } = e.lnglat
    const res = await fetch('/api/snap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat, lng })
    })
    if (!res.ok) return
    const data = await res.json()
    store.setSnappedNode(data)

    if (marker) map.remove(marker)
    marker = new AMap.Marker({ position: [data.lng, data.lat] })
    map.add(marker)
  })
})

onUnmounted(() => map?.destroy())
</script>

<style scoped>
.info-panel, .hint {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  font-size: 14px;
}
</style>
