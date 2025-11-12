<template>
  <div class="detail-container">
    <!-- Top Navigation Bar -->
    <nav class="navbar">
      <div class="nav-left">
        <button class="brand-btn" @click="navigateTo('/')">Parkzone</button>
        <div class="nav-buttons">
          <button class="nav-btn" @click="navigateTo('/')">Dashboard</button>
        </div>
      </div>
      <div class="nav-right">
        <button class="icon-btn">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="1.5"/>
            <path d="m15 15-3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
        <button class="icon-btn">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 2a6 6 0 0 1 6 6c0 4-6 8-6 8s-6-4-6-8a6 6 0 0 1 6-6Z" stroke="currentColor" stroke-width="1.5"/>
            <circle cx="10" cy="8" r="2" fill="currentColor"/>
          </svg>
        </button>
        <button class="icon-btn">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="3" stroke="currentColor" stroke-width="1.5"/>
          </svg>
        </button>
        <div class="user-profile">
          <div class="avatar">DH</div>
          <div class="user-info">
            <div class="user-name">Danny Hor</div>
            <div class="user-role">Parking use</div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <div class="detail-content">
      <!-- Left Section: Car Info -->
      <div class="car-info-section">
        <div class="info-grid">
          <div class="info-item">
            <label>Area name</label>
            <div class="info-value">{{ areaName }}</div>
          </div>
          <div class="info-item">
            <label>Customer name</label>
            <div class="info-value">{{ customerName }}</div>
          </div>
          <div class="info-item">
            <label>Areas</label>
            <div class="info-value">{{ area }}</div>
          </div>
        </div>

        <div class="info-grid mt-4">
          <div class="info-item">
            <label>Type car</label>
            <div class="info-value">{{ carType }}</div>
          </div>
          <div class="info-item">
            <label>Parking code</label>
            <div class="info-value">{{ parkingCode }}</div>
          </div>
          <div class="info-item">
            <label>Address</label>
            <div class="info-value">{{ address }}</div>
          </div>
        </div>

        <!-- Car Image -->
        <div class="car-image-container">
          <img src="/img/car.png" alt="Car" class="car-detail-image" />
        </div>

        <!-- Stats Cards -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-header">
              <span>Active user</span>
              <button class="menu-btn">...</button>
            </div>
            <div class="stat-value">
              {{ stats.activeUsers }} <span class="stat-change positive">{{ stats.activeUsersChange }}</span>
            </div>
            <div class="stat-chart">
              <div class="mini-chart" v-for="(bar, i) in 40" :key="i" :style="{ height: `${Math.random() * 100}%` }"></div>
            </div>
            <div class="stat-time">08:00 - 10:00</div>
          </div>

          <div class="stat-card">
            <div class="stat-header">
              <span>Bookings Today</span>
              <button class="menu-btn">...</button>
            </div>
            <div class="stat-value">
              {{ stats.bookingsToday }} <span class="stat-change positive">{{ stats.bookingsTodayChange }}</span>
            </div>
            <div class="stat-chart">
              <div class="mini-chart" v-for="(bar, i) in 40" :key="i" :style="{ height: `${Math.random() * 100}%` }"></div>
            </div>
            <div class="stat-time">00:00 - 00:00</div>
          </div>

          <div class="stat-card">
            <div class="stat-header">
              <span>Available Spaces</span>
              <button class="menu-btn">...</button>
            </div>
            <div class="stat-value">
              {{ stats.availableSpaces }} <span class="stat-change negative">{{ stats.availableSpacesChange }}</span>
            </div>
            <div class="stat-chart">
              <div class="mini-chart" v-for="(bar, i) in 40" :key="i" :style="{ height: `${Math.random() * 100}%` }"></div>
            </div>
            <div class="stat-time">09:00 - 23:00</div>
          </div>
        </div>
      </div>

      <!-- Right Section: Analytics -->
      <div class="analytics-section">
        <!-- Parking Fee Details -->
        <div class="panel-card">
          <div class="panel-header">
            <h3>Parking Fee Details</h3>
            <div class="fee-rate-badge">{{ formatNumber(vehicleData?.hourly_rate || 12000) }} {{ vehicleData?.currency || 'VND' }}/hour</div>
          </div>
          <div class="fee-breakdown">
            <div class="fee-row">
              <span class="fee-label">Entry Time:</span>
              <span class="fee-value">{{ formatDateTime(vehicleData?.entry_timestamp) }}</span>
            </div>
            <div class="fee-row">
              <span class="fee-label">Current Time:</span>
              <span class="fee-value">{{ formatDateTime(vehicleData?.current_timestamp) }}</span>
            </div>
            <div class="fee-row">
              <span class="fee-label">Duration:</span>
              <span class="fee-value highlight">{{ vehicleData?.minutes?.toFixed(2) || 0 }} minutes</span>
            </div>
            <div class="fee-row">
              <span class="fee-label">Car Type:</span>
              <span class="fee-value">{{ vehicleData?.car_type || 'Normal' }}</span>
            </div>
            <div class="fee-row">
              <span class="fee-label">Area:</span>
              <span class="fee-value">{{ vehicleData?.area || 'Unknown' }}</span>
            </div>
            <div class="fee-row">
              <span class="fee-label">Status:</span>
              <span :class="['status-badge', vehicleData?.parking_status?.toLowerCase()]">
                {{ vehicleData?.parking_status || 'Unknown' }}
              </span>
            </div>
            <div class="fee-row total">
              <span class="fee-label">Total Fee:</span>
              <span class="fee-value-large">{{ formatNumber(vehicleData?.fee || 0) }} {{ vehicleData?.currency || 'VND' }}</span>
            </div>
          </div>
          <div class="fee-chart-info">
            <p class="fee-note">💡 Fee is calculated based on parking duration at {{ formatNumber(vehicleData?.hourly_rate || 12000) }} {{ vehicleData?.currency || 'VND' }} per hour</p>
          </div>
        </div>

        <!-- Parking Zone -->
        <div class="panel-card mt-4">
          <div class="panel-header">
            <h3>Parking zone</h3>
            <button class="menu-btn">...</button>
          </div>
          <div class="parking-zone-chart">
            <div class="circular-progress">
              <svg viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="80" fill="none" stroke="#e0e0e0" stroke-width="20" />
                <circle cx="100" cy="100" r="80" fill="none" stroke="#4A90E2" stroke-width="20"
                  :stroke-dasharray="`${parkingZone.parking} ${100 - parkingZone.parking}`"
                  stroke-linecap="round" transform="rotate(-90 100 100)" />
                <circle cx="100" cy="100" r="80" fill="none" stroke="#9E9E9E" stroke-width="20"
                  :stroke-dasharray="`${parkingZone.permits} ${100 - parkingZone.permits}`"
                  :stroke-dashoffset="`-${parkingZone.parking}`"
                  stroke-linecap="round" transform="rotate(-90 100 100)" />
                <circle cx="100" cy="100" r="80" fill="none" stroke="#4CAF50" stroke-width="20"
                  :stroke-dasharray="`${parkingZone.booking} ${100 - parkingZone.booking}`"
                  :stroke-dashoffset="`-${parkingZone.parking + parkingZone.permits}`"
                  stroke-linecap="round" transform="rotate(-90 100 100)" />
              </svg>
              <div class="circular-progress-value">
                {{ parkingZone.total }}%
                <div class="circular-progress-label">vs last month</div>
              </div>
            </div>
          </div>
          <div class="parking-zone-legend">
            <div class="legend-item">
              <span class="legend-color parking"></span>
              <span class="legend-label">Parking ({{ parkingZone.parking }}%)</span>
              <span class="legend-value">{{ parkingZone.parkingSlots }} slots</span>
            </div>
            <div class="legend-item">
              <span class="legend-color permits"></span>
              <span class="legend-label">Permits ({{ parkingZone.permits }}%)</span>
              <span class="legend-value">{{ parkingZone.permitsSlots }} slots</span>
            </div>
            <div class="legend-item">
              <span class="legend-color booking"></span>
              <span class="legend-label">Booking ({{ parkingZone.booking }}%)</span>
              <span class="legend-value">{{ parkingZone.bookingSlots }} slots</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'

