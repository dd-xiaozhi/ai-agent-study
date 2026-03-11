<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'

interface Player {
  name: string
  role: string
  status: 'alive' | 'dead'
  avatar?: string
}

interface Message {
  name: string
  content: string
  role: string // 'system' | 'wolf' | 'villager' | etc.
  timestamp: string
}

const players = ref<Player[]>([])
const messages = ref<Message[]>([])
const connected = ref(false)
const gameStarted = ref(false)
const chatContainer = ref<HTMLElement | null>(null)
const currentPhase = ref('游戏准备')
const currentTask = ref('等待游戏开始...')

// Mock data for initial design preview (will be replaced by WS)
// players.value = [
//   { name: '刘备', role: '未知', status: 'alive' },
//   { name: '曹操', role: '未知', status: 'alive' },
// ]

const connectWebSocket = () => {
  const ws = new WebSocket('ws://localhost:8000/ws')
  
  ws.onopen = () => {
    connected.value = true
    console.log('Connected to server')
  }
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('Received:', data)
      
      if (data.type === 'msg') {
        messages.value.push({
          name: data.name,
          content: data.content,
          role: data.role || 'user',
          timestamp: new Date().toLocaleTimeString()
        })
      } else if (data.type === 'player_update') {
        // Update players list
        // Assuming data.players is a list of player objects
        players.value = data.players
      } else if (data.type === 'system') {
         messages.value.push({
          name: '系统',
          content: data.content,
          role: 'system',
          timestamp: new Date().toLocaleTimeString()
        })
      } else if (data.type === 'phase') {
        currentPhase.value = data.content
        currentTask.value = data.task
      }
    } catch (e) {
      console.error('Error parsing message', e)
    }
  }
  
  ws.onclose = () => {
    connected.value = false
    console.log('Disconnected')
    setTimeout(connectWebSocket, 3000)
  }
}

const startGame = async () => {
  try {
    gameStarted.value = true
    await fetch('http://localhost:8000/start', { method: 'POST' })
  } catch (e) {
    console.error('Failed to start game', e)
    gameStarted.value = false
  }
}

// Auto-scroll to bottom
watch(() => messages.value.length, () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
})

onMounted(() => {
  connectWebSocket()
})

const getRoleColor = (role: string) => {
  if (role === 'system') return 'text-gold-400'
  if (role === 'wolf') return 'text-crimson'
  return 'text-gray-200'
}

const getAvatarColor = (name: string) => {
    // Simple hash for color
    const colors = ['bg-red-700', 'bg-blue-700', 'bg-green-700', 'bg-yellow-700', 'bg-purple-700', 'bg-indigo-700']
    let hash = 0
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash)
    }
    return colors[Math.abs(hash) % colors.length]
}

</script>

