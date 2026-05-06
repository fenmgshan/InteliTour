<template>
  <nav class="navbar">
    <span class="brand">InteliTour</span>
    <router-link to="/" class="nav-link">地图导航</router-link>
    <router-link to="/diary" class="nav-link">旅游日记</router-link>
  </nav>
  <router-view />
</template>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; }
.navbar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 44px; background: #1677ff; color: white;
  display: flex; align-items: center; gap: 20px; padding: 0 20px;
}
.brand { font-weight: bold; font-size: 16px; margin-right: 10px; }
.nav-link { color: rgba(255,255,255,0.85); text-decoration: none; font-size: 14px; }
.nav-link.router-link-active { color: white; font-weight: 600; border-bottom: 2px solid white; padding-bottom: 2px; }
</style>
