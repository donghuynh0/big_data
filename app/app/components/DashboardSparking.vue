<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'

// WebSocket connection
let socket: Socket | null = null
const connectionStatus = ref('Connecting...')
const isConnected = ref(false)

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
  }>,
  floors: {} as Record<string, Array<{
    location: string
    license_plate: string
  }>>,
  timestamp: ''
})

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
  socket = io('http://localhost:8000', {
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
    parkingData.value = data
  })
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('vi-VN').format(num)
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

// Lifecycle hooks
onMounted(() => {
  connectWebSocket()

  // Fetch initial data
  fetch('http://localhost:8000/api/data')
    .then(res => res.json())
    .then(data => {
      parkingData.value = data
    })
    .catch(err => console.error('Error loading initial data:', err))
})

onUnmounted(() => {
  if (socket) {
    socket.disconnect()
  }
})
</script>

<template>
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
            <div class="vehicles-table">
              <div class="table-header">
                <div class="table-cell">License Plate</div>
                <div class="table-cell">Location</div>
                <div class="table-cell">Customer</div>
                <div class="table-cell">Time (min)</div>
                <div class="table-cell">Fee (VND)</div>
              </div>
              <div v-for="vehicle in parkingData.vehicles.slice(0, 10)" :key="vehicle.license_plate"
                   class="table-row"
                   @click="navigateTo(`/car/${vehicle.license_plate}`)"
                   style="cursor: pointer;">
                <div class="table-cell">{{ vehicle.license_plate }}</div>
                <div class="table-cell">{{ vehicle.location }}</div>
                <div class="table-cell">{{ vehicle.customer_name }}</div>
                <div class="table-cell">{{ vehicle.minutes }}</div>
                <div class="table-cell fee-cell">{{ formatNumber(vehicle.fee) }}</div>
              </div>
              <div v-if="parkingData.vehicles.length === 0" class="table-row empty">
                <div class="table-cell" style="grid-column: 1 / -1; text-align: center;">No vehicles currently parked</div>
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
  </div>
</template>

<style>
@import "../../assets/css/main.css";
</style>
