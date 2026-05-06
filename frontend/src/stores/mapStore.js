import { defineStore } from 'pinia'

export const useMapStore = defineStore('map', {
  state: () => ({
    mode: 'route',          // 'route' | 'explore'
    origin: null,
    waypoints: [],
    routeResult: null,
    strategy: 'distance',
    roundTrip: false,
    exploreOrigin: null,
    exploreResults: [],
  }),
  actions: {
    setOrigin(p) { this.origin = p },
    addWaypoint(p) { this.waypoints.push(p) },
    setRouteResult(r) { this.routeResult = r },
    clear() { this.origin = null; this.waypoints = []; this.routeResult = null },
    setExploreOrigin(p) { this.exploreOrigin = p },
    setExploreResults(r) { this.exploreResults = r },
    clearExplore() { this.exploreOrigin = null; this.exploreResults = [] },
  }
})
