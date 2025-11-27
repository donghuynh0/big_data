<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { io, Socket } from 'socket.io-client'
import { ToastProvider, ToastRoot, ToastTitle, ToastDescription, ToastViewport } from 'reka-ui'

// WebSocket connection
let socket: Socket | null = null
const connectionStatus = ref('Connecting...')
const isConnected = ref(false)

// Toast state
const toasts = ref<Array<{
  id: string
  title: string
  description: string
  type: 'enter' | 'exit'
}>>([])

// Parking state
const parkingData = ref({
  stats: {
    total_parked: 0,
    total_fee: 0,
    available_spots: 60
  },
  vehicles: [] as Array<{
    license_plate: string
    location: string
    minutes: number
    fee: number
    customer_name?: string
    area?: string
    car_type?: string
    floor?: string
    parking_status?: string
    currency?: string
    hourly_rate?: number
  }>,
  floors: {} as Record<string, Array<{
    location: string
    license_plate: string
  }>>,
  timestamp: ''
})

// History state
const parkingHistory = ref<Array<{
  event_type: string
  license_plate: string
  location: string
  customer_name: string
  area: string
  car_type: string
  fee: number
  minutes: number
  timestamp: string
  parking_status?: string
  currency?: string
  hourly_rate?: number
}>>([])

const historyFilter = ref<'ALL' | 'ENTERING' | 'PARKED' | 'EXITING'>('ALL')
const showHistory = ref(false)

// Previous parking data for comparison
const previousVehicles = ref<Set<string>>(new Set())

const selectedZone = ref('A')
const zones = ['A', 'B', 'C', 'D']
const spotsPerFloor = 21
const selectedSpot = ref<string | null>(null)

// Computed properties
const currentZoneSpots = computed(() => {
  const floorData = parkingData.value.floors[selectedZone.value] || []
  const occupiedSpots: Record<string, any> = {}

  floorData.forEach(spot => {
    occupiedSpots[spot.location] = spot
  })

  const spots = []
  for (let i = 1; i <= spotsPerFloor; i++) {
    const spotLocation = `${selectedZone.value}${i}`
    const spotData = occupiedSpots[spotLocation]

    if (spotData) {
      const vehicleInfo = parkingData.value.vehicles.find(
        v => v.license_plate === spotData.license_plate
      )

      spots.push({
        id: spotLocation,
        occupied: true,
        license_plate: spotData.license_plate,
        minutes: vehicleInfo?.minutes || 0,
        fee: vehicleInfo?.fee || 0
      })
    } else {
      spots.push({
        id: spotLocation,
        occupied: false,
        license_plate: null,
        minutes: 0,
        fee: 0
      })
    }
  }

  return spots
})

const parkingStats = computed(() => {
  return zones.map(zone => {
    const occupied = (parkingData.value.floors[zone] || []).length
    const percentage = (occupied / spotsPerFloor) * 100
    return {
      label: `Zone ${zone}`,
      value: percentage,
      occupied: occupied,
      total: spotsPerFloor,
      color: percentage > 50 ? '#FFB800' : '#E5E5E5'
    }
  })
})

// WebSocket functions
const connectWebSocket = () => {
  socket = io('http://192.168.80.101:8000', {
    transports: ['websocket', 'polling']
  })

  socket.on('connect', () => {
    connectionStatus.value = 'Connected'
    isConnected.value = true
    console.log('✅ Connected to WebSocket server')
  })

  socket.on('disconnect', () => {
    connectionStatus.value = 'Disconnected'
    isConnected.value = false
    console.log('❌ Disconnected from WebSocket server')
  })

  socket.on('update', (data) => {
    // Detect parking events before updating
    if (parkingData.value.vehicles.length > 0) {
      detectParkingEvents(data.vehicles)
    }
    parkingData.value = data
  })
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('vi-VN').format(num)
}

// Toast functions
const addToast = (title: string, description: string, type: 'enter' | 'exit') => {
  const id = `toast-${Date.now()}-${Math.random()}`
  toasts.value.push({ id, title, description, type })
  
  // Auto remove toast after 5 seconds
  setTimeout(() => {
    removeToast(id)
  }, 5000)
}

