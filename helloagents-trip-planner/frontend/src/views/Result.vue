<template>
  <div class="result-container" id="trip-plan-content">
    <!-- 页面标题 -->
    <div class="result-header">
      <h1>🗺️ {{ tripPlan?.city }} 旅行计划</h1>
      <p>{{ tripPlan?.start_date }} 至 {{ tripPlan?.end_date }} · {{ tripPlan?.days?.length || 0 }}天</p>

      <div class="header-actions">
        <a-button @click="goBack" class="action-btn">
          ← 返回首页
        </a-button>
        <a-button
          type="primary"
          @click="toggleEditMode"
          class="action-btn"
          :danger="editMode"
        >
          {{ editMode ? '退出编辑' : '✏️ 编辑行程' }}
        </a-button>
        <a-dropdown>
          <a-button type="primary" class="action-btn">
            📤 导出行程 ▼
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item @click="exportAsImage">🖼️ 导出为图片</a-menu-item>
              <a-menu-item @click="exportAsPDF">📄 导出为PDF</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- 编辑模式提示 -->
    <a-alert
      v-if="editMode"
      message="编辑模式：可以删除或移动景点"
      type="info"
      show-icon
      style="margin-bottom: 20px"
      closable
    />

    <a-row :gutter="24">
      <!-- 左侧侧边导航 -->
      <a-col :span="4" class="sidebar-col">
        <a-affix :offset-top="20">
          <a-menu
            v-model:selectedKeys="selectedKeys"
            mode="inline"
            @click="scrollToSection"
            class="sidebar-menu"
          >
            <a-menu-item key="overview">
              <span>📋 行程概览</span>
            </a-menu-item>
            <a-menu-item key="budget">
              <span>💰 预算明细</span>
            </a-menu-item>
            <a-menu-item key="map">
              <span>🗺️ 地图</span>
            </a-menu-item>
            <a-menu-item key="days">
              <span>📅 每日行程</span>
            </a-menu-item>
            <a-menu-item key="weather">
              <span>🌤️ 天气</span>
            </a-menu-item>
          </a-menu>
        </a-affix>
      </a-col>

      <!-- 右侧内容区 -->
      <a-col :span="20">
        <!-- 行程概览 -->
        <div id="overview" class="section">
          <h2 class="section-title">📋 行程概览</h2>
          <a-card class="content-card">
            <a-row :gutter="16">
              <a-col :span="6">
                <a-statistic title="目的地" :value="tripPlan?.city" />
              </a-col>
              <a-col :span="6">
                <a-statistic title="天数" :value="tripPlan?.days?.length || 0" suffix="天" />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  title="景点数"
                  :value="totalAttractions"
                  suffix="个"
                />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  v-if="tripPlan?.budget"
                  title="预估总费用"
                  :value="tripPlan.budget.total"
                  suffix="元"
                  :value-style="{ color: '#cf1322', fontWeight: 'bold' }"
                />
              </a-col>
            </a-row>
            <a-divider />
            <p class="suggestions">💡 {{ tripPlan?.overall_suggestions }}</p>
          </a-card>
        </div>

        <!-- 预算明细 -->
        <div id="budget" class="section" v-if="tripPlan?.budget">
          <h2 class="section-title">💰 预算明细</h2>
          <a-card class="content-card">
            <a-row :gutter="16">
              <a-col :span="6">
                <a-statistic
                  title="景点门票"
                  :value="tripPlan.budget.total_attractions"
                  suffix="元"
                  :value-style="{ color: '#1890ff' }"
                />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  title="酒店住宿"
                  :value="tripPlan.budget.total_hotels"
                  suffix="元"
                  :value-style="{ color: '#52c41a' }"
                />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  title="餐饮费用"
                  :value="tripPlan.budget.total_meals"
                  suffix="元"
                  :value-style="{ color: '#faad14' }"
                />
              </a-col>
              <a-col :span="6">
                <a-statistic
                  title="交通费用"
                  :value="tripPlan.budget.total_transportation"
                  suffix="元"
                  :value-style="{ color: '#722ed1' }"
                />
              </a-col>
            </a-row>
            <a-divider />
            <div style="text-align: center;">
              <a-statistic
                title="预估总费用"
                :value="tripPlan.budget.total"
                suffix="元"
                :value-style="{ color: '#cf1322', fontSize: '28px', fontWeight: 'bold' }"
              />
            </div>
          </a-card>
        </div>

        <!-- 地图 -->
        <div id="map" class="section">
          <h2 class="section-title">🗺️ 景点地图</h2>
          <a-card class="content-card">
            <div ref="mapContainer" class="map-container"></div>
          </a-card>
        </div>

        <!-- 每日行程 -->
        <div id="days" class="section">
          <h2 class="section-title">📅 每日行程</h2>
          <div
            v-for="(day, dayIndex) in tripPlan?.days"
            :key="dayIndex"
            class="day-plan"
          >
            <a-card class="content-card day-card">
              <template #title>
                <div class="day-title">
                  <span class="day-badge">第{{ dayIndex + 1 }}天</span>
                  <span class="day-date">{{ day.date }}</span>
                  <span class="day-desc">{{ day.description }}</span>
                </div>
              </template>

              <!-- 酒店信息 -->
              <div v-if="day.hotel" class="hotel-info">
                <a-tag color="blue">🏨 {{ day.hotel.name }}</a-tag>
                <span class="hotel-address">{{ day.hotel.address }}</span>
                <span v-if="day.hotel.estimated_cost" class="hotel-price">
                  ¥{{ day.hotel.estimated_cost }}/晚
                </span>
              </div>

              <!-- 景点列表 -->
              <div class="attractions-list">
                <h4>📍 景点安排</h4>
                <a-timeline>
                  <a-timeline-item
                    v-for="(attraction, attractionIndex) in day.attractions"
                    :key="attractionIndex"
                    :color="attractionIndex === 0 ? 'green' : attractionIndex === day.attractions.length - 1 ? 'red' : 'blue'"
                  >
                    <div class="attraction-item">
                      <div class="attraction-content">
                        <h5 class="attraction-name">
                          {{ attractionIndex + 1 }}. {{ attraction.name }}
                          <a-tag v-if="attraction.rating" color="orange">
                            ⭐ {{ attraction.rating }}
                          </a-tag>
                        </h5>
                        <p class="attraction-address">📍 {{ attraction.address }}</p>
                        <p class="attraction-desc">{{ attraction.description }}</p>
                        <div class="attraction-meta">
                          <span v-if="attraction.visit_duration">
                            ⏱️ {{ attraction.visit_duration }}分钟
                          </span>
                          <span v-if="attraction.ticket_price !== undefined">
                            🎫 ¥{{ attraction.ticket_price }}
                          </span>
                        </div>
                        <img
                          v-if="attraction.image_url"
                          :src="attraction.image_url"
                          :alt="attraction.name"
                          class="attraction-image"
                          @error="onImageError"
                        />
                      </div>

                      <!-- 编辑按钮 -->
                      <div v-if="editMode" class="edit-buttons">
                        <a-button
                          size="small"
                          :disabled="attractionIndex === 0"
                          @click="moveAttraction(dayIndex, attractionIndex, 'up')"
                        >
                          ↑ 上移
                        </a-button>
                        <a-button
                          size="small"
                          :disabled="attractionIndex === day.attractions.length - 1"
                          @click="moveAttraction(dayIndex, attractionIndex, 'down')"
                        >
                          ↓ 下移
                        </a-button>
                        <a-button
                          size="small"
                          danger
                          @click="deleteAttraction(dayIndex, attractionIndex)"
                        >
                          🗑️ 删除
                        </a-button>
                      </div>
                    </div>
                  </a-timeline-item>
                </a-timeline>
              </div>

              <!-- 餐饮安排 -->
              <div v-if="day.meals?.length" class="meals-list">
                <h4>🍽️ 餐饮安排</h4>
                <a-row :gutter="16">
                  <a-col
                    v-for="(meal, mealIndex) in day.meals"
                    :key="mealIndex"
                    :span="8"
                  >
                    <a-card class="meal-card" size="small">
                      <template #title>
                        <span>{{ getMealTypeLabel(meal.type) }}</span>
                      </template>
                      <p class="meal-name">{{ meal.name }}</p>
                      <p v-if="meal.estimated_cost !== undefined && meal.estimated_cost !== null" class="meal-cost">
                        ¥{{ meal.estimated_cost }}
                      </p>
                    </a-card>
                  </a-col>
                </a-row>
              </div>
            </a-card>
          </div>

          <!-- 编辑模式操作栏 -->
          <div v-if="editMode" class="edit-actions">
            <a-button type="primary" @click="saveChanges" size="large">
              💾 保存修改
            </a-button>
            <a-button @click="cancelEdit" size="large" style="margin-left: 12px;">
              ❌ 取消
            </a-button>
          </div>
        </div>

        <!-- 天气信息 -->
        <div id="weather" class="section" v-if="tripPlan?.weather_info?.length">
          <h2 class="section-title">🌤️ 天气预报</h2>
          <a-card class="content-card">
            <a-row :gutter="16">
              <a-col
                v-for="(weather, index) in tripPlan.weather_info"
                :key="index"
                :span="8"
              >
                <a-card class="weather-card" size="small">
                  <template #title>
                    <span>{{ weather.date }}</span>
                  </template>
                  <div class="weather-content">
                    <p>
                      <span class="weather-label">白天：</span>
                      {{ weather.day_weather }} {{ weather.day_temp }}°C
                    </p>
                    <p>
                      <span class="weather-label">夜间：</span>
                      {{ weather.night_weather }} {{ weather.night_temp }}°C
                    </p>
                    <p>
                      <span class="weather-label">风向：</span>
                      {{ weather.wind_direction }} {{ weather.wind_power }}
                    </p>
                  </div>
                </a-card>
              </a-col>
            </a-row>
          </a-card>
        </div>
      </a-col>
    </a-row>

    <!-- 导出遮罩层（导出时隐藏地图） -->
    <div v-if="exporting" class="export-overlay">
      <a-spin size="large" tip="正在生成导出文件..." />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import type { TripPlan, Attraction } from '@/types'

