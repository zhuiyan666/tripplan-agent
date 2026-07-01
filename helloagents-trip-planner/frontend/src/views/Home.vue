<template>
  <div class="home-container">
    <div class="page-header">
      <h1 class="page-title">✈️ 智能旅行助手</h1>
      <p class="page-subtitle">基于AI的个性化旅行规划</p>
    </div>

    <a-card class="form-card" :bordered="false">
      <a-form
        :model="formData"
        layout="vertical"
        @finish="handleSubmit"
      >
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item
              label="目的地城市"
              name="city"
              :rules="[{ required: true, message: '请输入目的地城市' }]"
            >
              <a-input
                v-model:value="formData.city"
                placeholder="如：北京、上海、杭州"
                size="large"
              />
            </a-form-item>
          </a-col>

          <a-col :span="12">
            <a-form-item
              label="旅行天数"
              name="days"
              :rules="[{ required: true, message: '请输入旅行天数' }]"
            >
              <a-input-number
                v-model:value="formData.days"
                :min="1"
                :max="30"
                size="large"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item
              label="开始日期"
              name="start_date"
              :rules="[{ required: true, message: '请选择开始日期' }]"
            >
              <a-date-picker
                v-model:value="startDateValue"
                style="width: 100%"
                size="large"
                placeholder="选择开始日期"
                value-format="YYYY-MM-DD"
                @change="onStartDateChange"
              />
            </a-form-item>
          </a-col>

          <a-col :span="12">
            <a-form-item
              label="结束日期"
              name="end_date"
              :rules="[{ required: true, message: '请选择结束日期' }]"
            >
              <a-date-picker
                v-model:value="endDateValue"
                style="width: 100%"
                size="large"
                placeholder="选择结束日期"
                value-format="YYYY-MM-DD"
                @change="onEndDateChange"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="旅行偏好" name="preferences">
              <a-select
                v-model:value="formData.preferences"
                size="large"
                placeholder="选择旅行偏好"
              >
                <a-select-option value="历史文化">🏛️ 历史文化</a-select-option>
                <a-select-option value="自然风光">🏔️ 自然风光</a-select-option>
                <a-select-option value="美食探索">🍜 美食探索</a-select-option>
                <a-select-option value="购物休闲">🛍️ 购物休闲</a-select-option>
                <a-select-option value="亲子游">👨‍👩‍👧‍👦 亲子游</a-select-option>
                <a-select-option value="冒险户外">🏕️ 冒险户外</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>

          <a-col :span="12">
            <a-form-item label="预算级别" name="budget">
              <a-select
                v-model:value="formData.budget"
                size="large"
                placeholder="选择预算级别"
              >
                <a-select-option value="经济">💰 经济型（人均2000以下）</a-select-option>
                <a-select-option value="中等">💰💰 中等（人均2000-5000）</a-select-option>
                <a-select-option value="豪华">💰💰💰 豪华型（人均5000以上）</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="交通方式" name="transportation">
              <a-select
                v-model:value="formData.transportation"
                size="large"
                placeholder="选择交通方式"
              >
                <a-select-option value="公共交通">🚇 公共交通</a-select-option>
                <a-select-option value="自驾">🚗 自驾</a-select-option>
                <a-select-option value="出租车">🚕 出租车/网约车</a-select-option>
                <a-select-option value="步行">🚶 步行为主</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>

          <a-col :span="12">
            <a-form-item label="住宿类型" name="accommodation">
              <a-select
                v-model:value="formData.accommodation"
                size="large"
                placeholder="选择住宿类型"
              >
                <a-select-option value="经济型酒店">🏨 经济型酒店</a-select-option>
                <a-select-option value="舒适型酒店">🏨 舒适型酒店</a-select-option>
                <a-select-option value="豪华酒店">🏨 豪华酒店</a-select-option>
                <a-select-option value="民宿">🏡 民宿</a-select-option>
                <a-select-option value="青年旅社">🛏️ 青年旅社</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            :loading="loading"
            block
            class="submit-btn"
          >
            🚀 开始规划
          </a-button>
        </a-form-item>

        <a-form-item v-if="loading">
          <a-progress
            :percent="loadingProgress"
            status="active"
            :stroke-color="{ from: '#108ee9', to: '#87d068' }"
          />
          <p class="loading-status">{{ loadingStatus }}</p>
        </a-form-item>
      </a-form>
    </a-card>

    <div class="features-section">
      <a-row :gutter="24">
        <a-col :span="6">
          <a-card class="feature-card" :bordered="false">
            <div class="feature-icon">📋</div>
            <h3>智能行程规划</h3>
            <p>AI自动生成最优游览路线，合理规划每日行程</p>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card class="feature-card" :bordered="false">
            <div class="feature-icon">🗺️</div>
            <h3>地图可视化</h3>
            <p>在地图上标注景点位置，直观展示游览路线</p>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card class="feature-card" :bordered="false">
            <div class="feature-icon">💰</div>
            <h3>预算计算</h3>
            <p>自动估算门票、酒店、餐饮、交通费用</p>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card class="feature-card" :bordered="false">
            <div class="feature-icon">📤</div>
            <h3>一键导出</h3>
            <p>支持导出为PDF或图片，方便保存和分享</p>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateTripPlan } from '@/services/api'