const removeToast = (id: string) => {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

// Detect parking events
const detectParkingEvents = (newVehicles: Array<any>) => {
  const currentVehicles = new Set(newVehicles.map(v => v.license_plate))
  
  // Check for new vehicles (parked)
  currentVehicles.forEach(plate => {
    if (!previousVehicles.value.has(plate)) {
      const vehicle = newVehicles.find(v => v.license_plate === plate)
      if (vehicle) {
        addToast(
          '🚗 Vehicle Parked',
          `${vehicle.license_plate} parked at ${vehicle.location}`,
          'enter'
        )
      }
    }
  })
  
  // Check for removed vehicles (exiting)
  previousVehicles.value.forEach(plate => {
    if (!currentVehicles.has(plate)) {
      addToast(
        '🚙 Vehicle Exiting',
        `${plate} is leaving the parking lot`,
        'exit'
      )
    }
  })
  
  // Update previous vehicles
  previousVehicles.value = currentVehicles
}

const selectZone = (zone: string) => {
  selectedZone.value = zone
  selectedSpot.value = null
}

const selectSpot = (spotId: string) => {
  selectedSpot.value = selectedSpot.value === spotId ? null : spotId
}

const navigateToDetail = (spot: any) => {
  if (spot.occupied && spot.license_plate) {
    navigateTo(`/car/${spot.license_plate}`)
  }
}

// History functions
const fetchParkingHistory = async () => {
  try {
    const response = await fetch('http://192.168.80.101:8000/api/history?limit=100')
    const data = await response.json()
    parkingHistory.value = data.history || []
    console.log('📋 Loaded parking history:', parkingHistory.value.length, 'entries')
  } catch (err) {
    console.error('Error loading parking history:', err)
  }
}

const filteredHistory = computed(() => {
  if (historyFilter.value === 'ALL') {
    return parkingHistory.value
  }
  return parkingHistory.value.filter(item => item.event_type === historyFilter.value)
})

const toggleHistory = () => {
  showHistory.value = !showHistory.value
  if (showHistory.value) {
    fetchParkingHistory()
  }
}

const setHistoryFilter = (filter: 'ALL' | 'ENTERING' | 'PARKED' | 'EXITING') => {
  historyFilter.value = filter
}

const getEventBadgeClass = (eventType: string) => {
  if (eventType === 'ENTERING') return 'badge-entering'
  if (eventType === 'PARKED') return 'badge-parked'
  if (eventType === 'EXITING') return 'badge-exiting'
  return 'badge-entering'
}

// Lifecycle hooks
onMounted(() => {
  connectWebSocket()

  // Fetch initial data
  fetch('http://192.168.80.101:8000/api/data')
    .then(res => res.json())
    .then(data => {
      parkingData.value = data
      // Initialize previous vehicles set
      previousVehicles.value = new Set(data.vehicles.map((v: any) => v.license_plate))
    })
    .catch(err => console.error('Error loading initial data:', err))
  
  // Fetch history
  fetchParkingHistory()
})

onUnmounted(() => {
  if (socket) {
    socket.disconnect()
  }
})
</script>

<template>
  <ToastProvider>
    <div class="dashboard-container">
      <!-- Top Navigation Bar -->
    <nav class="navbar">
      <div class="nav-left">
        <button class="brand-btn">Parkzone</button>
        <div class="nav-buttons">
          <button class="nav-btn active">Dashboard</button>
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
          <div class="avatar">NV</div>
          <div class="user-info">
            <div class="user-name">Nhan Vo</div>
            <div class="user-role">Parking use</div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Left Section -->
      <div class="left-section">
        <div class="parking-card">
          <h2 class="card-title">Downtown Plaza Parking</h2>

          <!-- Zone Selection -->
          <div class="zone-buttons">
            <button
              v-for="zone in zones"
              :key="zone"
              :class="['zone-btn', { active: selectedZone === zone }]"
              @click="selectZone(zone)"
            >
              Zone {{ zone }}
            </button>
          </div>

          <!-- Parking Grid -->
          <div class="parking-grid">
            <div
              v-for="spot in currentZoneSpots"
              :key="spot.id"
              :class="['parking-spot', {
                occupied: spot.occupied,
                selected: selectedSpot === spot.id
              }]"
              :title="spot.occupied ? `${spot.license_plate} - ${spot.minutes} min - ${formatNumber(spot.fee)} VND - Double click to view details` : 'Available'"
              @click="selectSpot(spot.id)"
              @dblclick="navigateToDetail(spot)"
            >
              <div class="spot-label">{{ spot.id }}</div>
              <img v-if="spot.occupied" src="/img/car.png" class="car-icon" alt="Car" />
            </div>
          </div>

          <!-- Additional Info Cards -->
          <div class="info-cards">
            <div class="info-card">
              <h3>Current parked</h3>
              <p class="count">{{ parkingData.stats.total_parked }}</p>
              <p class="sub-text">vehicles</p>
            </div>
            <div class="info-card">
              <h3>Total Parking Fee</h3>
              <p class="count fee">{{ formatNumber(parkingData.stats.total_fee) }}</p>
              <p class="sub-text">VND</p>
            </div>
            <div class="info-card">
              <h3>Available Spots</h3>
              <p class="count">{{ parkingData.stats.available_spots }}</p>
              <p class="sub-text">spots remaining</p>
            </div>
          </div>

          <!-- Vehicles List with Fees -->
          <div class="vehicles-list">
            <h3 class="section-title">Parked Vehicles Details</h3>
            <div class="vehicles-table-wrapper">
              <div class="vehicles-table">
                <div class="table-header">
                  <div class="table-cell">License Plate</div>
                  <div class="table-cell">Location</div>
                  <div class="table-cell">Customer</div>
                  <div class="table-cell">Area</div>
                  <div class="table-cell">Car Type</div>
                  <div class="table-cell">Status</div>
                  <div class="table-cell">Time (min)</div>
                  <div class="table-cell">Fee</div>
                </div>
                <div class="table-body">
                  <div v-for="vehicle in parkingData.vehicles" :key="vehicle.license_plate"
                       class="table-row"
                       @click="navigateTo(`/car/${vehicle.license_plate}`)"
                       style="cursor: pointer;">
                    <div class="table-cell">{{ vehicle.license_plate }}</div>
                    <div class="table-cell">{{ vehicle.location }}</div>
                    <div class="table-cell">{{ vehicle.customer_name }}</div>
                    <div class="table-cell">{{ vehicle.area }}</div>
                    <div class="table-cell">{{ vehicle.car_type }}</div>
                    <div class="table-cell">
                      <span :class="['status-badge', vehicle.parking_status?.toLowerCase()]">
                        {{ vehicle.parking_status }}
                      </span>
                    </div>
                    <div class="table-cell">{{ vehicle.minutes?.toFixed(2) }}</div>
                    <div class="table-cell fee-cell">{{ formatNumber(vehicle.fee) }} {{ vehicle.currency || 'VND' }}</div>
                  </div>
                  <div v-if="parkingData.vehicles.length === 0" class="table-row empty">
                    <div class="table-cell" style="grid-column: 1 / -1; text-align: center;">No vehicles currently parked</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Parking History Section -->
          <div class="history-section">
            <div class="history-header">
              <h3 class="section-title">Parking History</h3>
              <button class="toggle-history-btn" @click="toggleHistory">
                {{ showHistory ? 'Hide History' : 'Show History' }}
              </button>
            </div>

            <div v-if="showHistory" class="history-content">
              <!-- Filter Tabs -->
              <div class="history-filters">
                <button 
                  :class="['filter-btn', { active: historyFilter === 'ALL' }]"
                  @click="setHistoryFilter('ALL')"
                >
                  All Events
                </button>
                <button 
                  :class="['filter-btn', { active: historyFilter === 'ENTERING' }]"
                  @click="setHistoryFilter('ENTERING')"
                >
                  Entering
                </button>
                <button 
                  :class="['filter-btn', { active: historyFilter === 'PARKED' }]"
                  @click="setHistoryFilter('PARKED')"
                >
                  Parked
                </button>
                <button 
                  :class="['filter-btn', { active: historyFilter === 'EXITING' }]"
                  @click="setHistoryFilter('EXITING')"
                >
                  Exiting
                </button>
              </div>

              <!-- History Table -->
              <div class="history-table-wrapper">
                <div class="history-table">
                  <div class="table-header">
                    <div class="table-cell">Event</div>
                    <div class="table-cell">License Plate</div>
                    <div class="table-cell">Location</div>
                    <div class="table-cell">Customer</div>
                    <div class="table-cell">Area</div>
                    <div class="table-cell">Car Type</div>
                    <div class="table-cell">Status</div>
                    <div class="table-cell">Duration</div>
                    <div class="table-cell">Fee</div>
                    <div class="table-cell">Time</div>
                  </div>
                  <div class="table-body">
                    <div v-for="(item, index) in filteredHistory" :key="index" class="table-row">
                      <div class="table-cell">
                        <span :class="['event-badge', getEventBadgeClass(item.event_type)]">
                          {{ item.event_type }}
                        </span>
                      </div>
                      <div class="table-cell">{{ item.license_plate }}</div>
                      <div class="table-cell">{{ item.location }}</div>
                      <div class="table-cell">{{ item.customer_name }}</div>
                      <div class="table-cell">{{ item.area }}</div>
                      <div class="table-cell">{{ item.car_type }}</div>
                      <div class="table-cell">
                        <span :class="['status-badge', item.parking_status?.toLowerCase()]">
                          {{ item.parking_status || '-' }}
                        </span>
                      </div>
                      <div class="table-cell">{{ item.minutes?.toFixed(2) || 0 }} min</div>
                      <div class="table-cell fee-cell">{{ item.fee > 0 ? formatNumber(item.fee) + ' ' + (item.currency || 'VND') : '-' }}</div>
                      <div class="table-cell">{{ item.timestamp }}</div>
                    </div>
                    <div v-if="filteredHistory.length === 0" class="table-row empty">
                      <div class="table-cell" style="grid-column: 1 / -1; text-align: center;">No history records</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Section -->
      <div class="right-section">
        <!-- Parking Overview -->
        <div class="panel-card">
          <h3 class="panel-title">Parking Overview</h3>
          <div class="chart-container">
            <div class="bar-chart">
              <div
                v-for="stat in parkingStats"
                :key="stat.label"
                class="bar-item"
              >
                <div class="bar-wrapper">
                  <div
                    class="bar"
                    :style="{ height: `${Math.max(stat.value, 10)}%`, backgroundColor: stat.color }"
                  ></div>
                </div>
                <span class="bar-label">{{ stat.label }}</span>
              </div>
            </div>
          </div>
          <div class="overview-stats">
            <div class="stat-item">
              <svg class="stat-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 2C5.24 2 3 4.24 3 7c0 3.5 5 7 5 7s5-3.5 5-7c0-2.76-2.24-5-5-5z" stroke="currentColor" stroke-width="1.5"/>
                <circle cx="8" cy="7" r="1.5" fill="currentColor"/>
              </svg>
              <div>
                <div class="stat-label">Most used zone</div>
                <div class="stat-value">Zone A</div>
              </div>
            </div>
            <div class="stat-item">
              <div>
                <div class="stat-label">Avg parking</div>
                <div class="stat-value">2h 15m</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Nearby Parking Options -->
        <div class="panel-card">
          <h3 class="panel-title">Nearby Parking Options</h3>
          <div class="nearby-list">
            <div class="nearby-item">
              <div class="nearby-info">
                <div class="nearby-name">City Center Parking</div>
                <div class="nearby-distance">0.5 km away</div>
              </div>
              <div class="nearby-status available">12 spots</div>
            </div>
            <div class="nearby-item">
              <div class="nearby-info">
                <div class="nearby-name">Mall Parking Lot</div>
                <div class="nearby-distance">1.2 km away</div>
              </div>
              <div class="nearby-status available">8 spots</div>
            </div>
            <div class="nearby-item">
              <div class="nearby-info">
                <div class="nearby-name">Station Parking</div>
                <div class="nearby-distance">2.1 km away</div>
              </div>
              <div class="nearby-status limited">3 spots</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notifications -->
    <ToastRoot
      v-for="toast in toasts"
      :key="toast.id"
      :class="['toast-notification', toast.type]"
    >
      <ToastTitle class="toast-title">{{ toast.title }}</ToastTitle>
      <ToastDescription class="toast-description">{{ toast.description }}</ToastDescription>
    </ToastRoot>

    <ToastViewport class="toast-viewport" />
  </div>
  </ToastProvider>
