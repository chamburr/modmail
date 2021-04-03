export default ({ $axios, $moment }, inject) => {
  inject('discord', {
    getName(user) {
      if (!user) return 'Unknown#0000'
      return `${user.username}#${('0000' + user.discriminator).slice(-4)}`
    },
    getAvatar(user) {
      if (user && user.avatar) {
        return `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.${
          user.avatar.startsWith('a_') ? 'gif' : 'png'
        }?size=512`
      }
      return 'https://cdn.discordapp.com/embed/avatars/0.png'
    },
    getIcon(guild) {
      if (guild && guild.icon) {
        return `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.${
          guild.icon.startsWith('a_') ? 'gif' : 'png'
        }?size=512`
      }
      return 'https://cdn.discordapp.com/embed/avatars/0.png'
    },
  })

  inject('track', {
    getIcon(track) {
      if (track && track.uri.split('//')[1].split('/')[0].includes('youtube.com')) {
        const identifier = track.uri.split('?v=')[1]
        return `https://img.youtube.com/vi/${identifier}/mqdefault.jpg`
      }
      return require('~/assets/images/disc.png')
    },
    getDuration(track) {
      if (!track) return '00:00'

      const duration = new Date(track.length)
      const seconds = Math.floor((duration / 1000) % 60)
      const minutes = Math.floor((duration / (1000 * 60)) % 60)
      const hours = Math.floor(duration / (1000 * 60 * 60))

      const result = []
      if (hours > 1) result.push(hours >= 10 ? `${hours}` : `0${hours}`)
      result.push(minutes >= 10 ? `${minutes}` : `0${minutes}`)
      result.push(seconds >= 10 ? `${seconds}` : `0${seconds}`)

      return result.join(':')
    },
  })

  inject('api', {
    async getUsers(elements) {
      if (elements.length === 0) return []

      if (typeof elements[0] !== 'object') {
        elements = [...new Set(elements)]
      } else {
        elements = [...new Set(elements.map(element => element.author))]
      }

      return await $axios.$get('/users', { params: { ids: elements.join(',') } }).then(res => {
        const users = {}
        for (const element of res) {
          users[element.id] = element
        }
        return users
      })
    },
    clone(element) {
      return JSON.parse(JSON.stringify(element))
    },
    isEqual(before, after) {
      return JSON.stringify(before) === JSON.stringify(after)
    },
    isEmpty(element) {
      return Object.keys(element).length === 0
    },
    diff(before, after) {
      const diff = {}
      for (const element of Object.keys(before)) {
        const beforeString = JSON.stringify(before[element])
        const afterString = JSON.stringify(after[element])
        if (beforeString !== afterString) {
          diff[element] = JSON.parse(afterString)
        }
      }
      return diff
    },
  })
}