const route = useRoute()
const licensePlate = route.params.id as string

// WebSocket connection
let socket: Socket | null = null
const isConnected = ref(false)

// Vehicle data
const vehicleData = ref<any>(null)
const parkingData = ref({
  stats: {
    total_parked: 0,
    total_fee: 0,
    available_spots: 84
  },
  vehicles: [] as Array<{
    license_plate: string
    location: string
    minutes: number
    fee: number
    customer_name: string
    area: string
    car_type: string
    floor?: string
    parking_status?: string
    currency?: string
    hourly_rate?: number
  }>,
  timestamp: ''
})

// Computed properties
const areaName = computed(() => vehicleData.value?.location?.substring(0, 1) === 'A' ? 'Duck Bowl' :
                                 vehicleData.value?.location?.substring(0, 1) === 'B' ? 'City Center' :
                                 vehicleData.value?.location?.substring(0, 1) === 'C' ? 'Mall Area' : 'Station Plaza')
const customerName = computed(() => vehicleData.value?.customer_name || 'Unknown')
const area = computed(() => vehicleData.value?.area || 'Unknown')
const carType = computed(() => vehicleData.value?.car_type || 'Normal')
const parkingCode = computed(() => vehicleData.value?.location || 'N/A')
const address = computed(() => {
  const areas: Record<string, string> = {
    'Tokyo': '24,2400 TKY',
    'Osaka': '15,1500 OSK',
    'Kyoto': '30,3000 KYT',
    'Yokohama': '22,2200 YKH',
    'Nagoya': '18,1800 NGY',
    'Sapporo': '12,1200 SPR',
    'Fukuoka': '25,2500 FKO',
    'Kobe': '20,2000 KBE'
  }
  return areas[area.value] || '00,0000 UNK'
})