const router = useRouter()
const mapContainer = ref<HTMLElement>()
const activeSection = ref('overview')
const selectedKeys = ref(['overview'])
const editMode = ref(false)
const originalPlan = ref<TripPlan | null>(null)
const exporting = ref(false)

// 高德地图实例
let map: any = null
let markers: any[] = []

// 获取存储的行程计划
const tripPlan = ref<TripPlan | null>(null)

onMounted(() => {
  const stored = sessionStorage.getItem('tripPlan')
  if (stored) {
    try {
      tripPlan.value = JSON.parse(stored)
      nextTick(() => {
        initMap()
      })
    } catch (e) {
      message.error('行程数据加载失败')
      router.push({ name: 'home' })
    }
  } else {
    message.warning('请先创建行程计划')
    router.push({ name: 'home' })
  }
})

// 总景点数
const totalAttractions = computed(() => {
  if (!tripPlan.value?.days) return 0
  return tripPlan.value.days.reduce((sum, day) => sum + (day.attractions?.length || 0), 0)
})

// 获取餐饮类型标签
const getMealTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    breakfast: '🌅 早餐',
    lunch: '☀️ 午餐',
    dinner: '🌙 晚餐',
    snack: '🍿 小吃'
  }
  return labels[type] || type
}

// 初始化地图
const initMap = async () => {
  if (!tripPlan.value?.days?.length || !mapContainer.value) return

  try {
    // 动态加载高德地图JS API
    const AMap = await loadAMap()

    // 计算地图中心点（所有景点的平均位置）
    let totalLng = 0, totalLat = 0, count = 0
    tripPlan.value.days.forEach(day => {
      day.attractions?.forEach(attr => {
        if (attr.location?.longitude && attr.location?.latitude) {
          totalLng += attr.location.longitude
          totalLat += attr.location.latitude
          count++
        }
      })
    })

    const center = count > 0
      ? [totalLng / count, totalLat / count]
      : [116.397128, 39.916527] // 默认北京中心

    map = new AMap.Map(mapContainer.value, {
      zoom: 12,
      center,
      viewMode: '2D'
    })

    // 添加标记
    addMarkers()
  } catch (error) {
    console.error('地图加载失败:', error)
    showMapPlaceholder('地图加载失败，请检查网络连接或配置正确的API密钥')
  }
}

