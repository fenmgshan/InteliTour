import { defineStore } from 'pinia'

export const useMapStore = defineStore('map', {
  state: () => ({
    origin: null,       // { lat, lng }
    waypoints: [],      // [{ lat, lng }, ...]
    routeResult: null,  // ShortestPathResponse | TSPResponse
    strategy: 'distance',
    roundTrip: false,
  }),
  actions: {
    setOrigin(p) { this.origin = p },
    addWaypoint(p) { this.waypoints.push(p) },
    setRouteResult(r) { this.routeResult = r },
    clear() {
      this.origin = null
      this.waypoints = []
      this.routeResult = null
    }
  }
})