const stats = computed(() => ({
  activeUsers: parkingData.value.stats.total_parked,
  activeUsersChange: '(+40)',
  bookingsToday: Math.floor(parkingData.value.stats.total_parked * 1.2),
  bookingsTodayChange: '(+25)',
  availableSpaces: parkingData.value.stats.available_spots,
  availableSpacesChange: '(-20)'
}))

const parkingZone = computed(() => {
  const totalSpots = 84
  const occupied = parkingData.value.stats.total_parked
  const percentage = (occupied / totalSpots) * 100

  return {
    total: percentage.toFixed(2),
    parking: 42,
    parkingSlots: occupied,
    permits: 21,
    permitsSlots: Math.floor(occupied * 0.3),
    booking: 24,
    bookingSlots: Math.floor(occupied * 0.4)
  }
})

// Format number function
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('vi-VN').format(num)
}

// Format datetime function
const formatDateTime = (timestamp: number | undefined) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('vi-VN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// WebSocket functions
const connectWebSocket = () => {
  socket = io('http://192.168.80.101:8000', {
    transports: ['websocket', 'polling']
  })

  socket.on('connect', () => {
    isConnected.value = true
    console.log('✅ Connected to WebSocket server')
  })

  socket.on('disconnect', () => {
    isConnected.value = false
    console.log('❌ Disconnected from WebSocket server')
  })

  socket.on('update', (data) => {
    parkingData.value = data

    // Find the specific vehicle by license plate
    const vehicle = data.vehicles.find((v: any) => v.license_plate === licensePlate)
    if (vehicle) {
      vehicleData.value = vehicle
    }
  })
}

// Lifecycle hooks
onMounted(() => {
  connectWebSocket()

  // Fetch initial data
  fetch('http://192.168.80.101:8000/api/data')
    .then(res => res.json())
    .then(data => {
      parkingData.value = data

      // Find the specific vehicle
      const vehicle = data.vehicles.find((v: any) => v.license_plate === licensePlate)
      if (vehicle) {
        vehicleData.value = vehicle
      }
    })
    .catch(err => console.error('Error loading initial data:', err))
})

onUnmounted(() => {
  if (socket) {
    socket.disconnect()
  }
})
</script>

<style scoped>
.detail-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

/* Navigation Bar */
.navbar {
  background-color: #ffffff;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.brand-btn {
  background-color: #f0f0f0;
  color: #666;
  border: none;
  padding: 0.5rem 1.5rem;
  border-radius: 20px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.brand-btn:hover {
  background-color: #e0e0e0;
}

.nav-buttons {
  display: flex;
  gap: 0.5rem;
}

.nav-btn {
  background-color: transparent;
  color: #666;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 20px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover {
  background-color: #f5f5f5;
}

.nav-btn.active {
  background-color: #000;
  color: #fff;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.icon-btn {
  background-color: transparent;
  border: none;
  color: #666;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.icon-btn:hover {
  background-color: #f5f5f5;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding-left: 1rem;
  border-left: 1px solid #e5e5e5;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: #333;
}

.user-role {
  font-size: 0.75rem;
  color: #999;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 2rem;
  margin-bottom: 1.5rem;
}

.tabs {
  display: flex;
  gap: 1rem;
}

.tab {
  background: none;
  border: none;
  padding: 0.5rem 1rem;
  font-size: 0.95rem;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.tab.active {
  color: #333;
  font-weight: 600;
  border-bottom: 2px solid #333;
}

.add-location-btn {
  background-color: #000;
  color: #fff;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.detail-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-top: 30px;
  padding: 0 2rem 2rem 2rem;
}

.car-info-section {
  background: #fff;
  border-radius: 16px;
  padding: 2rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.info-item label {
  display: block;
  font-size: 0.85rem;
  color: #999;
  margin-bottom: 0.5rem;
}

.info-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.mt-4 {
  margin-top: 2rem;
}

.car-image-container {
  margin: 3rem 0;
  text-align: right;
}

.car-detail-image {
  max-width: 300px;
  width: 100%;
  height: auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-top: 2rem;
}

.stat-card {
  background: #f9f9f9;
  border-radius: 12px;
  padding: 1.25rem;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #666;
}

.menu-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  color: #999;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 1rem;
}

.stat-change {
  font-size: 0.9rem;
  font-weight: 500;
  margin-left: 0.5rem;
}

.stat-change.positive {
  color: #4CAF50;
}

.stat-change.negative {
  color: #F44336;
}

.stat-chart {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 40px;
  margin-bottom: 0.5rem;
}

.mini-chart {
  flex: 1;
  background: #4A90E2;
  border-radius: 2px;
  min-height: 4px;
}

.stat-time {
  font-size: 0.75rem;
  color: #999;
}

.analytics-section {
  display: flex;
  flex-direction: column;
}

.panel-card {
  background: #fff;
  border-radius: 16px;
  padding: 2rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.panel-header h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.fee-rate-badge {
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
  color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.fee-breakdown {
  margin: 1.5rem 0;
}

.fee-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.2s;
}

.fee-row:hover {
  background-color: #f9f9f9;
}

.fee-row.total {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 2px solid #bae6fd;
  border-radius: 8px;
  margin-top: 1rem;
  padding: 1.25rem;
}

.fee-label {
  font-size: 0.95rem;
  color: #666;
  font-weight: 500;
}

.fee-value {
  font-size: 0.95rem;
  color: #333;
  font-weight: 600;
}

.fee-value.highlight {
  color: #4CAF50;
  font-size: 1.1rem;
}

.fee-value-large {
  font-size: 1.8rem;
  font-weight: 700;
  color: #0369a1;
}

.fee-chart-info {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #fffbf0;
  border-left: 4px solid #FFB800;
  border-radius: 4px;
}

.fee-note {
  font-size: 0.85rem;
  color: #666;
  margin: 0;
  line-height: 1.5;
}

.parking-zone-chart {
  display: flex;
  justify-content: center;
  padding: 2rem 0;
}

.circular-progress {
  position: relative;
  width: 200px;
  height: 200px;
}

.circular-progress-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  font-size: 2rem;
  font-weight: 700;
  color: #333;
}

.circular-progress-label {
  font-size: 0.75rem;
  color: #999;
  font-weight: 400;
  margin-top: 0.25rem;
}

.parking-zone-legend {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.legend-color.parking {
  background-color: #4A90E2;
}

.legend-color.permits {
  background-color: #9E9E9E;
}

.legend-color.booking {
  background-color: #4CAF50;
}

.legend-label {
  flex: 1;
  font-size: 0.9rem;
  color: #666;
}

.legend-value {
  font-weight: 600;
  color: #333;
}

/* Fee Section */
.fee-section {
  margin: 2rem 0;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 12px;
  border: 2px solid #bae6fd;
}

.fee-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 1rem;
}

.fee-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.fee-item {
  background: #fff;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.fee-item.highlight {
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
  border: none;
}

.fee-item.highlight label {
  color: #fff;
}

.fee-item label {
  display: block;
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.fee-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.fee-value-large {
  font-size: 1.8rem;
  font-weight: 700;
  color: #48A64C;
}

/* Status Badge Styles */
.status-badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
}

.status-badge.parked {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #81c784;
}

.status-badge.arriving {
  background: #e3f2fd;
  color: #1565c0;
  border: 1px solid #90caf9;
}

.status-badge.leaving {
  background: #fff3e0;
  color: #e65100;
  border: 1px solid #ffcc80;
}

@media (max-width: 768px) {
  .fee-grid {
    grid-template-columns: 1fr;
  }
}
</style>