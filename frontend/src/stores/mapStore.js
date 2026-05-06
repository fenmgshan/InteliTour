import { defineStore } from 'pinia'

export const useMapStore = defineStore('map', {
  state: () => ({
    snappedNode: null  // { node_id, lat, lng, distance }
  }),
  actions: {
    setSnappedNode(node) {
      this.snappedNode = node
    }
  }
})
