<template>
  <div class="detail-page">
    <div v-if="loading" class="hint">加载中…</div>
    <div v-else-if="!diary" class="hint">日记不存在</div>
    <template v-else>
      <div class="header">
        <h1>{{ diary.title }}</h1>
        <div class="meta">
          <span>作者：{{ diary.author }}</span>
          <el-tag v-if="diary.destination" type="info" size="small">{{ diary.destination }}</el-tag>
          <span>👀 {{ diary.heat }}</span>
          <span>⭐ {{ diary.rating.toFixed(1) }}</span>
        </div>
      </div>

      <div class="content" v-html="diary.content"></div>

      <div class="actions">
        <div class="rate-box">
          <span>评分：</span>
          <el-rate v-model="userRating" @change="submitRating" :disabled="ratingCooldown" />
        </div>
        <el-button type="danger" size="small" @click="deleteDiary">删除日记</el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { diaryApi } from '../../api/diary'

const route = useRoute()
const router = useRouter()
const diary = ref(null)
const loading = ref(true)
const userRating = ref(0)
const ratingCooldown = ref(false)

onMounted(async () => {
  try {
    diary.value = await diaryApi.get(route.params.id)
    userRating.value = diary.value.rating
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
})

async function submitRating() {
  if (ratingCooldown.value) {
    ElMessage.warning('暂时无法评分，请稍后再试')
    return
  }
  try {
    await diaryApi.rate(route.params.id, userRating.value)
    ElMessage.success('评分成功')
    ratingCooldown.value = true
    setTimeout(() => ratingCooldown.value = false, 2000)
  } catch {
    ElMessage.error('评分失败')
  }
}

async function deleteDiary() {
  try {
    await ElMessageBox.confirm('确定删除此日记？', '提示', { type: 'warning' })
    await diaryApi.delete(route.params.id)
    ElMessage.success('删除成功')
    router.push('/diary')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.detail-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 64px 20px 60px;
}
.hint { color: #888; text-align: center; padding: 40px 0; }
.header { margin-bottom: 20px; }
.header h1 { font-size: 24px; margin-bottom: 10px; }
.meta { display: flex; align-items: center; gap: 12px; color: #666; font-size: 13px; flex-wrap: wrap; }
.content { line-height: 1.8; font-size: 15px; border-top: 1px solid #f0f0f0; padding-top: 20px; margin-bottom: 24px; }
.actions {
  position: fixed;
  right: 32px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  padding: 16px 12px;
}
.rate-box { display: flex; flex-direction: column; align-items: center; gap: 6px; font-size: 13px; color: #666; }
</style>