<template>
  <div class="flex h-screen w-full bg-ink-900 font-sans overflow-hidden">
    <!-- Left Sidebar: Tasks/Players -->
    <div class="w-80 border-r border-white/10 flex flex-col bg-ink-800">
      <div class="p-4 border-b border-white/10 bg-ink-900/50">
        <h1 class="text-xl font-serif font-bold text-gray-200 tracking-wider flex items-center gap-2">
          <div class="i-carbon-game-console text-gold text-2xl"></div>
          三国狼人杀
        </h1>
        <div class="flex items-center gap-2 mt-2 text-xs">
          <span class="w-2 h-2 rounded-full" :class="connected ? 'bg-green-500' : 'bg-red-500'"></span>
          <span class="text-gray-400">{{ connected ? '已连接' : '断开连接' }}</span>
        </div>
      </div>
      
      <div class="flex-1 overflow-y-auto p-4 space-y-3">
        
        <!-- Task Card -->
        <div class="mb-6 p-4 rounded-lg bg-gradient-to-br from-gold/10 to-transparent border border-gold/30 shadow-lg relative overflow-hidden group">
            <div class="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <div class="i-carbon-task text-4xl text-gold"></div>
            </div>
            <div class="text-xs text-gold-400 font-bold uppercase tracking-widest mb-1">当前阶段</div>
            <div class="text-lg text-gray-200 font-serif font-bold mb-2">{{ currentPhase }}</div>
            <div class="text-sm text-gray-400 leading-relaxed">{{ currentTask }}</div>
        </div>

        <div class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">存活玩家</div>
        
        <div v-for="player in players" :key="player.name" 
             class="group flex items-center gap-3 p-3 rounded-lg border border-white/5 bg-white/5 hover:bg-white/10 transition-all duration-300">
          <div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white shadow-lg"
               :class="[getAvatarColor(player.name), player.status === 'dead' ? 'filter grayscale opacity-50' : '']">
            {{ player.name.substring(0, 1) }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="font-medium text-gray-200 truncate">{{ player.name }}</div>
            <div class="text-xs text-gray-500 truncate flex items-center gap-1">
               <span v-if="player.status === 'dead'" class="text-red-500">[已死亡]</span>
               <span v-else class="text-green-500">[存活]</span>
               <span v-if="player.role && player.role !== '未知'">- {{ player.role }}</span>
            </div>
          </div>
        </div>
        
        <div v-if="players.length === 0" class="text-center py-10 text-gray-600 text-sm">
          等待游戏开始...
        </div>
      </div>
      
      <div class="p-4 border-t border-white/10 bg-ink-900/50">
        <button @click="startGame" :disabled="gameStarted"
                class="w-full py-3 px-4 bg-gradient-to-r from-crimson to-red-900 hover:from-red-600 hover:to-red-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded shadow-lg transition-all duration-300 flex items-center justify-center gap-2">
          <div v-if="!gameStarted" class="i-carbon-play-filled"></div>
          <div v-else class="i-carbon-circle-dash animate-spin"></div>
          {{ gameStarted ? '游戏中...' : '开始游戏' }}
        </button>
      </div>
    </div>

    <!-- Right Main: Output Content -->
    <div class="flex-1 flex flex-col bg-ink-900 relative">
        <!-- Background decoration -->
        <div class="absolute inset-0 bg-[url('https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/dream-ball.png')] opacity-5 pointer-events-none bg-center bg-no-repeat bg-contain filter blur-xl"></div>
        
        <div class="p-4 border-b border-white/10 flex justify-between items-center bg-ink-800/80 backdrop-blur z-10">
            <h2 class="font-serif text-lg text-gray-300">对局记录</h2>
            <div class="text-xs text-gray-500">DeepSeek-V3.2 Powered</div>
        </div>

        <div ref="chatContainer" class="flex-1 overflow-y-auto p-6 space-y-6 z-10 scroll-smooth">
            <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-600 space-y-4">
                <div class="i-carbon-chat text-6xl opacity-20"></div>
                <div>等待消息...</div>
            </div>

            <div v-for="(msg, index) in messages" :key="index" class="animate-fade-in-up">
                <!-- System Message -->
                <div v-if="msg.role === 'system' || msg.name === '游戏主持人'" class="flex justify-center my-4">
                    <div class="bg-white/5 border border-gold/30 text-gold-300 px-4 py-2 rounded-full text-sm font-serif flex items-center gap-2 shadow-[0_0_15px_rgba(197,160,89,0.1)]">
                        <div class="i-carbon-bullhorn"></div>
                        {{ msg.content.replace('📢 ', '') }}
                    </div>
                </div>

                <!-- Player Message -->
                <div v-else class="flex gap-4 max-w-4xl" :class="msg.name === '我' ? 'ml-auto flex-row-reverse' : ''">
                    <div class="flex-shrink-0 flex flex-col items-center gap-1">
                        <div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white shadow-lg border border-white/10"
                             :class="getAvatarColor(msg.name)">
                            {{ msg.name.substring(0, 1) }}
                        </div>
                        <div class="text-[10px] text-gray-500 max-w-[4rem] truncate text-center">{{ msg.name }}</div>
                    </div>
                    
                    <div class="flex flex-col gap-1 min-w-0">
                        <div class="bg-white/10 p-3 rounded-2xl rounded-tl-none text-gray-200 text-sm leading-relaxed shadow-sm border border-white/5 relative group">
                            <!-- Triangle -->
                            <div class="absolute top-0 -left-2 w-0 h-0 border-t-[10px] border-t-white/10 border-l-[10px] border-l-transparent transform rotate-0"></div>
                            
                            {{ msg.content }}
                            
                            <!-- Role badge if known/revealed (optional) -->
                            <!-- <div v-if="msg.role" class="absolute -top-2 -right-2 text-[10px] px-1.5 py-0.5 rounded bg-black/50 text-gray-400 border border-white/10">
                                {{ msg.role }}
                            </div> -->
                        </div>
                        <div class="text-[10px] text-gray-600 px-1">{{ msg.timestamp }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<style>
/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: #1a1a1a; 
}
::-webkit-scrollbar-thumb {
  background: #333; 
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #444; 
}
</style>