// 显示地图占位图
const showMapPlaceholder = (msg: string) => {
  if (mapContainer.value) {
    mapContainer.value.innerHTML = `
      <div style="display:flex;justify-content:center;align-items:center;height:100%;background:#f5f5f5;border-radius:8px;">
        <div style="text-align:center;color:#999;">
          <div style="font-size:48px;margin-bottom:12px;">🗺️</div>
          <div>${msg}</div>
        </div>
      </div>
    `
  }
}

// 加载高德地图
const loadAMap = (): Promise<any> => {
  return new Promise((resolve, reject) => {
    if ((window as any).AMap) {
      resolve((window as any).AMap)
      return
    }

    const amapKey = import.meta.env.VITE_AMAP_JS_KEY || ''
    const amapSecurityCode = import.meta.env.VITE_AMAP_SECURITY_CODE || ''

    // 高德地图 JS API v2.0 安全密钥配置
    if (amapSecurityCode) {
      (window as any)._AMapSecurityConfig = {
        securityJsCode: amapSecurityCode
      }
    }

    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${amapKey}`
    script.onload = () => {
      const checkAMap = () => {
        const AMap = (window as any).AMap
        if (AMap) {
          resolve(AMap)
        } else {
          setTimeout(checkAMap, 100)
        }
      }
      checkAMap()
    }
    script.onerror = () => reject(new Error('高德地图脚本加载失败'))
    document.head.appendChild(script)
  })
}

// 添加标记和路线
const addMarkers = () => {
  if (!map || !tripPlan.value) return

  // 清除已有标记和路线
  markers.forEach(m => map.remove(m))
  markers = []

  const AMap = (window as any).AMap
  if (!AMap) return

  // 每天使用不同颜色
  const dayColors = ['#1890ff', '#52c41a', '#faad14', '#722ed1', '#eb2f96', '#13c2c2']

  tripPlan.value.days.forEach((day, dayIdx) => {
    const color = dayColors[dayIdx % dayColors.length]
    const pathPoints: any[] = []

    day.attractions?.forEach((attr, attrIdx) => {
      if (attr.location?.longitude && attr.location?.latitude) {
        const marker = new AMap.Marker({
          position: [attr.location.longitude, attr.location.latitude],
          title: attr.name,
          label: {
            content: `${dayIdx + 1}-${attrIdx + 1}`,
            direction: 'top'
          }
        })
        map.add(marker)
        markers.push(marker)
        pathPoints.push([attr.location.longitude, attr.location.latitude])
      }
    })

    // 绘制当天路线
    if (pathPoints.length >= 2) {
      const polyline = new AMap.Polyline({
        path: pathPoints,
        strokeColor: color,
        strokeWeight: 4,
        strokeOpacity: 0.8,
        strokeStyle: 'solid',
        lineJoin: 'round'
      })
      map.add(polyline)
      markers.push(polyline)
    }
  })
}

// 图片加载失败处理
const onImageError = (e: Event) => {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
}

// 侧边栏锚点跳转
const scrollToSection = ({ key }: { key: string }) => {
  activeSection.value = key
  const element = document.getElementById(key)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 返回首页
const goBack = () => {
  router.push({ name: 'home' })
}

// 切换编辑模式
const toggleEditMode = () => {
  if (!editMode.value) {
    // 进入编辑模式，保存原始副本
    originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
  }
  editMode.value = !editMode.value
}

// 移动景点
const moveAttraction = (dayIndex: number, attractionIndex: number, direction: 'up' | 'down') => {
  if (!tripPlan.value?.days[dayIndex]?.attractions) return
  const attractions = tripPlan.value.days[dayIndex].attractions
  const newIndex = direction === 'up' ? attractionIndex - 1 : attractionIndex + 1

  if (newIndex >= 0 && newIndex < attractions.length) {
    // 交换位置
    const temp = attractions[attractionIndex]
    attractions[attractionIndex] = attractions[newIndex]
    attractions[newIndex] = temp
  }
}

// 删除景点
const deleteAttraction = (dayIndex: number, attractionIndex: number) => {
  if (!tripPlan.value?.days[dayIndex]?.attractions) return
  tripPlan.value.days[dayIndex].attractions.splice(attractionIndex, 1)
  message.success('景点已删除')
}

// 保存修改
const saveChanges = () => {
  editMode.value = false
  // 更新sessionStorage
  if (tripPlan.value) {
    sessionStorage.setItem('tripPlan', JSON.stringify(tripPlan.value))
  }
  // 重新初始化地图
  nextTick(() => {
    addMarkers()
  })
  message.success('修改已保存')
}

// 取消编辑
const cancelEdit = () => {
  if (originalPlan.value) {
    tripPlan.value = JSON.parse(JSON.stringify(originalPlan.value))
  }
  editMode.value = false
  nextTick(() => {
    addMarkers()
  })
}

// 导出为图片
const exportAsImage = async () => {
  exporting.value = true
  try {
    // 临时隐藏地图以避免导出问题
    const mapEl = document.getElementById('map')
    const originalDisplay = mapEl?.style.display
    if (mapEl) mapEl.style.display = 'none'

    const element = document.getElementById('trip-plan-content')
    if (!element) {
      message.error('导出失败：找不到内容元素')
      return
    }

    const canvas = await html2canvas(element, {
      backgroundColor: '#ffffff',
      scale: 2,
      useCORS: true,
      allowTaint: true,
      logging: false
    })

    // 恢复地图
    if (mapEl && originalDisplay !== undefined) {
      mapEl.style.display = originalDisplay || ''
    }

    const link = document.createElement('a')
    link.download = `${tripPlan.value?.city || '旅行'}计划.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    message.success('导出成功！')
  } catch (error) {
    message.error('导出失败，请重试')
    console.error(error)
  } finally {
    exporting.value = false
  }
}

// 导出为PDF
const exportAsPDF = async () => {
  exporting.value = true
  try {
    // 临时隐藏地图
    const mapEl = document.getElementById('map')
    const originalDisplay = mapEl?.style.display
    if (mapEl) mapEl.style.display = 'none'

    const element = document.getElementById('trip-plan-content')
    if (!element) {
      message.error('导出失败：找不到内容元素')
      return
    }

    const canvas = await html2canvas(element, {
      backgroundColor: '#ffffff',
      scale: 2,
      useCORS: true,
      allowTaint: true,
      logging: false
    })

    // 恢复地图
    if (mapEl && originalDisplay !== undefined) {
      mapEl.style.display = originalDisplay || ''
    }

    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const imgWidth = 210 // A4宽度mm
    const imgHeight = (canvas.height * imgWidth) / canvas.width

    pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight)
    pdf.save(`${tripPlan.value?.city || '旅行'}计划.pdf`)
    message.success('PDF导出成功！')
  } catch (error) {
    message.error('PDF导出失败，请重试')
    console.error(error)
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.result-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  background: #f5f5f5;
}

.result-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 30px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.result-header h1 {
  font-size: 28px;
  font-weight: bold;
  color: #1890ff;
  margin-bottom: 8px;
}

.result-header p {
  color: #666;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  border-radius: 20px;
}

.sidebar-col {
  position: sticky;
  top: 20px;
}

.sidebar-menu {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.suggestions {
  color: #666;
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
}

.map-container {
  width: 100%;
  height: 450px;
  border-radius: 8px;
  overflow: hidden;
}

.day-plan {
  margin-bottom: 20px;
}

.day-card {
  border-radius: 12px;
}

.day-title {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.day-badge {
  background: #1890ff;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: bold;
}

.day-date {
  color: #666;
  font-size: 14px;
}

.day-desc {
  color: #333;
  font-size: 15px;
  font-weight: 500;
}

.hotel-info {
  margin-bottom: 16px;
  padding: 12px;
  background: #e6f7ff;
  border-radius: 8px;
}

.hotel-address {
  color: #666;
  font-size: 13px;
  margin-left: 8px;
}

.hotel-price {
  color: #cf1322;
  font-weight: bold;
  font-size: 14px;
  margin-left: 8px;
}

.attractions-list {
  margin-top: 16px;
}

.attractions-list h4 {
  font-size: 16px;
  margin-bottom: 12px;
  color: #333;
}

.attraction-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.attraction-content {
  flex: 1;
}

.attraction-name {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #333;
}

.attraction-address {
  color: #888;
  font-size: 13px;
  margin-bottom: 4px;
}

.attraction-desc {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 8px;
}

.attraction-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
}

.attraction-image {
  width: 200px;
  height: 130px;
  object-fit: cover;
  border-radius: 8px;
  margin-top: 8px;
}

.edit-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 80px;
}

.meals-list {
  margin-top: 20px;
}

.meals-list h4 {
  font-size: 16px;
  margin-bottom: 12px;
  color: #333;
}

.meal-card {
  text-align: center;
  border-radius: 8px;
}

.meal-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.meal-cost {
  color: #cf1322;
  font-weight: bold;
}

.weather-card {
  text-align: center;
  border-radius: 8px;
}

.weather-content {
  font-size: 14px;
  line-height: 1.8;
}

.weather-label {
  font-weight: 500;
  color: #333;
}

.edit-actions {
  display: flex;
  justify-content: center;
  margin: 30px 0;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.export-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}
</style>
