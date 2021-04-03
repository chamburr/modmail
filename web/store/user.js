export const state = () => ({
  user: {},
  guilds: [],
})

export const mutations = {
  set(state, user) {
    state.user = Object.assign({}, user)
  },
  setGuilds(state, guilds) {
    state.guilds = [...guilds]
  },
  reset(state) {
    state.user = {}
    state.guilds = []
  },
}

export const getters = {
  user(state) {
    return {
      ...state.user,
    }
  },
  guilds(state) {
    return [...state.guilds]
  },
  isNull(state) {
    return Object.keys(state.user).length === 0
  },
  isGuildsNull(state) {
    return state.guilds.length === 0
  },
}
