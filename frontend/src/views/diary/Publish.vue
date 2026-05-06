<template>
  <div class="publish-page">
    <div class="form">
      <el-input v-model="title" placeholder="日记标题" size="large" maxlength="255" show-word-limit />
      <el-input v-model="author" placeholder="作者昵称（选填，默认匿名）" maxlength="100" />
      <el-input v-model="destination" placeholder="目的地（选填）" maxlength="255" />

      <div style="border:1px solid #d9d9d9;border-radius:4px;overflow:hidden">
        <Toolbar :editor="editorRef" :defaultConfig="toolbarConfig" />
        <Editor
          :defaultConfig="editorConfig"
          style="height:400px;overflow-y:auto"
          @onCreated="e => editorRef = e"
        />
      </div>

      <el-button type="primary" :loading="loading" @click="submit">发布</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import '@wangeditor/editor/dist/css/style.css'
import { diaryApi } from '../../api/diary'

const router = useRouter()
const title = ref('')
const author = ref('')
const destination = ref('')
const loading = ref(false)
const editorRef = shallowRef(null)
const toolbarConfig = {}
const editorConfig = { placeholder: '记录你的旅途…' }

async function submit() {
  if (!title.value.trim()) return ElMessage.warning('请填写标题')
  const html = editorRef.value?.getHtml() || ''
  if (!html || html === '<p><br></p>') return ElMessage.warning('请填写内容')
  loading.value = true
  try {
    await diaryApi.create({ title: title.value.trim(), destination: destination.value.trim(), content: html, author: author.value.trim() || '匿名', rating: 0 })
    ElMessage.success('发布成功')
    router.push('/diary')
  } catch {
    ElMessage.error('发布失败，请重试')
  } finally {
    loading.value = false
  }
}

onBeforeUnmount(() => editorRef.value?.destroy())
</script>

<style scoped>
.publish-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 64px 20px 40px;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
