export const state = () => ({
  guild: {},
  config: {},
  player: {},
  queue: [],
  permission: {},
})

export const mutations = {
  set(state, guild) {
    state.guild = Object.assign({}, guild)
  },
  setConfig(state, config) {
    for (const element of Object.keys(config)) {
      if (config[element] === 0) {
        config[element] = null
      }
    }
    state.config = Object.assign({}, config)
  },
  setPlayer(state, player) {
    state.player = Object.assign({}, player)
  },
  incPosition(state, amount) {
    state.player = Object.assign({}, state.player, { position: state.player.position + amount })
  },
  setQueue(state, queue) {
    state.queue = [...queue]
  },
  setPermission(state, permission) {
    state.permission = Object.assign({}, permission)
  },
  reset(state) {
    state.guild = {}
    state.config = {}
    state.player = {}
    state.queue = []
    state.permission = {}
  },
}

export const getters = {
  id(state) {
    return state.guild.id
  },
  guild(state) {
    return {
      ...state.guild,
    }
  },
  config(state) {
    return {
      ...state.config,
    }
  },
  player(state) {
    return {
      ...state.player,
    }
  },
  queue(state) {
    return [...state.queue]
  },
  permission(state) {
    return {
      ...state.permission,
    }
  },
  isNull(state) {
    return Object.keys(state.guild).length === 0 || Object.keys(state.config).length === 0
  },
  isPlayerNull(state) {
    return Object.keys(state.player).length === 0
  },
}