</template>

<style>
@import "../../assets/css/main.css";

/* Toast Styles */
.toast-viewport {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 300px;
  max-width: 400px;
  z-index: 9999;
  list-style: none;
  padding: 0;
  margin: 0;
}

.toast-notification {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  animation: slideIn 0.3s ease-out;
  border-left: 4px solid #4CAF50;
}

.toast-notification.enter {
  border-left-color: #4CAF50;
}

.toast-notification.exit {
  border-left-color: #FF9800;
}

.toast-title {
  font-weight: 600;
  font-size: 15px;
  color: #1a1a1a;
  margin: 0;
}

.toast-description {
  font-size: 14px;
  color: #666;
  margin: 0;
}

@keyframes slideIn {
  from {
    transform: translateX(calc(100% + 20px));
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-notification[data-swipe='move'] {
  transform: translateX(var(--reka-toast-swipe-move-x));
}

.toast-notification[data-swipe='cancel'] {
  transform: translateX(0);
  transition: transform 200ms ease-out;
}

.toast-notification[data-swipe='end'] {
  animation: slideOut 200ms ease-out;
}

@keyframes slideOut {
  from {
    transform: translateX(var(--reka-toast-swipe-end-x));
  }
  to {
    transform: translateX(calc(100% + 20px));
  }
}

/* Vehicles Table Wrapper with Scroll */
.vehicles-table-wrapper {
  max-height: 400px;
  overflow-y: auto;
  border-radius: 12px;
  background: white;
  border: 1px solid #e5e5e5;
}

.vehicles-table {
  background-color: #fff;
}

.vehicles-table .table-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: linear-gradient(135deg, #FFD77A 0%, #FFC445 100%);
  color: #333;
  font-weight: 600;
}

.vehicles-table .table-body {
  max-height: 350px;
  overflow-y: auto;
}

.vehicles-table-wrapper::-webkit-scrollbar {
  width: 8px;
}

.vehicles-table-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.vehicles-table-wrapper::-webkit-scrollbar-thumb {
  background: #f1f1f1;
  border-radius: 10px;
}

.vehicles-table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #f1f1f1;
}

/* History Section Styles */
.history-section {
  margin-top: 30px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.toggle-history-btn {
  padding: 8px 20px;
  background: linear-gradient(135deg, #FFD77A 0%, #FFC445 100%);
  color: #333;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-history-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(255, 184, 0, 0.4);
}

.history-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.history-filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 10px;
}

.filter-btn {
  flex: 1;
  padding: 10px 20px;
  background: white;
  border: 2px solid transparent;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-btn:hover {
  background: #f0f0f0;
}

.filter-btn.active {
  background: linear-gradient(135deg, #FFD77A 0%, #FFC445 100%);
  border-color: #FFB800;
  color: #333;
  font-weight: 600;
  box-shadow: 0 4px 10px rgba(255, 184, 0, 0.3);
}

.history-table-wrapper {
  max-height: 500px;
  overflow-y: auto;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.history-table {
  background: white;
}

.history-table .table-body {
  max-height: 450px;
  overflow-y: auto;
}

.history-table-wrapper::-webkit-scrollbar {
  width: 8px;
}

.history-table-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.history-table-wrapper::-webkit-scrollbar-thumb {
  background: #f1f1f1;
  border-radius: 10px;
}

.history-table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #f1f1f1;
}

.history-table .table-header {
  display: grid;
  grid-template-columns: 90px 130px 90px 120px 100px 100px 100px 90px 130px 1fr;
  gap: 8px;
  padding: 15px 20px;
  background: linear-gradient(135deg, #FFD77A 0%, #FFC445 100%);
  color: #333;
  font-weight: 600;
  font-size: 13px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.history-table .table-row {
  display: grid;
  grid-template-columns: 90px 130px 90px 120px 100px 100px 100px 90px 130px 1fr;
  gap: 8px;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s ease;
}

.history-table .table-row:hover {
  background: #f8f9fa;
}

.history-table .table-row:last-child {
  border-bottom: none;
}

.event-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-entering {
  background: #e3f2fd;
  color: #1565c0;
  border: 1px solid #90caf9;
}

.badge-parked {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #81c784;
}

.badge-exiting {
  background: #fff3e0;
  color: #e65100;
  border: 1px solid #ffcc80;
}

.history-table .table-cell {
  display: flex;
  align-items: center;
  font-size: 13px;
}

/* Status Badge Styles */
.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
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

/* Vehicles Table Grid */
.vehicles-table .table-header {
  display: grid;
  grid-template-columns: 130px 90px 120px 100px 100px 100px 100px 140px;
  gap: 10px;
  padding: 15px 20px;
}

.vehicles-table .table-row {
  display: grid;
  grid-template-columns: 130px 90px 120px 100px 100px 100px 100px 140px;
  gap: 10px;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s ease;
}

.vehicles-table .table-row:hover {
  background: #f8f9fa;
}
</style>