import type { TripPlanRequest } from '@/types'

const router = useRouter()
const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')
const startDateValue = ref(null)
const endDateValue = ref(null)

const formData = ref<TripPlanRequest>({
  city: '',
  start_date: '',
  end_date: '',
  days: 3,
  preferences: '历史文化',
  budget: '中等',
  transportation: '公共交通',
  accommodation: '经济型酒店'
})

const onStartDateChange = (date: string) => {
  formData.value.start_date = date
  // 自动计算结束日期
  if (date && formData.value.days > 0) {
    const start = new Date(date)
    const end = new Date(start.getTime() + (formData.value.days - 1) * 24 * 60 * 60 * 1000)
    const endStr = end.toISOString().split('T')[0]
    formData.value.end_date = endStr
    endDateValue.value = endStr as any
  }
}

const onEndDateChange = (date: string) => {
  formData.value.end_date = date
  // 自动计算天数
  if (date && formData.value.start_date) {
    const start = new Date(formData.value.start_date)
    const end = new Date(date)
    const diff = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
    formData.value.days = Math.max(1, diff + 1)
  }
}

const handleSubmit = async () => {
  // 验证日期
  if (!formData.value.start_date || !formData.value.end_date) {
    message.error('请选择完整的旅行日期')
    return
  }

  loading.value = true
  loadingProgress.value = 0

  // 模拟进度更新
  const statusMessages = [
    '🔍 正在搜索景点...',
    '🌤️ 正在查询天气...',
    '🏨 正在推荐酒店...',
    '📋 正在生成行程计划...',
    '✨ 正在优化路线...',
    '🎨 正在准备图片...'
  ]

  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += Math.random() * 15
      if (loadingProgress.value > 90) loadingProgress.value = 90

      const statusIndex = Math.min(
        Math.floor((loadingProgress.value / 90) * statusMessages.length),
        statusMessages.length - 1
      )
      loadingStatus.value = statusMessages[statusIndex]
    }
  }, 800)

  try {
    const response = await generateTripPlan(formData.value)
    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '✅ 完成！'

    // 存储结果并跳转
    sessionStorage.setItem('tripPlan', JSON.stringify(response))
    router.push({ name: 'result' })
  } catch (error: any) {
    clearInterval(progressInterval)
    message.error(error.response?.data?.detail || '生成计划失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 36px;
  font-weight: bold;
  color: #1890ff;
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 16px;
  color: #666;
}

.form-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 32px;
  margin-bottom: 40px;
}

.submit-btn {
  height: 48px;
  font-size: 18px;
  border-radius: 24px;
}

.loading-status {
  text-align: center;
  margin-top: 12px;
  font-size: 16px;
  color: #666;
}

.features-section {
  margin-top: 20px;
}

.feature-card {
  text-align: center;
  padding: 24px 16px;
  border-radius: 12px;
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.feature-card p {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}
</style>
