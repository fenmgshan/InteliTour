<template>
  <div class="diary-index">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-select v-model="mode" style="width:140px;flex-shrink:0">
        <el-option label="标题" value="title" />
        <el-option label="目的地" value="destination" />
        <el-option label="全文检索" value="fulltext" />
      </el-select>
      <el-input
        v-model="query"
        placeholder="搜索日记…"
        clearable
        @keyup.enter="doSearch"
        @clear="loadRecommend"
        style="flex:1"
      />
      <el-button type="primary" @click="doSearch">搜索</el-button>
    </div>

    <!-- 卡片区 -->
    <div v-if="loading" class="hint">加载中…</div>
    <div v-else-if="!diaries.length" class="hint">暂无日记</div>
    <el-row v-else :gutter="16">
      <el-col v-for="d in diaries" :key="d.id" :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="diary-card" shadow="hover" @click="$router.push(`/diary/${d.id}`)">
          <div class="card-title">{{ d.title }}</div>
          <el-tag v-if="d.destination" size="small" type="info" class="card-dest">{{ d.destination }}</el-tag>
          <div class="card-meta">
            <span>👀 {{ d.heat ?? 0 }}</span>
            <span>⭐ {{ (d.rating ?? 0).toFixed(1) }}</span>
            <span class="card-author">{{ d.author }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- FAB -->
    <el-button type="primary" circle class="fab" @click="$router.push('/diary/publish')">
      <span style="font-size:22px;line-height:1">+</span>
    </el-button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { diaryApi } from '../../api/diary'

const mode = ref('title')
const query = ref('')
const diaries = ref([])
const loading = ref(false)

async function loadRecommend() {
  loading.value = true
  try { diaries.value = await diaryApi.list(20) } finally { loading.value = false }
}

async function doSearch() {
  if (!query.value.trim()) return loadRecommend()
  loading.value = true
  try { diaries.value = await diaryApi.search(mode.value, query.value.trim()) }
  finally { loading.value = false }
}

onMounted(loadRecommend)
</script>

<style scoped>
.diary-index {
  max-width: 1200px;
  margin: 0 auto;
  padding: 64px 20px 80px;
}
.search-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}
.hint { color: #888; text-align: center; padding: 40px 0; }
.diary-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform .15s;
}
.diary-card:hover { transform: translateY(-2px); }
.card-title { font-weight: 600; font-size: 15px; margin-bottom: 8px; }
.card-dest { margin-bottom: 8px; }
.card-meta { display: flex; gap: 12px; font-size: 13px; color: #666; align-items: center; }
.card-author { margin-left: auto; color: #999; }
.fab {
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 52px;
  height: 52px;
  box-shadow: 0 4px 16px rgba(22,119,255,.4);
  z-index: 200;
}
</style>
