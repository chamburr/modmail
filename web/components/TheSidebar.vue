<template>
  <nav id="sidebar-nav" class="text-center py-5">
    <div id="sidebar-container" class="bg-dark py-5 h-100 overflow-scroll-y scrollbar-none">
      <div class="container px-5 pb-2">
        <img id="sidebar-icon" class="rounded" :src="$discord.getIcon(guild)" alt="Icon" />
        <p class="h5 text-wrap font-weight-bold mt-3 mb-2">{{ guild.name }}</p>
      </div>
      <div v-for="element in modules" :key="element.name" class="text-left">
        <template v-if="element.admin !== 'true' || permission.manage_guild">
          <NuxtLink v-if="element.link != null" :to="element.link">
            <div id="sidebar-link" class="font-weight-bold text-white px-4 py-2">
              {{ element.name }}
            </div>
          </NuxtLink>
          <div v-else class="small font-weight-bold text-light text-uppercase px-4 mt-3 mb-2">
            {{ element.name }}
          </div>
        </template>
      </div>
    </div>
  </nav>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'TheSidebar',
  computed: {
    ...mapGetters('guild', ['guild', 'permission']),
    ...mapGetters(['modules']),
  },
}
</script>

<style scoped lang="scss">
#sidebar-nav {
  position: sticky;
  top: 75px;
  height: calc(100vh - 75px);
}

#sidebar-container {
  border-radius: 0.75rem;
}

#sidebar-icon {
  height: 100px;
  width: 100px;
}

#sidebar-link:hover {
  color: $gray-400;
  background-color: $gray-700;
}
</style>
